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

from django.core.management.base import NoArgsCommand
import consoleLog

from kanji_test.lexicon import load_lexicon
from kanji_test.user_model_plugins.visual_similarity import load_neighbours

class Command(NoArgsCommand):
    help = "Builds all required static database tables."
    requires_model_validation = True

    def handle_noargs(self, **options):
        consoleLog.default.start('Building kanji_test', nSteps=2)
        load_lexicon.load_lexicon()

        load_neighbours.load_neighbours()
        consoleLog.default.finish()

# vim: ts=4 sw=4 sts=4 et tw=78:
