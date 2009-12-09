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
import numpy
import itertools

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.conf import settings
from simplestats import basic_stats, mean

from kanji_test.analysis.decorators import staff_only
from kanji_test.drill import models
from kanji_test.util import charts
from kanji_test.tutor import study_list
from kanji_test.user_model import models as usermodel_models

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
    
    (
        context['mean_tbt'],
        context['std_tbt'],
    ) = basic_stats(stats.get_time_between_tests())
    
    context['log_start_time'] = models.TestSet.objects.order_by('start_time'
            )[0].start_time
    context['log_end_time'] = models.TestSet.objects.order_by('-start_time',
            )[0].start_time

    context['tests_per_user'] = num_tests / float(num_users)
    context['responses_per_test'] = num_responses / float(num_tests)
    
    all_responses = models.MultipleChoiceResponse.objects
    context['mean_score'] = (all_responses.filter(option__is_correct=True
            ).count() / float(all_responses.count()))

    test_stats = stats.get_test_size_stats()
    pretty_results = [(k, 100*t, 100*c) for (k, t, c) in test_stats]
    context['test_dist'] = pretty_results

    context['mean_time_used'] = stats.get_mean_time_used()

    return render_to_response("analysis/basic.html", context,
            RequestContext(request))

@staff_only
def data(request, name=None, format=None):
    "Fetches data set as either a chart or as a CSV file."
    chart = _build_graph(name)
    if name.count('_') > 2:
        raise Http404

    if format == 'json':
        if settings.DEBUG:
            mimetype = 'text/html'
        else:
            mimetype = 'application/json'
        return HttpResponse(simplejson.dumps(chart.get_url()),
                mimetype=mimetype)

    elif format == 'csv':
        return _chart_csv_response(chart, name)
        
    else:
        raise Http404
    
@staff_only
def chart_dashboard(request, name=None):
    context = {}
    context['column_1'], context['column_2'], context['column_3'] = \
            available_charts
    
    if name is not None:
        if name.count('_') > 2:
            raise Http404
        
        context['name'] = name
        context['desc'] = name_to_desc[name]

        chart = _build_graph(name)
        context['chart'] = chart

    return render_to_response("analysis/charts.html", context,
            RequestContext(request))

_default_num_raters = 10

@staff_only
def raters(request):
    """
    Displays the top n raters by one of several metrics.
    """
    context = {}
    context['raters'] = stats.get_global_rater_stats()
    n = 'n' in request.GET and int(request.GET['n']) or _default_num_raters
    context['n'] = n
    context['order_by'] = request.REQUEST.get('order_by', 'n_responses')
    return render_to_response("analysis/raters.html", context,
            RequestContext(request))

_default_num_pivots = 10

@staff_only
def rater_detail(request, rater_id=None):
    context = {'use_nav': True}
    rater = User.objects.get(id=rater_id)
    context['rater'] = rater
    word_chart, kanji_chart = study_list.get_performance_charts(rater)
    word_chart.set_size('350x250')
    kanji_chart.set_size('350x250')
    context['word_chart'] = word_chart
    context['first_test'] = rater.testset_set.order_by('start_time'
            )[0].start_time
    context['last_test'] = rater.testset_set.exclude(end_time=None
            ).order_by('-start_time')[0].end_time
    context['time_tested'] = context['last_test'] - context['first_test']
    context['kanji_chart'] = kanji_chart
    context['stats'] = stats.get_rater_stats(rater)
    context['word_ratio'] = word_chart.get_data()[1][-1] / \
            float(word_chart.get_data()[0][-1])
    context['kanji_ratio'] = kanji_chart.get_data()[1][-1] / \
            float(kanji_chart.get_data()[0][-1])
    return render_to_response('analysis/rater_detail.html', context,
            RequestContext(request))

@staff_only
def rater_csv(request, rater_id=None, data_type=None):
    "Provide an individual rater's performance data in CSV format."
    rater_id = int(rater_id)
    if data_type not in ['kanji', 'word']:
        raise Http404
    
    rater = User.objects.get(id=rater_id)
    word_chart, kanji_chart = study_list.get_performance_charts(rater)
    name = 'rater_%d_%s' % (rater_id, data_type)
    if data_type == 'kanji':
        return _chart_csv_response(kanji_chart, name, data_set_name='charted')
    
    assert data_type == 'word'
    return _chart_csv_response(word_chart, name, data_set_name='charted')

@staff_only
def pivots(request):
    context = {}
    context['syllabi'] = usermodel_models.Syllabus.objects.all()
    return render_to_response("analysis/pivots.html", context,
            RequestContext(request))

@staff_only
def pivots_by_syllabus(request, syllabus_tag=None):
    """
    Displays the top n pivots for a given syllabus.
    """
    if syllabus_tag is None:
        raise Http404

    context = {}

    n = 'n' in request.GET and int(request.GET['n']) or _default_num_pivots
    context['n'] = n

    syllabus_tag = syllabus_tag.replace('_', ' ')
    syllabus = usermodel_models.Syllabus.objects.get(
            tag=syllabus_tag)
    context['syllabus'] = syllabus
    
    order_by = request.GET.get('order_by', 'questions')
    if order_by == 'questions':
        method = stats.get_pivots_by_questions
    elif order_by == 'errors':
        method = stats.get_pivots_by_errors
    
    context['partial_lexemes'] = method(n, syllabus.id, 'w')
    context['partial_kanjis'] = method(n, syllabus.id, 'k')
 
    return render_to_response('analysis/pivots_by_syllabus.html', context,
            RequestContext(request))

@staff_only
def pivot_detail(request, syllabus_tag=None, pivot_type=None, pivot_id=None):
    """
    Describes a single pivot in detail.
    """
    if pivot_type not in ['k', 'w'] or pivot_id is None:
        raise Http404
    pivot_id = int(pivot_id)
    
    context = {}
    context['pivot_type'] = pivot_type
    context['syllabus'] = usermodel_models.Syllabus.objects.get(
            tag=syllabus_tag.replace('_', ' '))

    if pivot_type == 'k':
        pivot = usermodel_models.PartialKanji.objects.get(id=pivot_id)
    else:
        assert pivot_type == 'w'
        pivot = usermodel_models.PartialLexeme.objects.get(id=pivot_id)

    context['pivot'] = pivot
    
    base_response_stats = stats.get_pivot_response_stats(pivot.id, pivot_type)
    context['response_dists'] = [
            (l, charts.PieChart(d.items(), size='750x200'))
            for (l, d) in base_response_stats]
    
    return render_to_response('analysis/pivot_detail.html', context,
            RequestContext(request))

#----------------------------------------------------------------------------#
# HELPERS
#----------------------------------------------------------------------------#

def _chart_csv_response(chart, name, data_set_name=None):
    "Respond with the data from a chart."
    if not data_set_name:
        data_set_name = name.split('_')[2]
    if not settings.DEBUG:
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = \
                'attachment; filename=%s.csv' % name
    else:
        response = HttpResponse(mimetype='text/html')
    writer = csv.writer(response)
    for row in chart.get_data(data_set_name):
        if isinstance(row, (float, int, numpy.number)):
            writer.writerow([row])
        else:
            writer.writerow(row)
                        
    return response

class _Column(object):
    def __init__(self, title, charts_v):
        self.title = title
        self.charts = charts_v

available_charts = (
        _Column('User information', [
            ('user_firstlang',      'First language'),
            ('user_secondlang',     'Second language'),
            ('user_combinedlang',   'Combined languages'),
            ('user_dropout',        'User dropout'),
            ('syllabus_volume',     'Syllabus by # users'),
            ('time_betweentests',   'Time between tests [hist]'),
            ('time_sessions',       'Mean score over sessions'),
            ('user_prepostdiff',    'Pre-post diff'),
            ('user_abilityjlpt3',   'User ability [JLPT 3]'),
            ('user_abilityjlpt4',   'User ability [JLPT 4]'),
        ]),
        _Column('Tests and responses', [
            ('test_mean',       'Mean score on nth test'),
            ('test_normtime',   'Mean score over time [norm]'),
            ('test_time',       'Mean score over time'),
            ('test_volume',     'Users by # tests'),
            ('response_volume', 'Users by # responses'),
            ('test_length',     'Test length by volume'),
            ('test_dropout',    'Mean score vs # tests'),
            ('test_firstlast',  'Last vs first test difference'),
        ]),
        _Column('Questions and plugins', [
            ('pivot_exposures',     'Mean # exposures per pivot'),
            ('plugin_questions',    'Plugin by # questions'),
            ('plugin_error',        'Mean error by plugin'),
            ('plugin_errorbin_early', 'Mean error by plugin [early]'),
            ('plugin_errorbin_mid',  'Mean error by plugin [mid]'),
            ('plugin_errorbin_late', 'Mean error by plugin [late]'),
            ('plugin_errorbin_volume', 'Volume of early/mid/late responses'),
            ('pivot_type',          'Accuracy by word type'),
        ])
    )

name_to_desc = dict(reduce(operator.add, (c.charts for c in \
        available_charts)))

def _build_graph(name):
    "Builds a graph using the given name."
    parts = name.split('_', 1)
    first_part = parts.pop(0)
    try:
        method = globals()['_build_%s_graph' % first_part]
    except KeyError:
        raise KeyError(name)

    return method(*parts)

def _build_user_graph(name):
    if name.endswith('lang'):
        name = name[:-len('lang')]
        dist = stats.get_language_data(name)
        return charts.PieChart(dist.items(), max_options=8)
    
    elif name == 'dropout':
        data = stats.get_dropout_figures()
        approx_data = stats.approximate(data)
        chart = charts.MultiLineChart(approx_data, data_name='histogram',
                x_axis=(0.4, 1.0, 0.1), y_axis=(0, 1.0, 0.1))
        chart.add_data('raw', data)
        return chart
        
    elif name == 'prepostdiff':
        data = [r['pre_post_diff'] for r in stats.get_global_rater_stats()
                if r['n_tests'] > 2 and r['pre_post_diff']]
        hist_data = stats.histogram(data, n_bins=11, normalize=False,
                x_min=-0.7, x_max=0.7)
        chart = charts.LineChart(hist_data, data_name='histogram',
            x_axis=(-0.8, 0.8, 0.2))
        chart.add_data('raw', data)
        return chart
    
    elif name == 'abilityjlpt3':
        data = stats.get_user_scores('jlpt 3')
        hist_data = stats.histogram(data, x_min=0.0, x_max=1.0, normalize=False)
        chart = charts.LineChart(hist_data, data_name='histogram',
                x_axis=(0.0, 1.0, 0.1))
        chart.add_data('raw', data)
        return chart
    
    elif name == 'abilityjlpt4':
        data = stats.get_user_scores('jlpt 4')
        hist_data = stats.histogram(data, x_min=0.0, x_max=1.0, normalize=False)
        chart = charts.LineChart(hist_data, data_name='histogram',
                x_axis=(0.0, 1.0, 0.1))
        chart.add_data('raw', data)
        return chart
        
    raise KeyError(name)

def _build_syllabus_graph(name):
    if name == 'volume':
        return charts.PieChart(stats.get_syllabus_volume())

    raise KeyError(name)

def _build_time_graph(name):
    if name == 'betweentests':
        data = stats.get_time_between_tests()
        hist_data = stats.log_histogram(data, start=1.0/(24*60))
        chart = charts.LineChart(hist_data, data_name='histogram')
        chart.add_data('raw', [(x,) for x in data])
        return chart
    
    elif name == 'sessions':
        data = stats.get_mean_score_over_sessions()
        approx_data = stats.approximate(data, n_points=12)
        chart = charts.MultiLineChart(approx_data, y_axis=(0.0, 1, 0.1),
                x_axis=(0, 1, 0.1), data_name='approximate')
        chart.add_data('raw', data)
        two_colours = charts.color_desc(2).split(',')
        three_colours = ','.join((two_colours[0], two_colours[1],
                two_colours[1]))
        chart['chco'] = three_colours
        return chart
    
    raise KeyError(name)

def _build_test_graph(name):
    if name == 'mean':
        score_data = stats.get_mean_score_nth_test()
        data = stats.group_by_points(score_data, y_max=1.0, y_min=0.0)
        chart = charts.MultiLineChart(data, y_axis=(0, 1, 0.1),
                data_name='grouped')
        chart.add_data('raw', score_data)
        return chart

    elif name == 'volume':
        user_data = stats.get_users_by_n_tests()
        return charts.LineChart(user_data)

    elif name == 'length':
        return charts.PieChart(stats.get_test_length_volume())
        
    elif name == 'normtime':
        user_data = stats.get_score_over_norm_time()
        return charts.LineChart(user_data)
    
    elif name == 'time':
        base_data = stats.get_score_over_time()
        data = stats.approximate(base_data)
        chart = charts.MultiLineChart(data, y_axis=(0, 1.05, 0.1), 
                data_name='approximate')
        chart.add_data('raw', base_data)
        two_colours = charts.color_desc(2).split(',')
        three_colours = ','.join((two_colours[0], two_colours[1],
                two_colours[1]))
        chart['chco'] = three_colours
        return chart
    
    elif name == 'dropout':
        return charts.LineChart(stats.get_mean_score_by_n_tests())

    elif name == 'firstlast':
        data = stats.get_first_last_test()
        hist_data = stats.histogram(data, n_bins=11, normalize=False,
                x_min=-0.5, x_max=0.5)
        chart = charts.LineChart(hist_data, data_name='histogram',
                x_axis=(-0.5, 0.5, 0.1))
        chart.add_data('raw', data)
        return chart

    raise KeyError(name)

def _build_response_graph(name):
    if name == 'volume':
        user_data = stats.get_users_by_n_responses()
        chart = charts.LineChart(user_data)
        return chart

    raise KeyError(name)

def _build_pivot_graph(name):
    if name == 'exposures':
        data = stats.get_mean_exposures_per_pivot()
        return charts.BarChart(data, y_axis=(0, 50, 10))

    if name == 'type':
        data = stats.get_accuracy_by_pivot_type()
        return charts.BarChart(data, y_axis=(0, 1, 0.1))
    
    raise KeyError(name)

def _build_plugin_graph(name):
    if '_' in name:
        name, subpart = name.split('_', 1)
    else:
        subpart = None
    
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
        raw_data = stats.get_mean_error_by_plugin()
        data = _accumulate_plugin_errors(raw_data)
        k = (1 + settings.N_DISTRACTORS)
        data.append(('[random guess]', (k-1)/float(k)))
        chart = charts.BarChart(data, y_axis=(0,1.0,0.2))
        chart.add_data('raw', raw_data)
        return chart
    
    elif name == 'errorbin':
        data_sets = stats.get_power_binned_error_by_plugin()
        is_error_chart = True
        if subpart == 'early':
            raw_data = data_sets[0]
            data = _accumulate_plugin_errors(raw_data)
        elif subpart == 'mid':
            raw_data = data_sets[1]
            data = _accumulate_plugin_errors(raw_data)
        elif subpart == 'late':
            raw_data = data_sets[2]
            data = _accumulate_plugin_errors(raw_data)
        elif subpart == 'volume':
            is_error_chart = False
            data = zip(['Early', 'Mid', 'Late'], map(len, data_sets))
        else:
            raise KeyError(name)
            
        if is_error_chart:
            chart = charts.BarChart(data)#, y_axis=(0, 0.5, 0.1))
            chart.add_data('raw', raw_data)
        else:
            chart = charts.BarChart(data)
        return chart

    raise KeyError(name)    

def _accumulate_plugin_errors(raw_data):
    data = []
    for label, scores in itertools.groupby(raw_data, lambda x: x[0]):
        data.append((label, mean(v for (l, v) in scores)))
    return data    

# vim: ts=4 sw=4 sts=4 et tw=78:
