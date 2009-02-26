# -*- coding: utf-8 -*-
#
#  views.py
#  kanji_test
# 
#  Created by Lars Yencken on 25-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db import connection
from django.core import serializers
from django.http import HttpResponse, Http404
from django.utils import simplejson

from kanji_test.analysis.decorators import staff_only
from kanji_test.drill.models import MultipleChoiceResponse, TestSet
from kanji_test.util.probability import FreqDist
from kanji_test.user_profile.models import UserProfile

#----------------------------------------------------------------------------#
# VIEWS
#----------------------------------------------------------------------------#

@staff_only
def home(request):
    context = {}
    
    # Number of users
    num_users = count_active_users()
    context['num_users'] = num_users

    # Number of questions answered
    num_responses = MultipleChoiceResponse.objects.count()
    context['num_responses'] = num_responses
    context['responses_per_user'] = num_responses / float(num_users)

    num_tests = TestSet.objects.exclude(end_time=None).count()
    context['num_tests'] = num_tests

    context['tests_per_user'] = num_tests / float(num_users)
    context['responses_per_test'] = num_responses / float(num_tests)

    test_dist = get_test_stats()
    dist_values = [(k, 100*test_dist.freq(k)) \
            for k in sorted(test_dist.samples())]
    context['test_dist'] = dist_values

    return render_to_response("analysis/home.html", context,
            RequestContext(request))

@staff_only
def data(request):
    if request.method != "GET" or 'type' not in request.GET:
        raise Http404

    g = request.GET
    graph_type = g['type']

    data = []
    options = {}

    if graph_type == 'bar':
        options['bars'] = {'show': True, 'fill': True, 'barWidth': 0.8}
        options['xaxis'] = 2
        y_axis = _fetch_data(g['y_axis'])
        per_user_data = _organise_per_user(y_axis, max_shown=6)
        for i, (label, value) in enumerate(per_user_data):
            data.append({
                'label': label,
                'data': [[i, value]],
            })

    elif graph_type == 'scatter':
        graph_data = {}
        graph_data['points'] = {'show': True}
        y_axis = _fetch_data(g['y_axis'])
        x_axis = _fetch_data(g['x_axis'])
        graphs.append(graph_data)

    return HttpResponse(
            simplejson.dumps({'gdata': data, 'goptions': options}),
            mimetype='application/json',
        )

@staff_only
def charts(request):
    return render_to_response("analysis/charts.html", {},
            RequestContext(request))

#----------------------------------------------------------------------------#
# HELPERS
#----------------------------------------------------------------------------#

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

def get_test_stats():
    """
    Fetches the distribution of test sizes chosen by users, and the completion
    statistics for each reported size.
    """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT n_items, COUNT(*) FROM (
            SELECT testset_id, COUNT(*) as n_items
            FROM drill_testset_questions
            GROUP BY testset_id
        ) as tmp
        GROUP BY n_items
        ORDER BY n_items ASC
    """)
    dist_counts = cursor.fetchall()
    dist = FreqDist()
    for n_items, count in dist_counts:
        dist.inc(n_items, count)
    return dist

def _fetch_data(key):
    if key in ['first_lang', 'second_lang', 'lang_combined']:
        data = _fetch_language_data(key)
    else:
        data = {}

    return data

def _organise_per_user(axis_data, max_shown=None):
    """
    Takes the data for a single_axis and plots it against the number of
    users.
    """
    key_to_n_users = FreqDist()
    for user_id, key in _iter_keys(axis_data):
        key_to_n_users.inc(key)

    result = key_to_n_users.items()
    result.sort(key=lambda x: x[1], reverse=True)

    if max_shown is not None:
        assert max_shown >= 2
        if len(result) > max_shown:
            n_other = 0
            while len(result) > max_shown - 1:
                n_other += result.pop()[1]

            result.append(['Other', n_other])

    return result

def _iter_keys(axis_data):
    for user_id, maybe_key in axis_data.iteritems():
        if type(maybe_key) == list:
            for key in maybe_key:
                yield user_id, key
        else:
            yield user_id, maybe_key
    
def _fetch_language_data(key):
    "Fetches information about user first and second languages."

    if key == 'first_lang':
        profiles = list(UserProfile.objects.values('user_id', 'first_language'))
    elif key == 'second_lang':
        profiles = UserProfile.objects.values('user_id', 'second_languages')
    else:
        assert key == 'lang_combined'
        profiles = UserProfile.objects.values('user_id', 'first_language',
            'second_languages')
    
    data = {}
    for profile in profiles:
        langs = set()
        if 'first_language' in profile:
            langs.add(profile['first_language'].title())
        if 'second_languages' in profile:
            langs.update(l.strip().title() for l in \
                    profile['second_languages'].split(','))
        if '' in langs:
            langs.remove('') # Remove the case where no second language exists 
        data[profile['user_id']] = list(sorted(langs))

    return data

# vim: ts=4 sw=4 sts=4 et tw=78:
