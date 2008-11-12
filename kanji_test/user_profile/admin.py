# -*- coding: utf-8 -*-
#
#  admin.py
#  kanji_test
# 
#  Created by Lars Yencken on 13-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

from django.contrib import admin

from kanji_test.user_profile import models

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'syllabus')

admin.site.register(models.UserProfile, UserProfileAdmin)

# vim: ts=4 sw=4 sts=4 et tw=78:

