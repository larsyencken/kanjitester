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

from kanji_test.analysis.decorators import staff_only
from kanji_test.drill.models import MultipleChoiceResponse, TestSet
from kanji_test.util.probability import FreqDist

@staff_only
def analysis_home(request):
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

    test_dist = get_test_size_dist()
    dist_values = [(k, test_dist.freq(k)) for k in sorted(test_dist.samples())]
    context['test_dist'] = dist_values

    return render_to_response("analysis/home.html", context,
            RequestContext(request))

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

def get_test_size_dist():
    "Fetches the distribution of test sizes chosen by users."
    cursor = connection.cursor()
    cursor.execute("""
        SELECT n_items, COUNT(*) FROM (
            SELECT testset_id, COUNT(*) as n_items
            FROM drill_testset_responses
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
    
# vim: ts=4 sw=4 sts=4 et tw=78:
