# -*- coding: utf-8 -*-
#
#  urls.py
#  kanji_test
# 
#  Created by Lars Yencken on 25-02-2009.
#  Copyright 2009 Lars Yencken. All rights reserved.
#

from django.conf.urls.defaults import *

urlpatterns = patterns('kanji_test.analysis.views',
    url('^$', 'analysis_home', name='analysis_home'),
)

# vim: ts=4 sw=4 sts=4 et tw=78:

