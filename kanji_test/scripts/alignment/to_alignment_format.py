#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  to_alignment_format.py
#  kanji_test
# 
#  Created by Lars Yencken on 05-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Converts a syllabus file to alignment format, pruning any non-kanji entries.
"""

import sys, optparse

from cjktools.common import sopen

import align_core

def to_alignment_format(syllabus_name, output_file):
    o_stream = sopen(output_file, 'w')
    for word in align_core.iter_words(syllabus_name):
        if word.reading and word.has_kanji():
            print >> o_stream, word.surface, word.reading
    o_stream.close()

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] syllabus_name ouput_file

Converts the syllabus word file into alignment format."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--db', action='store_true', dest='use_database',
            default=False, help='Use surfaces from the database')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    try:
        (syllabus_name, output_name) = args
    except ValueError:
        parser.print_help()
        sys.exit(1)

    return to_alignment_format(syllabus_name, output_name)

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
