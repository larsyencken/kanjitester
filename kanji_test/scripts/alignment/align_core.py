# -*- coding: utf-8 -*-
#
#  align_core.py
#  kanji_test
# 
#  Created by Lars Yencken on 28-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
An interface to the expected alignments for a syllabus. 
"""

import itertools

from kanji_test.user_model.bundle import SyllabusBundle, WordEntry
from kanji_test.user_model import models

def iter_words(syllabus_name):
    """
    Returns an iterator over all the words which are expected to have
    alignments for the given syllabus.
    """
    combined_source = itertools.chain(
            SyllabusBundle(syllabus_name).words,
            _database_stream(syllabus_name),
        )

    seen_set = set()
    for word in combined_source:
        if word in seen_set:
            continue

        if word.reading and word.has_kanji():
            seen_set.add(word)
            yield word

def _database_stream(syllabus_name):
    syllabus = models.Syllabus.objects.get(tag=syllabus_name.replace('_', ' '))
    for partial_lexeme in syllabus.partiallexeme_set.all():
        # Assume only one reading available
        for reading in partial_lexeme.reading_set.all():
            for surface in partial_lexeme.surface_set.filter(has_kanji=True):
                yield WordEntry(reading.reading, surface.surface, '')

# vim: ts=4 sw=4 sts=4 et tw=78:
