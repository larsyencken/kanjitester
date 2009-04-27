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

from kanji_test import settings

def build_kanji_options(kanji, error_dist, exclude_set=None, adaptive=True):
    exclude_set = set(exclude_set or [])
    annotation_map = {}
    distractors = []
    while len(distractors) < settings.N_DISTRACTORS:
        if adaptive:
            potentials = error_dist.sample_n(kanji, settings.N_DISTRACTORS,
                    exclude_set)
        else:
            potentials = error_dist.sample_n_uniform(kanji,
                    settings.N_DISTRACTORS, exclude_set)

        for result in potentials:
            exclude_set.add(result)
            distractors.append(result)
            annotation_map[result] = result # No segments
            if len(distractors) == settings.N_DISTRACTORS:
                break

    return distractors, annotation_map

def build_word_options(segments, error_dist, exclude_set=None, adaptive=True):
    """
    Builds a series of distractors for a question, based on a method which
    samples from the segment space into the distractor space.
    """
    distractors = []
    annotation_map = {}
    while len(distractors) < settings.N_DISTRACTORS:
        if adaptive:
            potentials = error_dist.sample_seq_n(segments,
                    settings.N_DISTRACTORS, exclude_set=exclude_set)
        else:
            potentials = error_dist.sample_seq_n_uniform(segments,
                    settings.N_DISTRACTORS, exclude_set=exclude_set)
        for result in potentials:
            base_result = u''.join(result)
            if base_result not in exclude_set:
                exclude_set.add(base_result)
                distractors.append(base_result)
                annotation_map[base_result] = u'|'.join(result)
                if len(distractors) == settings.N_DISTRACTORS:
                    break

    return distractors, annotation_map

# vim: ts=4 sw=4 sts=4 et tw=78:
