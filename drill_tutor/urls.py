# -*- coding: utf-8 -*-
# 
#  urls.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-23.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from django.conf.urls.defaults import *

urlpatterns = patterns('drill_tutor.views',
    url(r'^test_factories/$', 'test_factories', name="drill_tutor_test"),
    url(r'^$', 'test_factories', name='drill_tutor_home'),
)