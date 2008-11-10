# -*- coding: utf-8 -*-
#
#  build.py
#  kanji_test
# 
#  Created by Lars Yencken on 18-09-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
A command to run the build method of all apps.
"""

from os import path 

from django.core.management.base import NoArgsCommand
from django.conf import settings 
import consoleLog

from kanji_test.lexicon import load_lexicon
from kanji_test.user_model import plugin_api
from kanji_test.user_model import add_syllabus

_log = consoleLog.default

class Command(NoArgsCommand):
    help = "Builds all required static database tables."
    requires_model_validation = True

    def handle_noargs(self, **options):
        apps_with_build = []
        for app_path in settings.INSTALLED_APPS:
            base_module = __import__(app_path)
            app_module = reduce(getattr, app_path.split('.')[1:], base_module)
            if hasattr(app_module, 'build'):
                apps_with_build.append((app_path, app_module))

        _log.start('Building kanji_test', nSteps=len(apps_with_build))
        for app_path, app_module in apps_with_build:
            app_module.build()
        _log.finish()

# vim: ts=4 sw=4 sts=4 et tw=78:
