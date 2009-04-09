#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dump_errors.py
#  kanji_test
# 
#  Created by Lars Yencken on 08-04-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

"""
Dumps all user errors into a simple CSV format for processing using other
tools.
"""

import sys, optparse
import csv

from cjktools.common import sopen
from django.conf import settings

from kanji_test.drill import models

def dump_errors(output_file):
    ostream = sopen(output_file, 'w')
    fields = ['item', 'item_type', 'question_type', 'user_answer',
            'correct_answer']
    for i in xrange(settings.N_DISTRACTORS - 1):
        fields.append('other_distractor_%d' % (i + 1))
    print >> ostream, '#' + ','.join(fields)
    writer = csv.writer(ostream)
    
    for response in models.MultipleChoiceResponse.objects.filter(
            option__is_correct=False):
        row = []
        row.append(response.question.pivot)
        row.append(response.question.pivot_type)
        row.append(response.question.question_type)
        
        user_answer = response.option.value
        all_options = response.option.question.options.all()
        correct_answer = all_options.get(is_correct=True).value
        distractors = [o.value for o in all_options 
                if not o.is_correct and o.value != user_answer]
        row.append(user_answer)
        row.append(correct_answer)
        row.extend(distractors)
        writer.writerow(row)
    ostream.close()

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] output_file

Dumps all user errors into a simple CSV format. The output consists of 
series of lines containing:

<item>,<item_type>,<question_type>,<user_answer>,<correct_answer>,...

after which all remaining distractors are listed."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            default=False, help='Enables debugging mode [False]')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if len(args) != 1:
        parser.print_help()
        sys.exit(1)

    output_file = args[0]
    dump_errors(output_file)
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
