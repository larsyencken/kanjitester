# -*- coding: utf-8 -*-
#
#  alignment.py
#  kanji_test
# 
#  Created by Lars Yencken on 06-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Resouces for parsing and utilising alignments.
"""

from itertools import izip

class FormatError(Exception): pass

_gp_sep = u':'
_seg_sep = u'|'

class Alignment(object):
    __slots__ = ('g_segs', 'p_segs')

    def __init__(self, g_segs, p_segs):
        if len(g_segs) != len(p_segs):
            raise ValueError('segment lengths must match')

        self.g_segs = g_segs
        self.p_segs = p_segs

    def grapheme(self):
        return u''.join(self.g_segs)
    grapheme = property(grapheme)

    def phoneme(self):
        return u''.join(self.p_segs)
    phoneme = property(phoneme)

    def __len__(self):
        return len(self.g_segs)

    def __iter__(self):
        for item in izip(self.g_segs, self.p_segs):
            yield item

    def __unicode__(self):
        return ' '.join(
                [_seg_sep.join(self.g_segs), _seg_sep.join(self.p_segs)],
            )
    
    @classmethod
    def from_line(cls, line):
        parts = line.rstrip().split(_gp_sep)
        try:
            entry, alignment = parts
            g_segs, p_segs = alignment.split()
        except ValueError:
            raise FormatError(line)

        return cls(g_segs.split(_seg_sep), p_segs.split(_seg_sep))
    
# vim: ts=4 sw=4 sts=4 et tw=78:

