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
from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.utils.http import urlencode

from kanji_test.analysis.decorators import staff_only
from kanji_test.drill.models import MultipleChoiceResponse, TestSet
from kanji_test.util import charts
from kanji_test import settings

import stats

#----------------------------------------------------------------------------#
# VIEWS
#----------------------------------------------------------------------------#

@staff_only
def basic(request):
    "Calculates and displays some basic statistics."
    context = {}
    
    # Number of users
    num_users = stats.count_active_users()
    context['num_users'] = num_users

    # Number of questions answered
    num_responses = MultipleChoiceResponse.objects.count()
    context['num_responses'] = num_responses
    context['responses_per_user'] = num_responses / float(num_users)

    num_tests = TestSet.objects.exclude(end_time=None).count()
    context['num_tests'] = num_tests

    context['tests_per_user'] = num_tests / float(num_users)
    context['responses_per_test'] = num_responses / float(num_tests)

    test_stats = stats.get_test_stats()
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
    dist = stats.get_language_data(name)
    return charts.PieChart(dist.items(), max_options=8)

def _build_syllabus_graph(name):
    if name == 'volume':
        return charts.PieChart(stats.get_syllabus_volume())

    raise KeyError('syllabus_' + name)

def _build_test_graph(name):
    if name == 'mean':
        score_data = stats.get_mean_score()
        return charts.LineChart(score_data)

    elif name == 'volume':
        user_data = stats.get_users_by_n_tests()
        return charts.LineChart(user_data)

    elif name == 'length':
        return charts.PieChart(stats.get_test_length_volume())

    else:
        raise KeyError('test_' + name)

def _build_response_graph(name):
    if name == 'volume':
        user_data = stats.get_users_by_n_responses()
        chart = charts.LineChart(user_data)
        return chart
    else:
        raise KeyError('response_' + name)

# vim: ts=4 sw=4 sts=4 et tw=78:
