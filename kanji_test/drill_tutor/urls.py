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
    url(r'^$', 'index', name='drill_tutor_dashboard'),
    url(r'^test_factories/$', 'test_factories', name="drill_tutor_test"),
    url(r'^check/$', 'test_answer_checking', name='drill_tutor_answers'),
)