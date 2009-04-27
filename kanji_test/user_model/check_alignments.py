#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  check_alignments.py
#  kanji_test
# 
#  Created by Lars Yencken on 11-03-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

"""
"""

import sys, optparse

import consoleLog
from cjktools import scripts

from kanji_test.user_model import models

_log = consoleLog.default

def check_alignments():
    for syllabus in models.Syllabus.objects.all():
        _log.start('Checking %s' % syllabus.tag)
        _check_syllabus(syllabus)
        _log.finish()
    return

#----------------------------------------------------------------------------#

def _check_syllabus(syllabus):
    """Checks for alignment errors in the syllabus."""
    prior_dist = models.PriorDist.objects.get(syllabus=syllabus,
            tag='reading | kanji')
    problems = []
    for partial_lexeme in syllabus.partiallexeme_set.all():
        for alignment in partial_lexeme.alignments:
            for g_seg, p_seg in alignment:
                if not scripts.contains_script(scripts.Script.Kanji, g_seg):
                    continue
                if prior_dist.density.filter(condition=g_seg, 
                        symbol=p_seg).count() != 1:
                    problems.append(
                            (alignment.alignment, g_seg, p_seg)
                        )

    problems_by_alignment = {}
    for alignment, g_seg, p_seg in problems:
        last_cases = problems_by_alignment.setdefault(alignment, list())
        last_cases.append((g_seg, p_seg))
    
    for alignment, cases in sorted(problems_by_alignment.iteritems()):
        _log.start(alignment, nSteps=len(cases))
        for g_seg, p_seg in cases:
            _log.log(u'No match for %s /%s/' % (g_seg, p_seg))
        _log.finish()

def _create_option_parser():
    usage = \
"""%prog [options]

Checks the alignments for all syllabi."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            default=False, help='Enables debugging mode [False]')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if args:
        parser.print_help()
        sys.exit(1)

    # Avoid psyco in debugging mode, since it merges stack frames.
    if not options.debug:
        try:
            import psyco
            psyco.profile()
        except:
            pass

    check_alignments()
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78: