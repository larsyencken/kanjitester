#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  clean_data.py
#  kanji_test
# 
#  Created by Lars Yencken on 27-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

"""
"""

import os, sys, optparse

from django.contrib.auth.models import User
import consoleLog

from kanji_test.drill import models

_log = consoleLog.default

def clean_data(email_address): 
    _log.start('Cleaning address %s' % email_address)
    _log.start('Checking database')
    users = User.objects.filter(email=email_address)
    _log.finish('Found %d user%s: %s' % (
            len(users), 
            (len(users) != 1) and 's' or '', # pluralize
            ', '.join(u.username for u in users)
        ))

    for user in users:
        _log.start('Cleaning %s' % user.username)
        test_sets = models.TestSet.objects.filter(user=user)

        _log.log('Removing %d test sets ' % test_sets.count())
        test_sets.delete()

        responses = models.Response.objects.filter(user=user)
        _log.log('Removing %d responses' % responses.count())
        responses.delete()

        _log.finish()
    _log.finish()

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] email_address

Cleans the database by removing data for all users with the given email
address."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            default=False, help='Enables debugging mode [False]')

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    try:
        email_address, = args
    except ValueError:
        parser.print_help()
        sys.exit(1)

    # Avoid psyco in debugging mode, since it merges stack frames.
    if not options.debug:
        try:
            import psyco
            psyco.profile()
        except:
            pass

    clean_data(email_address)
    
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
