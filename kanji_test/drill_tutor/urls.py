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
    url(r'^$', 'dashboard', name='drilltutor_dashboard'),
    url(r'^welcome/$', 'welcome', name='drilltutor_welcome'),
    url(r'^test/$', 'test_factories', name="drilltutor_test"),
    url(r'^check/$', 'test_answer_checking', name='drilltutor_answers'),
)
