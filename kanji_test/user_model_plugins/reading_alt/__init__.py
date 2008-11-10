# -*- coding: utf-8 -*-
#
#  __init__.py
#  reading_alt
# 
#  Created by Lars Yencken on 09-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
A django app for modelling kanji reading alternations.
"""

from checksum.models import Checksum

def build():
    import consoleLog
    from kanji_test.lexicon import models
    import reading_database

    log = consoleLog.default
    log.start('Building reading database', nSteps=2)
    log.log('Finding unique kanji')
    kanji_set = set(o['kanji'] for o in models.Kanji.objects.all().values(
            'kanji'))

    reading_database.ReadingDatabase.build(kanji_set)
    log.finish()

# vim: ts=4 sw=4 sts=4 et tw=78:
