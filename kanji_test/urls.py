# -*- coding: utf-8 -*-
# 
#  urls.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

from django.conf.urls.defaults import *
from django.contrib import admin

import settings

admin.autodiscover()

base_patterns = ('',
        (r'^admin/(.*)', admin.site.root),
        (r'^accounts/', include('registration.urls')),
    )

# Optional media view for debugging and testing.
if not settings.DEPLOYED:
    base_patterns += (
            url(r'^media/', 'views.media', name='media'),
        )

# Add the default pages.
base_patterns += (
        (r'', include('drill_tutor.urls')),
    )

urlpatterns = patterns(*base_patterns)
