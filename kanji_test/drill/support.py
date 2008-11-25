# -*- coding: utf-8 -*-
#
#  support.py
#  kanji_test
# 
#  Created by Lars Yencken on 05-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Supporting methods for drill plugins.
"""

from cjktools.scripts import Script, scriptType, containsScript

from kanji_test import settings

def build_options(pivot, sample_n_method, exclude_set=None):
    """
    Builds a series of distractors for a question, based on its pivot and
    a method which samples into the distractor space.
    """
    assert isinstance(pivot, unicode)
    exclude_set = set(exclude_set or [])
    exclude_set.add(pivot)

    if not containsScript(Script.Kanji, pivot):
        raise ValueError("Can't generate options without kanji")

    distractors = []
    annotation_map = {}
    while len(distractors) < settings.N_DISTRACTORS:
        potentials = []
        for char in pivot:
            potentials.append(sample_n_method(char, settings.N_DISTRACTORS,
                    exclude_set))
        potentials = zip(*potentials)

        for result in potentials:
            seg_result = u'|'.join(result)
            base_result = u''.join(result)
            if base_result not in exclude_set:
                exclude_set.add(base_result)
                distractors.append(base_result)
                annotation_map[base_result] = seg_result
                if len(distractors) == settings.N_DISTRACTORS:
                    break

    return distractors, annotation_map

# vim: ts=4 sw=4 sts=4 et tw=78:
