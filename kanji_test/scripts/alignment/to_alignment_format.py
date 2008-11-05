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

import os, sys, optparse
import re

from cjktools.common import sopen

def to_alignment_format(syllabus_file, output_file):
    i_stream = sopen(syllabus_file)
    o_stream = sopen(output_file, 'w')
    for line in i_stream:
        line = re.sub(u'\t\[.*\]', u'', line, re.UNICODE)
        line = line.strip().split('\t')
        if len(line) == 1:
            continue

        reading, surface = line
        print >> o_stream, surface, reading
    o_stream.close()
    i_stream.close()

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] syllabus_file ouput_file

Converts the syllabus word file into alignment format."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            default=False, help='Enables debugging mode [False]')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    try:
        (syllabus_file, output_file) = args
    except ValueError:
        parser.print_help()
        sys.exit(1)

    to_alignment_format(syllabus_file, output_file)
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
