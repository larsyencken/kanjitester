# -*- coding: utf-8 -*-
#
#  views.py
#  kanji_test
# 
#  Created by Lars Yencken on 25-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

import csv
import operator

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.db import connection
from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.utils.http import urlencode
from django.conf import settings

from kanji_test.analysis.decorators import staff_only
from kanji_test.drill import models
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
    num_responses = models.MultipleChoiceResponse.objects.count()
    context['num_responses'] = num_responses
    context['responses_per_user'] = num_responses / float(num_users)

    num_tests = models.TestSet.objects.exclude(end_time=None).count()
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
def chart_dashboard(request, name=None):
    context = {}
    context['column_1'], context['column_2'], context['column_3'] = \
            available_charts
    if name is not None:
        context['name'] = name
        context['desc'] = name_to_desc[name]

        chart = _build_graph(name)
        context['chart'] = chart

    return render_to_response("analysis/charts.html", context,
            RequestContext(request))

#----------------------------------------------------------------------------#
# HELPERS
#----------------------------------------------------------------------------#

class Column(object):
    def __init__(self, title, charts_v):
        self.title = title
        self.charts = charts_v

available_charts = (
        Column('User information', [
            ('lang_first',      'First language'),
            ('lang_second',     'Second language'),
            ('lang_combined',   'Combined languages'),
            ('syllabus_volume', 'Syllabus by # users'),
        ]),
        Column('Tests and responses', [
            ('test_mean',       'Mean score by # tests'),
            ('test_volume',     'Users by # tests'),
            ('response_volume', 'Users by # responses'),
            ('test_length',     'Test length by volume'),
        ]),
        Column('Questions and plugins', [
            ('pivot_exposures',     'Mean # exposures per pivot'),
            ('plugin_questions',    'Plugin by # questions'),
            ('plugin_error',        'Mean error by plugin'),
            ('pivot_type',          'Accuracy by word type'),
        ])
    )

name_to_desc = dict(reduce(operator.add, (c.charts for c in \
        available_charts)))

def _build_graph(name):
    parts = name.split('_')
    first_part = parts.pop(0)

    try:
        method = globals()['_build_%s_graph' % first_part]
    except KeyError:
        raise KeyError(name)

    return method(*parts)

def _build_lang_graph(name):
    dist = stats.get_language_data(name)
    return charts.PieChart(dist.items(), max_options=8)

def _build_syllabus_graph(name):
    if name == 'volume':
        return charts.PieChart(stats.get_syllabus_volume())

    raise KeyError(name)

def _build_test_graph(name):
    if name == 'mean':
        score_data = stats.get_mean_score()
        return charts.LineChart(score_data)

    elif name == 'volume':
        user_data = stats.get_users_by_n_tests()
        return charts.LineChart(user_data)

    elif name == 'length':
        return charts.PieChart(stats.get_test_length_volume())

    raise KeyError(name)

def _build_response_graph(name):
    if name == 'volume':
        user_data = stats.get_users_by_n_responses()
        chart = charts.LineChart(user_data)
        return chart

    raise KeyError(name)

def _build_pivot_graph(name):
    if name == 'exposures':
        data = stats.get_exposures_per_pivot()
        return charts.BarChart(data, y_axis=(0, 50, 10))

    if name == 'type':
        data = stats.get_accuracy_by_pivot_type()
        return charts.BarChart(data, y_axis=(0, 1, 0.1))
    
    raise KeyError(name)

def _build_plugin_graph(name):
    if name == 'questions':
        data = []
        for plugin in models.QuestionPlugin.objects.all():
            data.append((
                    plugin.name + \
                    ((plugin.is_adaptive) and ' [adaptive]' or ' [simple]'),
                    plugin.question_set.count(),
                ))
        return charts.PieChart(data)

    elif name == 'error':
        data = stats.get_mean_error_by_plugin()
        data.append(('[random guess]', 1.0/(1 + settings.N_DISTRACTORS)))
        return charts.BarChart(data, y_axis=(0,0.25,0.05))

    raise KeyError(name)

# vim: ts=4 sw=4 sts=4 et tw=78:
