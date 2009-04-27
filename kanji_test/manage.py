#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
#  manage.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

import sys
from cjktools.shell import set_screen_title

from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError:
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        set_screen_title('%s (manage.py)' % sys.argv[1])
    execute_manager(settings)
