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
from kanji_test.user_profile.models import UserProfile

_log = consoleLog.default

def clean_user_data(email=None, username=None): 
    if not email:
        raise Exception('need email for now')
    elif username:
        raise Exception("don't support username yet")

    _log.start('Cleaning address %s' % email)
    _log.start('Checking database')
    users = User.objects.filter(email=email)
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
    
language_map = {
    'En':           'English',
    'Eng':          'English',
    'Frenc':        'French',
    'Deutsch':      'German',
    'Malaysian':    'Malay',
    'Mongolia':     'Mongolian',
    'Indonesia':    'Indonesian',
    'Viet Nam':     'Vietnamese',
    'Vietnamemese': 'Vietnamese',
    'Sweden':       'Swedish',
    'No':           '',
    'In':           '',
    'None':         '',
    'A':            '',
}

def clean_languages():
    _log.start('Cleaning languages')
    n_cleaned = 0
    for profile in UserProfile.objects.all():
        dirty = False
        first_language = profile.first_language
        first_language = first_language.strip().title()
        if first_language in language_map:
            first_language = language_map[first_language]
        
        if first_language != profile.first_language:
            profile.first_language = first_language
            dirty = True
            
        if profile.second_languages is not None:
            second_languages = [l.strip().title() for l in
                profile.second_languages.strip().split(',')]
            second_languages = filter(None, second_languages)
            second_languages = [language_map.get(l, l) for l in \
                    second_languages]
            
            if second_languages:
                second_languages = ', '.join(second_languages)
            else:
                second_languages = None
            
            if second_languages != profile.second_languages:
                profile.second_languages = second_languages
                dirty = True
        
        if dirty:
            n_cleaned += 1
            profile.save()

    _log.finish('Cleaned %d profiles' % n_cleaned)

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options] email_address

Cleans the database by removing data for all users with the given email
address."""

    parser = optparse.OptionParser(usage)

    parser.add_option('--debug', action='store_true', dest='debug',
            default=False, help='Enables debugging mode [False]')
    
    parser.add_option('-e', action='store', dest='email',
            help='Clean user by email address')

    parser.add_option('-u', action='store', dest='username',
            help='Clean user by username')

    parser.add_option('-l', '--lang', action='store_true',
            dest='clean_languages',
            help='Clean reported languages')

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

    if options.email:
        clean_user_data(email=options.email)

    if options.username:
        clean_user_data(username=options.username)

    if options.clean_languages:
        clean_languages()
    
    return

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
