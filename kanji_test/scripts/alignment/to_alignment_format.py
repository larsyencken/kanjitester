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

from kanji_test.user_model.bundle import SyllabusBundle  

def to_alignment_format(syllabus_name, output_file):
    syllabus = SyllabusBundle(syllabus_name)

    o_stream = sopen(output_file, 'w')
    for word in syllabus.words:
        if word.reading and word.surface:
            print >> o_stream, word.surface, word.reading
    o_stream.close()

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] syllabus_name ouput_file

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
