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

import sys, optparse
from consoleLog import default as _log
from consoleLog import withProgress
import simplejson

from kanji_test.user_profile import models as userprofile_models
from kanji_test.drill import models as drill_models
from django.contrib.auth.models import User 

EXCLUDE_EMAILS = (
        'lljy@csse.unimelb.edu.au',
        'tim@csse.unimelb.edu.au',
    )

def export_logs():
    _log.start('Dumping logs', nSteps=2)

    latest = drill_models.Response.objects.exclude(
                user__email__in=EXCLUDE_EMAILS
            ).order_by('-timestamp')[0].timestamp
    datestamp = '%s_%.02d_%.02d' % (latest.year, latest.month, latest.day)
    _dump_users('kanjitester_users_%s.json' % datestamp)
    _dump_responses('kanjitester_responses_%s.json' % datestamp)

    _log.finish()

def _dump_users(filename):
    _log.log(filename)
    with open(filename, 'w') as ostream:
        profiles = userprofile_models.UserProfile.objects.exclude(
                user__email__in=EXCLUDE_EMAILS).order_by('user__id')

        for user_profile in profiles:
            if user_profile.user.response_set.count() == 0:
                continue
            record = {
                        'user_id': user_profile.user.id,
                        'first_language': user_profile.first_language,
                        'second_languages': filter(None, [
                            l.strip().title() for l in \
                            user_profile.second_languages.split(',')
                        ]),
                        'syllabus': user_profile.syllabus.tag,
                    }
            print >> ostream, simplejson.dumps(record)
        
def _dump_responses(filename):
    _log.log(filename + ' ', newLine=False)
    with open(filename, 'w') as ostream:
        users = User.objects.exclude(email__in=EXCLUDE_EMAILS)
        for user in withProgress(users):
            for response in drill_models.MultipleChoiceResponse.objects.filter(
                    user=user):
                question = response.question
                test_set = drill_models.TestSet.objects.get(questions=question)
                record = {
                        'user_id': user.id,
                        'test_id': test_set.id,
                        'timestamp': response.timestamp.ctime(),
                        'pivot': question.pivot,
                        'pivot_type': question.pivot_type,
                        'question_type': question.question_type,
                        'is_adaptive': question.question_plugin.is_adaptive,
                        'distractors': [
                                o.value for o in \
                                question.multiplechoicequestion.options.all()
                            ],
                        'correct_response': question.multiplechoicequestion.options.get(is_correct=True).value,
                        'user_response': response.option.value,
                    }
                print >> ostream, simplejson.dumps(record)

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
