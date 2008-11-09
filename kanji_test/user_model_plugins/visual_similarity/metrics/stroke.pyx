# 
#  stroke.pyx
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-15.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

"""
Optimised Levenstein distance calculation between stroke signatures for two
kanji.
"""

#----------------------------------------------------------------------------#

import os

from cjktools.exceptions import DomainError
from cjktools.common import sopen

from kanji_test import settings

#----------------------------------------------------------------------------#

_strokes_file = os.path.join(settings.DATA_DIR, 'structure', 'strokes_ulrich')

cdef class StrokeEditDistance:
    """The edit distance between stroke sequences for both kanji."""
    cdef readonly signatures
    cdef readonly object stroke_types
    cdef readonly int n_stroke_types

    def __init__(self):
        self.stroke_types = {}
        self.n_stroke_types = 0

        # Convert stroke sequence to integer sequences by constructing a 
        # mapping from stroke types to integers.
        self.signatures = {}
        i_stream = sopen(_strokes_file)
        for i, line in enumerate(i_stream):
            kanji, raw_strokes = line.rstrip().split()
            raw_strokes = raw_strokes.split(',')
            strokes = []
            for raw_stroke in raw_strokes:
                strokes.append(self._get_stroke_type(raw_stroke))
            self.signatures[kanji] = strokes
        i_stream.close()

    cdef _get_stroke_type(self, stroke):
        try:
            return self.stroke_types[stroke]
        except KeyError:
            pass

        self.stroke_types[stroke] = self.n_stroke_types
        self.n_stroke_types = self.n_stroke_types + 1

        return self.n_stroke_types - 1
    
    def raw_distance(self, kanji_a, kanji_b):
        try:
            s_py = self.signatures[kanji_a]
            t_py = self.signatures[kanji_b]
        except KeyError, e:
            raise DomainError, e

        return edit_distance(s_py, t_py)

    def __call__(self, kanji_a, kanji_b):
        try:
            s_py = self.signatures[kanji_a]
            t_py = self.signatures[kanji_b]
        except KeyError, e:
            raise DomainError, e

        result = edit_distance(s_py, t_py)
        return float(result) / max(len(s_py), len(t_py))

#----------------------------------------------------------------------------#

cdef edit_distance(s_py, t_py):
    cdef int m, n, i, j
    cdef int table[50][50]
    cdef int s[50]
    cdef int t[50]
    cdef int up, left, diag, cost

    s_len = len(s_py)
    t_len = len(t_py)
    if s_len > 49 or t_len > 49:
        raise ValueError, "stroke sequences too long"

    # Copy s_py to s
    for 0 <= i < s_len:
        table[i][0] = i
        s[i] = s_py[i]
    table[s_len][0] = s_len

    # Copy t_py to t
    for 0 <= j < t_len:
        table[0][j] = j
        t[j] = t_py[j]
    table[0][t_len] = t_len

    # Perform edit distance
    for 1 <= i <= s_len:
        for 1 <= j <= t_len:
            if s[i-1] == t[j-1]:
                cost = 0
            else:
                # XXX Could do better than uniform penalty funtion.
                cost = 1

            # table[i][j] = min(up, left, diag)
            up = table[i-1][j] + 1
            left = table[i][j-1] + 1
            diag = table[i-1][j-1] + cost
            if up <= left:
                if up <= diag:
                    table[i][j] = up
                else:
                    table[i][j] = diag
            else:
                if left <= diag:
                    table[i][j] = left
                else:
                    table[i][j] = diag

    return table[s_len][t_len]

#----------------------------------------------------------------------------#
