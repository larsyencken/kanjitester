#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  from_aligned_file.py
#  kanji_test
# 
#  Created by Lars Yencken on 06-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

import sys, optparse

import consoleLog
from cjktools.common import sopen
from cjktools import scripts

from kanji_test.user_model.bundle import SyllabusBundle
from kanji_test.util.alignment import AlignedFile

_log = consoleLog.default

def from_aligned_file(syllabus_name, aligned_file, output_file):
    _log.start('Extracting gp-aligned words', nSteps=3)

    _log.log('Loading syllabus')
    bundle = SyllabusBundle(syllabus_name)
    include_set = set((w.surface, w.reading) for w in bundle.words if \
            scripts.containsScript(scripts.Script.Kanji, w.surface))

    _log.log('Loading alignments')
    alignments = AlignedFile(aligned_file)
    
    _log.log('Saving alignments')
    o_stream = sopen(output_file, 'w')
    for alignment in alignments:
        key = (alignment.grapheme, alignment.phoneme)
        if key in include_set:
            print >> o_stream, alignment.to_line()
            include_set.remove(key)
    o_stream.close()

    if include_set:
        _log.start('%d entries not found' % len(include_set),
                nSteps=len(include_set))
        for surface, reading in sorted(include_set):
            _log.log('%s /%s/' % (surface, reading))
        _log.finish()
    else:
        _log.finish('All entries found')

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] syllabus_name aligned_file output_file

Extracts the alignments for the words in the syllabus from the aligned file."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            default=False, help='Enables debugging mode [False]')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    try:
        (syllabus_words, aligned_file, aligned_output) = args
    except ValueError:
        parser.print_help()
        sys.exit(1)

    from_aligned_file(syllabus_words, aligned_file, aligned_output)
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
