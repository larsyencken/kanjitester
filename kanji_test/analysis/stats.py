# -*- coding: utf-8 -*-
#
#  stats.py
#  kanji_test
# 
#  Created by Lars Yencken on 02-03-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

"""
This model provides a variety of analyses of usage data, many of which involve
low-level SQL queries in order to calculate them efficiently.
"""

from itertools import groupby
from datetime import timedelta

import numpy
from django.db import connection
from cjktools.stats import mean
from cjktools import scripts
from cjktools.sequences import unzip

from kanji_test.user_profile.models import UserProfile, Syllabus
from kanji_test.user_model.models import PartialLexeme, PartialKanji
from kanji_test.drill import models as drill_models
from kanji_test.util.probability import FreqDist

def get_mean_score():
    """
    Fetches the mean score on the nth test, for increasing n.
    """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT ur.user_id, AVG(ur.is_correct)
        FROM drill_testset_responses AS tsr
        INNER JOIN (
            SELECT r.user_id, r.id AS response_id, o.is_correct
            FROM drill_response AS r
            INNER JOIN drill_multiplechoiceresponse AS mcr
            ON r.id = mcr.response_ptr_id
            INNER JOIN drill_multiplechoiceoption AS o
            ON o.id = mcr.option_id
        ) AS ur
        ON tsr.multiplechoiceresponse_id = ur.response_id
        GROUP BY tsr.testset_id
        ORDER BY ur.user_id
    """)
    scores_by_n_tests = {}
    
    for user_id, rows in groupby(cursor.fetchall(), lambda r: r[0]):
        for i, (_user_id, score) in enumerate(rows):
            score_list = scores_by_n_tests.get(i + 1)
            score = float(score)
            if score_list:
                score_list.append(score)
            else:
                scores_by_n_tests[i + 1] = [score]

    results = []
    for i, scores in sorted(scores_by_n_tests.iteritems()):
        if len(scores) < 3:
            continue
        results.append((i, mean(scores)))

    return results

def get_time_between_tests():
    test_sets = drill_models.TestSet.objects.exclude(end_time=None).order_by(
            'user__id')
    
    data = []
    in_days = timedelta(days=1)
    for user_id, user_tests in groupby(test_sets, lambda t: t.user_id):
        last_test = user_tests.next().start_time
        
        for test_set in user_tests:
            time_diff = _scale_time_delta(test_set.start_time - last_test,
                    in_days)
            data.append(time_diff)
            last_test = test_set.start_time
    
    data.sort()
    return data

def get_time_between_tests_histogram():
    data = get_time_between_tests()
    n_points = float(len(data))

    one_min = 1.0/(24*60)
    rows = []
    for bin_min in _iter_log_values(one_min):
        freq = len([p for p in data if p > bin_min]) / n_points
        rows.append((
                bin_min,
                freq
        ))
        if freq < 0.01:
            break
                    
    return rows
    
def _iter_log_values(value):
    yield 0
    yield value
    while True:
        value *= 2
        yield value

def get_score_over_norm_time():
    "Fetches the score for each user normalized over the time axis."
    scores_by_test = dict((t, float(s)) for (t, s) in _get_test_scores())
    test_sets = drill_models.TestSet.objects.exclude(end_time=None)
    
    data = []
    key_f = lambda t: t.user_id
    for user_id, user_tests in groupby(sorted(test_sets, key=key_f), key_f):
        user_tests = sorted(user_tests, key=lambda t: t.start_time)
        # Ignore users with only one test
        if len(user_tests) < 2:
            continue
        
        first_test = user_tests[0].start_time
        last_test = user_tests[-1].start_time
        max_delta = last_test - first_test
        
        # Ignore users who didn't use the system for 24 hours
        if max_delta < timedelta(days=1):
            continue
        
        for test_set in user_tests:
            test_time = _scale_time_delta(test_set.start_time - first_test,
                    max_delta)
            data.append((test_time, scores_by_test[test_set.id]))
    
    
    data.sort()
    return data

def get_score_over_time():
    "Fetches the score for each user over time (measured in days)."
    scores_by_test = dict((t, float(s)) for (t, s) in _get_test_scores())
    
    user_key_f = lambda t: t.user_id
    test_sets = drill_models.TestSet.objects.exclude(end_time=None)
    test_sets = sorted(test_sets, key=user_key_f)
    
    granularity = '%.f' # the granularity of data points

    base_data = []
    one_day = timedelta(days=1)
    for user_id, user_tests in groupby(test_sets, user_key_f):
        user_tests = sorted(user_tests, key=lambda t: t.start_time)
        # Ignore users with only one test
        if len(user_tests) < 2:
            continue
            
        first_test = user_tests[0].start_time
        last_test = user_tests[-1].start_time
        max_delta = last_test - first_test
        
        # Ignore users who didn't use the system for 24 hours
        if max_delta < one_day:
            continue
    
        # Accumulate user responses, averaging over our interval
        time_f = lambda t: granularity % \
                _scale_time_delta(t.start_time - first_test, one_day)
        
        for n_days, interval_tests in groupby(user_tests, time_f):
            n_days = float(n_days)
            n_responses = 0
            weighted_score = 0.0
            for interval_test in interval_tests:
                test_len = len(interval_test)
                n_responses += test_len
                weighted_score += test_len * scores_by_test[interval_test.id]
                
            base_data.append((n_days, weighted_score / n_responses))
    
    # Group by up to two decimal places
    days = []
    low = []
    mean_data = []
    high = []
    key_f = lambda row: float('%.f' % row[0])
    base_data.sort(key=key_f)
    results = []
    for n_days, points in groupby(base_data, key_f):
        n_days = float(n_days)
        point_data = numpy.array([v for (t, v) in points])
        
        if len(point_data) < 2:
            continue

        days.append(n_days)
        
        avg = point_data.mean()
        mean_data.append(avg)

        stddev = point_data.std()
        low.append(avg - 2*stddev)
        high.append(min(avg + 2*stddev, 1.0))
        
        results.append((
                n_days,                     # x axis
                avg,                        # y axis
                max(avg - 2 * stddev, 0.0), # error bar
                min(avg + 2 * stddev, 1.0), # error bar
            ))
        
    return results

def get_users_by_n_tests():
    """
    Fetch the number of users who have taken at least n tests, for varying n.
    Only tests with responses are counted.
    """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT n_tests, COUNT(*) AS n_users
        FROM (
            SELECT t.user_id, COUNT(*) AS n_tests
            FROM (
                SELECT ts.user_id, COUNT(*) AS n_responses
                FROM drill_testset AS ts
                INNER JOIN drill_testset_responses AS tsr
                ON ts.id = tsr.testset_id
                GROUP BY ts.id
            ) AS t
            WHERE t.n_responses > 0
            GROUP BY t.user_id
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
    """
    Fetch the number of users who have at least n responses, for varying n.
    """
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
    """
    Fetch the number of tests taken of each available test length.
    """
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
    "Fetches the number of users per syllabus."
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
    "Fetch the number of users who have finished at least one test."
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM (
                SELECT user_id FROM drill_testset
                WHERE end_time IS NOT NULL
                GROUP BY user_id
            ) as tmp
    """)
    return cursor.fetchone()[0]

