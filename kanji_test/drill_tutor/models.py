# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    """Basic model of the user's kanji knowledge and study goals."""
    user = models.ForeignKey(User, unique=True)

    class Admin:
        list_display = ('',)
        search_fields = ('',)

    def __unicode__(self):
        return u"UserProfile"
