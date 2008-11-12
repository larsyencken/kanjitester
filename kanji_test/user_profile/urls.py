# -*- coding: utf-8 -*-
#
#  urls.py
#  kanji_test
# 
#  Created by Lars Yencken on 13-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

from django.conf.urls.defaults import *

urlpatterns = patterns('kanji_test.user_profile.views',
    url(r'^$', 'create_profile', name='userprofile_profile'),
)

# vim: ts=4 sw=4 sts=4 et tw=78:

