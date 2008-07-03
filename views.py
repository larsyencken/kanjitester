# -*- coding: utf-8 -*-
# 
#  views.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-07-03.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import django.views.static

import settings

def media(request):
    "A static view which renders media. Not to be used in deployment."
    return django.views.static.serve(
            request,
            request.path[len(settings.MEDIA_URL):],
            document_root=settings.MEDIA_ROOT,
        )