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

def build_options(segments, sample_n_method, exclude_samples=None,
        exclude_values=None):
    """
    Builds a series of distractors for a question, based on a method which
    samples from the segment space into the distractor space.
    """
    exclude_samples = set(exclude_samples or [])
    exclude_values = set(exclude_values or [] )
    distractors = []
    annotation_map = {}
    while len(distractors) < settings.N_DISTRACTORS:
        potentials = []
        for segment in segments:
            potentials.append(sample_n_method(segment, settings.N_DISTRACTORS,
                    exclude_samples))
        potentials = zip(*potentials)

        for result in potentials:
            base_result = u''.join(result)
            if base_result not in exclude_values:
                exclude_values.add(base_result)
                distractors.append(base_result)
                annotation_map[base_result] = u'|'.join(result)
                if len(distractors) == settings.N_DISTRACTORS:
                    break

    return distractors, annotation_map

# vim: ts=4 sw=4 sts=4 et tw=78:
