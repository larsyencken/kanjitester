# -*- coding: utf-8 -*-
#
#  add_missing_error_dist.py
#  kanji_test
#
#  Created by Lars Yencken on 2012-01-20.
#  Copyright 2012 Lars Yencken. All rights reserved.
#

"""
Find all users missing an error distribution, and regenerate it for them.
"""

import sys

from kanji_test.user_model import models
from django.core.exceptions import ObjectDoesNotExist

n_ok = 0
n_no_profile = 0
bad_users = []
for user in models.User.objects.all():
    try:
        syllabus = user.get_profile().syllabus
    except ObjectDoesNotExist:
        n_no_profile += 1
        continue

    if user.errordist_set.count() == 0:
        bad_users.append(user)
    else:
        n_ok += 1

print '%d ok' % n_ok
print '%d without profile' % n_no_profile
print '%d missing error dist' % len(bad_users)

print 
print 'Fixing bad profiles...'
for user in bad_users:
    sys.stdout.write(user.username + '... ')
    sys.stdout.flush()
    models.ErrorDist.init_from_priors(user)
    print 'ok'
