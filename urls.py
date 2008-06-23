# -*- coding: utf-8 -*-
# 
#  urls.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    # (r'^kanji_test/', include('kanji_test.foo.urls')),

    (r'^admin/', include('django.contrib.admin.urls')),
)
