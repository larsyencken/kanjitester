#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  export_logs.py
#  kanji_test
# 
#  Created by Lars Yencken on 28-12-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

from __future__ import with_statement

import os, sys, optparse
import datetime
import itertools
from xml.etree.ElementTree import Element, SubElement, tostring 
from consoleLog import default as _log
from consoleLog import withProgress

from kanji_test.user_profile import models as userprofile_models
from kanji_test.drill import models as drill_models

EXCLUDE_EMAILS = (
        'lljy@csse.unimelb.edu.au',
    )

def export_logs():
    _log.start('Dumping logs', nSteps=2)

    _log.start('Sanitizing logs', nSteps=2)
    root = Element('kanji-test-log')
    user_ids = add_user_info(root)
    earliest, latest = add_questions_and_responses(root, user_ids)
    _log.finish()

    filename = 'kanji_test_logs_%s_%s_%s.xml' % (latest.year, latest.month,
            latest.day)
    _log.log('Writing to %s' % filename)
    with open(filename, 'w') as ostream:
        ostream.write(tostring(root, 'UTF-8'))
    _log.finish()

def add_user_info(root):
    user_ids = []
    user_info = SubElement(root, 'user-info')
    profiles = list(userprofile_models.UserProfile.objects.exclude(
            user__email__in=EXCLUDE_EMAILS))
    profiles.sort(key=lambda u: u.user.email)

    profiles = [(u, list(p)) for (u, p) in itertools.groupby(profiles,
            lambda x: x.user.id)]
    _log.log('Listing users ', newLine=False)
    for user_id, user_profiles in withProgress(profiles):
        profile = max(user_profiles, key=lambda x: x.id)
        syllabi = ','.join(p.syllabus.tag for p in user_profiles)
        user = SubElement(user_info, 'user', {'id': str(int(user_id))})
        user.attrib['first-language'] = profile.first_language
        if profile.second_languages:
            second_languages = profile.second_languages.split(',')
            second_languages = [l.strip() for l in second_languages]
            user.attrib['second-languages'] = ','.join(second_languages)
        user.attrib['syllabus'] = profile.syllabus.tag

        user_ids.append(profile.user_id)

    return user_ids

def add_questions_and_responses(root, user_ids):
    responses = SubElement(root, 'responses')
    _log.log('Analysing responses ', newLine=False)
    earliest = datetime.datetime.now()
    latest = datetime.datetime.now() - datetime.timedelta(365 * 20)
    for user_id in withProgress(user_ids):
        for response in drill_models.MultipleChoiceResponse.objects.filter(
                user__id=user_id):
            r = SubElement(root, 'response')
            r.attrib['user-id'] = str(int(user_id))
            r.attrib['timestamp'] = response.timestamp.ctime()
            earliest = min(response.timestamp, earliest)
            latest = max(response.timestamp, latest)
            question = response.question
            q = SubElement(r, 'question')
            q.attrib['type'] = question.question_type
            q.attrib['plugin'] = question.question_plugin.name
            q.attrib['adaptive'] = str(question.question_plugin.is_adaptive)

            for option in question.multiplechoicequestion.options.all():
                o = SubElement(q, 'option', {'value': option.value})
                if option.is_correct:
                    o.attrib['is-correct'] = '1'
                if option == response.option:
                    o.attrib['chosen'] = '1'

    return (earliest, latest)

#----------------------------------------------------------------------------#

def _create_option_parser():
    usage = \
"""%prog [options]

Dumps sanitized user logs."""

    parser = optparse.OptionParser(usage)

    return parser

def main(argv):
    parser = _create_option_parser()
    (options, args) = parser.parse_args(argv)

    if args:
        parser.print_help()
        sys.exit(1)

    export_logs()

#----------------------------------------------------------------------------#

if __name__ == '__main__':
    main(sys.argv[1:])

# vim: ts=4 sw=4 sts=4 et tw=78:
