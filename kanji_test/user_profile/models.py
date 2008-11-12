# -*- coding: utf-8 -*-
#
#  models.py
#  kanji_test
# 
#  Created by Lars Yencken on 13-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Models for the user_profile app.
"""

from django.db import models
from django.contrib.auth.models import User

from kanji_test.user_model.models import Syllabus

class UserProfile(models.Model):
    """Basic model of the user's kanji knowledge and study goals."""
    user = models.ForeignKey(User, unique=True)
    syllabus = models.ForeignKey(Syllabus)

    def __unicode__(self):
        return u"UserProfile for %s" % self.user.username

# vim: ts=4 sw=4 sts=4 et tw=78:
