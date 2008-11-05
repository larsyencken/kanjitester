#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  from_aligned_file.py
#  kanji_test
# 
#  Created by Lars Yencken on 06-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

import os, sys, optparse
from itertools import imap
import string

import consoleLog
from cjktools.common import sopen

_log = consoleLog.default

def from_aligned_file(syllabus_words, aligned_file, aligned_output):
    _log.start('Extracting gp-aligned words', nSteps=3)

    _log.start('Loading syllabus entries from %s' % \
            os.path.basename(syllabus_words), nSteps=1)
    include_set = set(imap(string.strip, sopen(syllabus_words)))
    _log.log('%d entries' % len(include_set))
    _log.finish()

    _log.log('Extracting words from %s' % os.path.basename(aligned_file))
    i_stream = sopen(aligned_file)
    o_stream = sopen(aligned_output, 'w')
    for line in i_stream:
        entry = line.split(':')[0]
        if entry in include_set:
            o_stream.write(line)
            include_set.remove(entry)
    o_stream.close()
    i_stream.close()
    if include_set:
        _log.start('%d entries not found' % len(include_set),
                nSteps=len(include_set))
        for entry in sorted(include_set):
            _log.log(entry)
        _log.finish()
    else:
        _log.log('All entries found')
    _log.finish()
    return

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] syllabus_words aligned_file aligned_output

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
