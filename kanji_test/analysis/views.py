# -*- coding: utf-8 -*-
#
#  views.py
#  kanji_test
# 
#  Created by Lars Yencken on 25-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

import csv

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db import connection
from django.core import serializers
from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.utils.http import urlencode
from cjktools.stats import mean
from cjktools.sequences import unzip

from kanji_test.analysis.decorators import staff_only
from kanji_test.drill.models import MultipleChoiceResponse, TestSet
from kanji_test.util.probability import FreqDist
from kanji_test.util import charts
from kanji_test.user_profile.models import UserProfile, Syllabus
from kanji_test import settings

#----------------------------------------------------------------------------#
# VIEWS
#----------------------------------------------------------------------------#

@staff_only
def basic(request):
    "Calculates and displays some basic statistics."
    context = {}
    
    # Number of users
    num_users = _count_active_users()
    context['num_users'] = num_users

    # Number of questions answered
    num_responses = MultipleChoiceResponse.objects.count()
    context['num_responses'] = num_responses
    context['responses_per_user'] = num_responses / float(num_users)

    num_tests = TestSet.objects.exclude(end_time=None).count()
    context['num_tests'] = num_tests

    context['tests_per_user'] = num_tests / float(num_users)
    context['responses_per_test'] = num_responses / float(num_tests)

    test_stats = _get_test_stats()
    pretty_results = [(k, 100*t, 100*c) for (k, t, c) in test_stats]
    context['test_dist'] = pretty_results

    return render_to_response("analysis/basic.html", context,
            RequestContext(request))

@staff_only
def data(request, name=None, format=None):
    "Fetches data set as either a chart or as a CSV file."
    chart = _build_graph(name)

    mimetype = 'text/html'
    if format == 'json':
        if not settings.DEBUG:
            mimetype = 'application/json'
        return HttpResponse(simplejson.dumps(chart.get_url()),
                mimetype=mimetype)

    elif format == 'csv':
        if not settings.DEBUG:
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = \
                    'attachment; filename=%s.csv' % name
        else:
            response = HttpResponse(mimetype='text/html')
        writer = csv.writer(response)
        for row in chart.data:
            writer.writerow(row)
        return response

    else:
        raise Http404

@staff_only
def chart_dashboard(request):
    return render_to_response("analysis/charts.html", {},
            RequestContext(request))

#----------------------------------------------------------------------------#
# HELPERS
#----------------------------------------------------------------------------#

def _count_active_users():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM (
                SELECT user_id FROM drill_testset
                WHERE end_time IS NOT NULL
                GROUP BY user_id
            ) as tmp
    """)
    return cursor.fetchone()[0]

def _get_test_stats():
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

def _build_graph(name):
    parts = name.split('_')
    first_part = parts.pop(0)

    if first_part == 'lang':
        return _build_language_graph(*parts)
    
    elif first_part == 'test':
        return _build_test_graph(*parts)

    elif first_part == 'response':
        return _build_response_graph(*parts)

    elif first_part == 'syllabus':
        return _build_syllabus_graph(*parts)

    else:
        raise KeyError(name)

def _build_language_graph(name):
    dist = _fetch_language_data(name)
    return charts.PieChart(dist.items(), max_options=8)

def _build_syllabus_graph(name):
    if name == 'volume':
        return charts.PieChart(_fetch_syllabus_volume())

    raise KeyError('syllabus_' + name)

def _fetch_language_data(name):
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
            for lang in profile['second_languages'].split(','):
                lang = lang.strip().title()
                if lang == 'Japanese':
                    continue
                elif lang == '' and name != 'lang_combined':
                    lang = 'None'
                dist.inc(lang)

    return dist

def _build_test_graph(name):
    if name == 'mean':
        score_data = _get_mean_score()
        return charts.LineChart(score_data)

    elif name == 'volume':
        user_data = _get_users_by_n_tests()
        return charts.LineChart(user_data)

    elif name == 'length':
        return charts.PieChart(_get_test_length_volume())

    else:
        raise KeyError('test_' + name)

def _get_mean_score():
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
    map = {}
    last_user_id = None
    i = None
    for user_id, score in cursor.fetchall():
        if user_id != last_user_id:
            i = 1
            last_user_id = user_id

        score = float(score)

        if i in map:
            map[i].append(score)
        else:
            map[i] = [score]

        i += 1

    results = []
    for i, scores in sorted(map.iteritems()):
        results.append((i, mean(scores)))

    return results

def _get_users_by_n_tests():
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

def _build_response_graph(name):
    if name == 'volume':
        user_data = _get_users_by_n_responses()
        chart = charts.LineChart(user_data)
        return chart
    else:
        raise KeyError('response_' + name)

def _get_users_by_n_responses():
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

def _get_test_length_volume():
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

def _fetch_syllabus_volume():
    data = []
    for syllabus in Syllabus.objects.all():
        data.append((syllabus.tag, syllabus.userprofile_set.count()))
    return data

# vim: ts=4 sw=4 sts=4 et tw=78:
