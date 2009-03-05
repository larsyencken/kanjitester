# -*- coding: utf-8 -*-
#
#  study_list.py
#  kanji_test
# 
#  Created by Lars Yencken on 27-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

import time 

from django.db import connection
from django.contrib.auth.models import User
from cjktools import scripts

from kanji_test.util import charts

def get_study_list(user):
    "Returns two sets, one of word mistakes and one of kanji mistakes."
    response_data = _fetch_response_data(user)

    mistakes_w = set()
    mistakes_k = set()
    for pivot, pivot_type, is_correct, timestamp in response_data:
        if pivot_type == 'k':
            mistake_set = mistakes_k
        elif pivot_type == 'w':
            mistake_set = mistakes_w
        else:
            raise ValueError('bad pivot type: %s' % pivot_type)

        if is_correct:
            mistake_set.discard(pivot)
        else:
            mistake_set.add(pivot)

    return mistakes_w, mistakes_k

def get_performance_charts(user):
    """
    Returns two charts, one of word performance and exposure, the other of
    kanji.
    """
    response_data = _fetch_response_data(user)
    if not response_data:
        return None

    colours = '000000,3030ff'
    
    word_data, kanji_data = _get_performance_analysis(response_data)
    
    word_chart = charts.SimpleLineChart(word_data)
    word_chart['chtt'] = 'Words'
    word_chart['chdl'] = 'Tested|Correct'
    word_chart['chco'] = colours
    
    kanji_chart = charts.SimpleLineChart(kanji_data)
    kanji_chart['chtt'] = 'Kanji'
    kanji_chart['chdl'] = 'Tested|Correct'
    kanji_chart['chco'] = colours
    
    return word_chart, kanji_chart

#----------------------------------------------------------------------------#

def _fetch_response_data(user):
    cursor = connection.cursor()
    cursor.execute("""
        SELECT q.pivot, q.pivot_type, q_time.is_correct, q_time.timestamp
        FROM (
            SELECT mco.question_id, mco.is_correct, ot.timestamp
            FROM (
                SELECT mcr.option_id, rbt.timestamp
                FROM (
                    SELECT id, timestamp FROM drill_response
                    WHERE user_id = %s
                ) AS rbt
                INNER JOIN drill_multiplechoiceresponse AS mcr
                ON mcr.response_ptr_id = rbt.id
            ) AS ot
            INNER JOIN drill_multiplechoiceoption AS mco
            ON mco.id = ot.option_id
        ) AS q_time
        INNER JOIN drill_question AS q
        ON q.id = q_time.question_id
        ORDER BY q_time.timestamp ASC
    """, (user.id, ))
    data = cursor.fetchall()
    return data

def _build_sets(study_list):
    kanji = set()
    words = set()
    for pivot, pivot_type, is_correct, timestamp in study_list:
        if pivot_type == 'k':
            pivot_set = kanji
        elif pivot_type == 'w':
            pivot_set = words
        else:
            raise ValueError('bad pivot type: %s' % pivot_type)

        if is_correct:
            pivot_set.discard(pivot)
        else:
            pivot_set.add(pivot)


    print '%d kanji' % len(kanji)
    print '%d words' % len(words)

def _embellish(response_data):
    """Adds kanji contained in words as kanji exposed."""
    kanji_script = scripts.Script.Kanji
    for pivot, pivot_type, is_correct, timestamp in response_data:
        yield (pivot, pivot_type, is_correct, timestamp)
        if pivot_type == 'w' and scripts.containsScript(kanji_script, pivot):
            for kanji in scripts.uniqueKanji(pivot):
                yield kanji, 'k', is_correct, timestamp

def _get_performance_analysis(response_data):
    current_time = None
    unique_w = set()
    correct_w = set()
    unique_w_t = []
    correct_w_t = []
    unique_k = set()
    correct_k = set()
    unique_k_t = []
    correct_k_t = []
    for pivot, pivot_type, is_correct, timestamp in _embellish(response_data):
        if current_time != timestamp:
            # Flush previous timestamp's data
            unique_w_t.append(len(unique_w))
            correct_w_t.append(len(correct_w))
            unique_k_t.append(len(unique_k))
            correct_k_t.append(len(correct_k))
            current_time = timestamp

        if pivot_type == 'w':
            unique_w.add(pivot)
            if is_correct:
                correct_w.add(pivot)
            else:
                correct_w.discard(pivot)
        elif pivot_type == 'k':
            unique_k.add(pivot)
            if is_correct:
                correct_k.add(pivot)
            else:
                correct_k.discard(pivot)

    else:
        unique_w_t.append(len(unique_w))
        correct_w_t.append(len(correct_w))
        unique_k_t.append(len(unique_k))
        correct_k_t.append(len(correct_k))

    return (unique_w_t, correct_w_t), (unique_k_t, correct_k_t)

# vim: ts=4 sw=4 sts=4 et tw=78:
