# -*- coding: utf-8 -*-
#
#  stats.py
#  kanji_test
# 
#  Created by Lars Yencken on 16-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Methods for accessing user performance statistics.
"""

from kanji_test.drill import models

def get_stats(user):
    "Returns a dictionary of user statistics, or None if none are available."
    stats = {'has_questions': True}
    stats['n_tests'] = models.TestSet.objects.filter(user=user).count()

    responses = models.MultipleChoiceResponse.objects.filter(user=user)
    stats['long_run'] = _check_stats(responses)
    
    if stats['long_run']['n_questions'] == 0:
        return {'has_questions': False}
    
    most_recent = models.TestSet.get_latest(user).responses.all()

    stats['most_recent'] = _check_stats(most_recent)
    return stats

def _check_stats(question_query):
    n_questions = question_query.count()
    n_correct = question_query.filter(option__is_correct=True).count()
    if n_questions:
        pc_correct = (100.0 * n_correct) / n_questions
    else:
        pc_correct = None

    return locals()

# vim: ts=4 sw=4 sts=4 et tw=78:

