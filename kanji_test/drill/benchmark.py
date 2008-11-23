#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  benchmark.py
#  kanji_test
# 
#  Created by Lars Yencken on 23-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
"""

import os, sys, optparse
import time
import cProfile

from cjktools.common import sopen
from django.contrib.auth.models import User

from kanji_test.user_profile.models import UserProfile
from kanji_test.user_model.models import Syllabus, ErrorDist
from kanji_test.drill.models import TestSet

def benchmark(n_sets, n_questions):
    test_user = _new_test_user()
    start_time = time.time()
    for i in xrange(n_sets):
        test_set = TestSet.from_user(test_user, n_questions)
    end_time = time.time()
    test_user.delete()
    time_taken = end_time - start_time
    print 'Total time: %.2f' % time_taken
    print 'Per test set: %.2f' % (time_taken / n_sets)
    print 'Per question: %.2f' % (time_taken / (n_sets * n_questions))

def _new_test_user():
    User.objects.filter(username='test_user').delete()
    test_user = User(username='test_user')
    test_user.save()
    test_user.userprofile_set.create(syllabus=Syllabus.objects.all(
            ).order_by('?')[0])
    ErrorDist.init_from_priors(test_user)

    return test_user

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] 

Benchmarks test-set creation."""

    parser = optparse.OptionParser(usage)

    parser.add_option('-n', '--nsets', action='store', dest='n_sets',
            type='int', help='The number of test sets to generate [10]',
            default=10)
    
    parser.add_option('-q', '--questions', action='store', dest='n_questions',
            type='int', help='The number of questions to generate [10]',
            default=10)

    parser.add_option('-o', '--output', action='store', dest='filename',
            help='Store profiling information to the given file.')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if args:
        parser.print_help()
        sys.exit(1)

    if options.filename:
        User.objects.filter(username='test_user').delete()
        cProfile.runctx('benchmark(options.n_sets, options.n_questions)',
                globals(), locals(), options.filename)
    else:
        benchmark(options.n_sets, options.n_questions)
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
