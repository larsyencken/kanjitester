# -*- coding: utf-8 -*-
#
#  bundle.py
#  kanji_test
# 
#  Created by Lars Yencken on 27-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
An interface to syllabus filesystem resources, known as bundles.
"""

from os import path
import operator
import glob

from django.conf import settings
from cjktools import scripts
from cjktools.common import sopen

from kanji_test.util.alignment import AlignedFile

_syllabi_path = path.join(settings.DATA_DIR, 'syllabus')

class BundleError(Exception): pass

class SyllabusBundle(object):
    """
    A convenience container for the resources required to fully specify a
    syllabus.

    >>> s = SyllabusBundle('jlpt_4')
    >>> len(s.chars)
    80
    >>> len(s.words)
    683
    >>> len(s.alignments)
    627
    """
    def __init__(self, name):
        self.name = name
        self.verbose_name = name.replace('_', ' ')

        if not self.verify(name):
            raise BundleError("bundle for %s is missing resources" % name)

        self.alignments = AlignedFile(self.get_aligned_filename(name))
        self.chars = CharFile(self.get_char_filename(name))
        self.words = WordFile(self.get_word_filename(name))

    @staticmethod
    def get_char_filename(name):
        return path.join(_syllabi_path, name + '.chars')

    @staticmethod
    def get_word_filename(name):
        return path.join(_syllabi_path, name + '.words')

    @staticmethod
    def get_aligned_filename(name):
        return path.join(_syllabi_path, name + '.aligned')

    @classmethod
    def get_dependencies(cls, name):
        return [
            cls.get_char_filename(name),
            cls.get_word_filename(name),
            cls.get_aligned_filename(name),
        ]

    @classmethod
    def verify(cls, name):
        "Checks that all the required files are available for this name."
        return reduce(
                operator.and_,
                map(path.exists, cls.get_dependencies(name)),
            )

def iter_bundles():
    "Returns an iterator over bundles for all valid syllabi."
    for name in list_names():
        yield SyllabusBundle(name)

def list_names():
    "Returns a list of the available and verified syllabi."
    syllabi = []
    glob_pattern = path.join(_syllabi_path, '*.words')
    for word_filename in glob.glob(glob_pattern):
        syllabus_name = path.splitext(path.basename(word_filename))[0]
        if SyllabusBundle.verify(syllabus_name):
            syllabi.append(syllabus_name)

    return syllabi

class CharFile(set):
    "A wrapper for syllabus character lists. "
    def __init__(self, filename):
        i_stream = sopen(filename)
        uniqueKanji = scripts.uniqueKanji
        for line in i_stream:
            if line.lstrip().startswith('#'):
                continue
            self.update(uniqueKanji(line))
        i_stream.close()

class WordEntry(object):
    __slots__ = ('reading', 'surface', 'notes')

    def __init__(self, reading, surface, notes):
        self.reading = reading
        self.surface = surface
        self.notes = notes

    def has_kanji(self):
        return scripts.containsScript(scripts.Script.Kanji, self.surface)

    @classmethod
    def from_line(cls, line):
        return cls(*line.replace(u'〜', '').rstrip('\n').split('\t'))

    def to_line(self):
        return '%s\t%s\t%s' % (self.reading, self.surface, self.notes)

    def __hash__(self):
        return hash(self._tuple())

    def _tuple(self):
        return (self.reading, self.surface, self.notes)

    def __cmp__(self, rhs):
        return cmp(self._tuple(), rhs._tuple())

    def __eq__(self, rhs):
        return self._tuple() == rhs._tuple()

class FormatError(Exception): pass

class WordFile(object):
    "A wrapper for syllabus word files."
    def __init__(self, filename):
        self._words = []
        i_stream = sopen(filename)
        for i, line in enumerate(i_stream):
            if line.lstrip().startswith('#'):
                continue

            try:
                self._words.append(WordEntry.from_line(line))
            except:
                raise FormatError('on line %d of %s' % (i + 1, filename))
        i_stream.close()

    def __iter__(self):
        return iter(self._words)

    def __len__(self):
        return len(self._words)

# vim: ts=4 sw=4 sts=4 et tw=78:
