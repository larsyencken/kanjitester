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

def build_kanji_options(item, sample_method, exclude_set=None):
    exclude_set = set(exclude_set or [])
    exclude_set.add(item)

    if not containsScript(Script.Kanji, item):
        raise ValueError("Can't generate options without kanji")

    distractors = []
    template = list(item)
    while len(distractors) < settings.N_DISTRACTORS:
        result = []
        for char in template:
            if scriptType(char) == Script.Kanji:
                result.append(sample_method(char))
            else:
                result.append(kanji_source)
        result = u''.join(result)
        if result not in exclude_set:
            distractors.append(result)
            exclude_set.add(result)

    return distractors

# vim: ts=4 sw=4 sts=4 et tw=78:
