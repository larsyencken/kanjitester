# -*- coding: utf-8 -*-
# 
#  context_processors.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-23.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from kanji_test import settings

def basic_vars(request):
    """Provides some basic variables for the request."""
    return {
        'media_url':        settings.MEDIA_URL,
        'admin_media_url':  settings.ADMIN_MEDIA_PREFIX,
    }