def get_pivots_by_questions(n, syllabus_id, pivot_type):
    """
    Fetches the n pivots of the given type and from the given syllabus which
    have been used in the most questions.
    """
    syllabus_query = _get_syllabus_query(syllabus_id, pivot_type)
    
    cursor = connection.cursor()
    cursor.execute("""
        SELECT pivot_id, COUNT(*) AS n_exposures
        FROM drill_question
        WHERE pivot_type = "%(pivot_type)s"
            AND pivot_id IN (%(syllabus_query)s)
        GROUP BY pivot_id
        ORDER BY n_exposures DESC
        LIMIT %(n)d
    """ % {
            'syllabus_query':   syllabus_query,
            'pivot_type':       pivot_type,
            'n':                n,
    })
    
    base_results = cursor.fetchall()
    pivot_ids = unzip(base_results)[0]
    if pivot_type == 'k':
        pivot_model = PartialKanji
    else:
        pivot_model = PartialLexeme 
    pivot_map = pivot_model.objects.in_bulk(pivot_ids)

    return [(pivot_map[pid], c, _get_n_errors(pid)) for \
            (pid, c) in base_results]

def get_pivots_by_errors(n, syllabus_id, pivot_type):
    "Get the top n pivots by the number of errors made on them."
    syllabus_query = _get_syllabus_query(syllabus_id, pivot_type)
    cursor = connection.cursor()        
    cursor.execute("""
        SELECT q.pivot_id, COUNT(*) AS n_errors
        FROM (
            SELECT mco.question_id
            FROM drill_multiplechoiceresponse AS mcr
            INNER JOIN drill_multiplechoiceoption AS mco
            ON mcr.option_id = mco.id
            WHERE NOT mco.is_correct
        ) AS qr
        INNER JOIN drill_question AS q
        ON qr.question_id = q.id
        WHERE pivot_type = "%(pivot_type)s"
            AND pivot_id IN (%(syllabus_query)s)
        GROUP BY pivot_id
        ORDER BY n_errors DESC
        LIMIT %(n)d
    """ % {
        'syllabus_query':   syllabus_query,
        'pivot_type':       pivot_type,
        'n':                n,
    })
    base_results = cursor.fetchall()
    pivot_ids = unzip(base_results)[0]
    if pivot_type == 'k':
        pivot_model = PartialKanji
    else:
        pivot_model = PartialLexeme 
    pivot_map = pivot_model.objects.in_bulk(pivot_ids)

    return [(pivot_map[pivot_id], _get_n_responses(pivot_id), n_errors) for \
            (pivot_id, n_errors) in base_results]

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
    for pivot, pivot_type, n_exposures in data:
        combined_c.append(n_exposures)

        if pivot_type == 'k':
            kanji_c.append(n_exposures)
            kanji_inc_dist.inc(pivot, n_exposures)

        elif pivot_type == 'w':
            word_c.append(n_exposures)
            for kanji in scripts.uniqueKanji(pivot):
                kanji_inc_dist.inc(kanji, n_exposures)

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

def get_global_rater_stats():
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT id, username
        FROM auth_user
    """)
    id_to_username = dict(cursor.fetchall())
    
    cursor.execute("""
        SELECT q_time.user_id, q.pivot, q.pivot_type, q_time.is_correct
        FROM (
            SELECT mco.question_id, mco.is_correct, ot.user_id, ot.timestamp
            FROM (
                SELECT mcr.option_id, dr.user_id, dr.timestamp
                FROM drill_response AS dr
                INNER JOIN drill_multiplechoiceresponse AS mcr
                ON mcr.response_ptr_id = dr.id
            ) AS ot
            INNER JOIN drill_multiplechoiceoption AS mco
            ON mco.id = ot.option_id
        ) AS q_time
        INNER JOIN drill_question AS q
        ON q.id = q_time.question_id
        ORDER BY user_id ASC, q_time.timestamp ASC
    """)
    results = []
    for user_id, rows in groupby(cursor.fetchall(), lambda r: r[0]):
        rows = [(p, pt, c) for (_u, p, pt, c) in rows] # discard user_id
        
        user_data = {
            'user_id':      user_id,
            'username':     id_to_username[user_id]
        }
        user_data['n_responses'] = len(rows)
        user_data['n_tests'] = drill_models.TestSet.objects.filter(
                user__id=user_id).exclude(end_time=None).count()
        user_data['mean_accuracy'] = mean(r[2] for r in rows)
        user_data['n_errors'] = _seq_len(r for r in rows if r[2])

        pre_ratio, post_ratio = _calculate_pre_post_ratios(rows)
        user_data['pre_ratio'] = pre_ratio
        user_data['post_ratio'] = post_ratio
        user_data['pre_post_diff'] = post_ratio - pre_ratio
        results.append(user_data)
    return results

#----------------------------------------------------------------------------#

def _seq_len(seq):
    i = 0
    for item in seq:
        i += 1
    return i

def _get_n_errors(pivot_id):
    return drill_models.Response.objects.filter(
            question__pivot_id=pivot_id).filter(
                multiplechoiceresponse__option__is_correct=False
            ).count()

def _get_n_responses(pivot_id):
    return drill_models.Response.objects.filter(question__pivot_id=pivot_id
            ).count()

def _get_syllabus_query(syllabus_id, pivot_type):
    """
    Returns a query for a table containing the pivot id for each pivot of the
    given type in the syllabus.
    """
    if pivot_type == 'k':
        pivot_table = 'user_model_partialkanji'
    elif pivot_type == 'w':
        pivot_table = 'user_model_partiallexeme'
    else:
        raise ValueError('unexpected pivot type: %s' % pivot_type)
        
    query = """
    SELECT id
    FROM %(pivot_table)s
    WHERE syllabus_id = %(syllabus_id)d
    """ % {
            'pivot_table':  pivot_table,
            'syllabus_id':  syllabus_id,
        }
    return query

def _calculate_pre_post_ratios(response_data):
    """
    Returns the number of data which are correctly responded to on their first
    presentation.
    """
    first_responses = {}
    last_responses = {}
    for pivot_id, pivot_type, is_correct in response_data:
        if pivot_id not in first_responses:
            first_responses[pivot_id] = is_correct
            
        last_responses[pivot_id] = is_correct
    
    return (
            mean(first_responses.itervalues()),
            mean(last_responses.itervalues()),
        )

def _get_test_scores():
    """
    Returns a list of (test_id, score) for all completed tests.
    """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT testset_id, score
        FROM (
            SELECT test_option.testset_id, AVG(mco.is_correct) AS score, 
                    COUNT(*) as n_responses
            FROM (
                SELECT tsr.testset_id, mcr.option_id
                FROM drill_testset_responses AS tsr
                INNER JOIN drill_multiplechoiceresponse AS mcr
                ON tsr.multiplechoiceresponse_id = mcr.response_ptr_id
            ) AS test_option
            INNER JOIN drill_multiplechoiceoption AS mco
            ON test_option.option_id = mco.id
            GROUP BY test_option.testset_id
        ) AS results
        WHERE n_responses > 0
    """)
    return cursor.fetchall()

_zero_delta = timedelta()
def _scale_time_delta(value, max_value):
    """
    Scales a timedelta object to between 0 and 1, according to max_value.

    >>> one_day = timedelta(days=1)
    >>> ten_days = timedelta(days=10)
    >>> twelve_days = timedelta(days=12)
    >>> abs(_scale_time_delta(_zero_delta, ten_days) - 0) < 1e-8
    True
    >>> abs(_scale_time_delta(one_day, ten_days) - 0.1) < 1e-8
    True
    >>> abs(_scale_time_delta(ten_days, ten_days) - 1) < 1e-8
    True
    >>> abs(_scale_time_delta(twelve_days, ten_days) - 1.2) < 1e-8
    True
    """
    return _time_delta_seconds(value) / float(_time_delta_seconds(max_value))

def _time_delta_seconds(delta):
    """
    Reduces a timedelta object to its value in seconds.

    >>> _time_delta_seconds(timedelta())
    0

    >>> _time_delta_seconds(timedelta(days=2, hours=1, minutes=4, seconds=23))
    176663
    """
    return delta.seconds + delta.days*24*60*60

# vim: ts=4 sw=4 sts=4 et tw=78: