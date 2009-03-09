# -*- coding: utf-8 -*-
#
#  stats.py
#  kanji_test
# 
#  Created by Lars Yencken on 02-03-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

"""
Statistical analysis of user data. 
"""

from django.db import connection
from django.contrib.auth.models import User
from cjktools.stats import mean
from cjktools import scripts
from cjktools.sequences import unzip

from kanji_test.user_profile.models import UserProfile, Syllabus
from kanji_test.user_model.models import PartialLexeme, PartialKanji
from kanji_test.drill import models as drill_models
from kanji_test.util.probability import FreqDist

def get_mean_score():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT r.user_id, AVG(o.is_correct)
        FROM drill_response AS r
        INNER JOIN drill_multiplechoiceresponse AS mcr
        ON r.id = mcr.response_ptr_id
        INNER JOIN drill_multiplechoiceoption AS o
        ON o.id = mcr.option_id
        GROUP BY r.user_id, r.timestamp
        ORDER BY r.user_id, r.timestamp
    """)
    scores_by_n_tests = {}
    last_user_id = None
    i = None
    for user_id, score in cursor.fetchall():
        if user_id != last_user_id:
            i = 1
            last_user_id = user_id

        score = float(score)

        if i in scores_by_n_tests:
            scores_by_n_tests[i].append(score)
        else:
            scores_by_n_tests[i] = [score]

        i += 1

    results = []
    for i, scores in sorted(scores_by_n_tests.iteritems()):
        results.append((i, mean(scores)))

    return results

def get_users_by_n_tests():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT n_tests, COUNT(*) AS n_users
        FROM (
            SELECT user_id, COUNT(*) AS n_tests
            FROM drill_testset
            GROUP BY user_id
        ) AS tests_per_user
        GROUP BY n_tests
        ORDER BY n_tests ASC
    """)
    data = list(cursor.fetchall())

    # Make cumulative
    for i in xrange(len(data) - 1, 0, -1):
        label, value = data[i-1]
        data[i-1] = (label, value + data[i][1])

    return data

def get_users_by_n_responses():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT n_responses, COUNT(*) AS n_users
        FROM (
            SELECT user_id, COUNT(*) AS n_responses
            FROM drill_response
            GROUP BY user_id
        ) AS responses_per_user
        GROUP BY n_responses
        ORDER BY n_responses ASC
    """)
    data = list(cursor.fetchall())

    # Make cumulative
    for i in xrange(len(data) - 1, 0, -1):
        label, value = data[i-1]
        data[i-1] = (label, value + data[i][1])

    return data

def get_test_length_volume():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT n_questions, COUNT(*) AS n_tests
        FROM (
            SELECT testset_id, COUNT(*) AS n_questions
            FROM drill_testset_questions
            GROUP BY testset_id
        ) AS questions_per_test
        GROUP BY n_questions
    """)
    return cursor.fetchall()

def get_syllabus_volume():
    data = []
    for syllabus in Syllabus.objects.all():
        data.append((syllabus.tag, syllabus.userprofile_set.count()))
    return data

def get_language_data(name):
    "Fetches information about user first and second languages."

    fields_needed = ['user_id']
    if name in ['first', 'combined']:
        fields_needed.append('first_language')
    elif name in ['second', 'combined']:
        fields_needed.append('second_languages')
    else:
        assert name == 'combined'

    profiles = UserProfile.objects.values(*fields_needed)
    
    dist = FreqDist()
    for profile in profiles:
        if 'first_language' in profile:
            lang = profile['first_language'].title()
            dist.inc(lang)
        if 'second_languages' in profile:
            if profile['second_languages']:
                for lang in profile['second_languages'].split(','):
                    lang = lang.strip().title()
                    if lang == 'Japanese':
                        continue
                    dist.inc(lang)
            elif name != 'lang_combined':
                dist.inc('None')

    return dist

def get_test_stats():
    """
    Fetches the distribution of test sizes chosen by users, and the completion
    statistics for each reported size.
    """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT n_items, COUNT(*), AVG(is_finished) FROM (
            SELECT 
                ts.id AS test_set_id,
                COUNT(*) AS n_items,
                (ts.end_time IS NOT NULL) AS is_finished
            FROM drill_testset_questions AS tsq
            INNER JOIN drill_testset AS ts
            ON tsq.testset_id = ts.id
            GROUP BY ts.id
        ) as tmp
        GROUP BY n_items
        ORDER BY n_items ASC
    """)
    data = cursor.fetchall()
    dist = FreqDist()
    completion_rates = {}
    for n_items, n_tests, completion_rate in data:
        dist.inc(n_items, n_tests)
        completion_rates[n_items] = completion_rate
    results = []
    for sample in sorted(dist.samples()):
        results.append((sample, dist.freq(sample), completion_rates[sample]))
    return results

def count_active_users():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM (
                SELECT user_id FROM drill_testset
                WHERE end_time IS NOT NULL
                GROUP BY user_id
            ) as tmp
    """)
    return cursor.fetchone()[0]

def get_top_n_pivots(n, syllabus_id, pivot_type):
    """
    Fetches the n pivots of the given type and from the given syllabus which
    have been used in the most questions.
    """
    cursor = connection.cursor()
    if pivot_type == 'k':
        pivot_table = 'user_model_partialkanji'
    elif pivot_type == 'w':
        pivot_table = 'user_model_partiallexeme'
    else:
        raise ValueError('unexpected pivot type: %s' % pivot_type)
        
    cursor.execute("""
        SELECT p.id, COUNT(*) as n_exposures
        FROM drill_question AS q
        INNER JOIN %(pivot_table)s AS p
        ON p.id = q.pivot_id
        WHERE q.pivot_type = "%(pivot_type)s" 
            AND p.syllabus_id = %(syllabus_id)d
        GROUP BY pivot_id
        ORDER BY n_exposures DESC
        LIMIT %(n)d
    """ % {
            'pivot_type':   pivot_type,
            'pivot_table':  pivot_table,
            'syllabus_id':  syllabus_id, 
            'n':            n,
    })
    
    base_results = cursor.fetchall()
    pivot_ids = unzip(base_results)[0]
    if pivot_type == 'k':
        pivot_model = PartialKanji
    else:
        pivot_model = PartialLexeme 
    pivot_map = pivot_model.objects.in_bulk(pivot_ids)

    return [(pivot_map[pid], c) for (pid, c) in base_results]

def get_mean_exposures_per_pivot():
    "Returns the number of exposures each pivot received."
    cursor = connection.cursor()
    cursor.execute("""
        SELECT pivot, pivot_type, COUNT(*) as n_exposures
        FROM drill_question
        GROUP BY CONCAT(pivot, "|", pivot_type)
    """)
    data = cursor.fetchall()
    word_c = []
    kanji_c = []
    combined_c = []
    kanji_inc_dist = FreqDist()
    for pivot, pivot_type, count in data:
        combined_c.append(count)

        if pivot_type == 'k':
            kanji_c.append(count)
            kanji_inc_dist.inc(pivot, count)

        elif pivot_type == 'w':
            word_c.append(count)
            for kanji in scripts.uniqueKanji(pivot):
                kanji_inc_dist.inc(kanji, count)

        else:
            raise ValueError('unknown pivot type: %s' % pivot_type)

    return [
            ('Words', mean(word_c)),
            ('Kanji', mean(kanji_c)),
            ('Combined', mean(combined_c)),
            ('Kanji combined', mean(kanji_inc_dist.values())),
        ]

def get_mean_error_by_plugin():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT plugin.name, 1 - plugin_score.score
        FROM (
            SELECT
                question.question_plugin_id,
                AVG(chosen_option.is_correct) as score
            FROM (
                SELECT mco.question_id, mco.is_correct
                FROM drill_multiplechoiceresponse AS mcr
                INNER JOIN drill_multiplechoiceoption AS mco
                ON mcr.option_id = mco.id
            ) as chosen_option
            INNER JOIN drill_question AS question
            ON chosen_option.question_id = question.id
            GROUP BY question.question_plugin_id
        ) AS plugin_score
        INNER JOIN drill_questionplugin AS plugin
        ON plugin_score.question_plugin_id = plugin.id
        ORDER BY plugin.name ASC
    """)
    return [(l, float(v)) for (l, v) in cursor.fetchall()] 

def get_accuracy_by_pivot_type():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT
            question.pivot,
            SUM(chosen_option.is_correct) as n_correct,
            COUNT(*) as n_responses
        FROM (
            SELECT mco.question_id, mco.is_correct
            FROM drill_multiplechoiceresponse AS mcr
            INNER JOIN drill_multiplechoiceoption AS mco
            ON mcr.option_id = mco.id
        ) as chosen_option
        INNER JOIN drill_question AS question
        ON chosen_option.question_id = question.id
        WHERE question.pivot_type = "w"
        GROUP BY question.pivot
    """)
    raw_data = cursor.fetchall()
    counts = {'Hiragana': FreqDist(), 'Katakana': FreqDist(), 'Kanji':
        FreqDist()}
    complex_scripts = set([scripts.Script.Kanji, scripts.Script.Unknown])
    kanji_script = scripts.Script.Kanji
    only_hiragana = set([scripts.Script.Hiragana])
    only_katakana = set([scripts.Script.Katakana])
    for word, n_correct, n_responses in raw_data:
        scripts_found = scripts.scriptTypes(word)
        if scripts_found.intersection(complex_scripts):
            dist = counts['Kanji']
        elif scripts_found.intersection(only_katakana):
            dist = counts['Katakana']
        else:
            dist = counts['Hiragana']

        dist.inc(True, int(n_correct))
        dist.inc(False, int(n_responses - n_correct))

    keys = ('Hiragana', 'Katakana', 'Kanji')

    data = [(key, counts[key].freq(True)) for key in keys]

    average = FreqDist()
    for key in keys:
        average.inc(True, counts[key][True])
        average.inc(False, counts[key][False])

    data.append(('Average', average.freq(True)))

    return data

def get_top_n_raters(n):
    "Fetches the top n users by number of responses."
    if n < 1:
        raise ValueError('need at least one user')
    cursor = connection.cursor()
    cursor.execute("""
        SELECT r.user_id, COUNT(*) as n_responses, AVG(o.is_correct) as score
        FROM drill_response AS r
        INNER JOIN drill_multiplechoiceresponse AS mcr
        ON r.id = mcr.response_ptr_id
        INNER JOIN drill_multiplechoiceoption AS o
        ON o.id = mcr.option_id
        GROUP BY r.user_id
        ORDER BY n_responses DESC
        LIMIT %s
    """, (n,))
    query_results = cursor.fetchall()
    user_ids = []
    for user_id, n_responses, score in query_results:
        user_ids.append(user_id)
    user_map = User.objects.in_bulk(user_ids)

    return [(user_map[user_id], nr, s) for (user_id, nr, s) in \
            query_results]

def get_rater_stats(rater):
    responses = drill_models.MultipleChoiceOption.objects.filter(
            multiplechoiceresponse__user=rater).values('is_correct')
    mean_accuracy = mean((r['is_correct'] and 1 or 0) for r in responses)
    
    return {
        'n_responses': drill_models.Response.objects.filter(
                user=rater).count(),
        'n_tests': drill_models.TestSet.objects.filter(
                user=rater).count(),
        'mean_accuracy': mean_accuracy,
    }

def get_pivot_response_stats(pivot_id, pivot_type):
    """
    Given a particular pivot, generate a distribution of observed erroneous 
    responses for each type of plugin.
    """
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT plugin_option.plugin_id, plugin_option.value
        FROM drill_multiplechoiceresponse AS mcr
        INNER JOIN (
            SELECT pivot_qn.plugin_id, mco.id AS option_id, mco.value
            FROM (
                SELECT id, question_plugin_id AS plugin_id
                FROM drill_question
                WHERE pivot_type = "%(pivot_type)s"
                    AND pivot_id = %(pivot_id)d
            ) AS pivot_qn
            INNER JOIN drill_multiplechoiceoption AS mco
            ON mco.question_id = pivot_qn.id
        ) AS plugin_option
        ON plugin_option.option_id = mcr.option_id
    """ % {'pivot_type': pivot_type, 'pivot_id': pivot_id})
    rows = cursor.fetchall()
    dist_map = {}
    plugin_ids_used = set(plugin_id for (plugin_id, error_value) in rows)
    for plugin_id in plugin_ids_used:
        dist_map[plugin_id] = FreqDist()
    
    for plugin_id, error_value in rows:
        dist_map[plugin_id].inc(error_value)
    
    plugin_map = drill_models.QuestionPlugin.objects.in_bulk(dist_map.keys())
    
    results = [(plugin_map[plugin_id].name, dist) \
            for (plugin_id, dist) in dist_map.iteritems()]
    combined_dist = FreqDist()
    for name, dist in results:
        combined_dist.inc(name, dist.N())
    results[0:0] = [('By plugin type', combined_dist)]
    
    return results

# vim: ts=4 sw=4 sts=4 et tw=78: