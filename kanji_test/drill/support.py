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

def build_options(item, sample_method, exclude_set=None):
    exclude_set = set(exclude_set or [])
    exclude_set.add(item)

    if not containsScript(Script.Kanji, item):
        raise ValueError("Can't generate options without kanji")

    distractors = []
    annotations = []
    while len(distractors) < settings.N_DISTRACTORS:
        result = []
        for char in item:
            if scriptType(char) == Script.Kanji:
                result.append(sample_method(char))
            else:
                result.append(char)
        seg_result = u'|'.join(result)
        base_result = u''.join(result)
        if base_result not in exclude_set:
            exclude_set.add(base_result)
            distractors.append(base_result)
            annotations.append(seg_result)

    return distractors, annotations

# vim: ts=4 sw=4 sts=4 et tw=78:
