# -*- coding: utf-8 -*-
# 
#  clean_logs.py
#  kanji_test
#  
#  Created by Lars Yencken on 2009-04-06.
#  Copyright 2009 Lars Yencken. All rights reserved.
# 

"""
A command to clean usage logs.
"""

from django.core.management.base import NoArgsCommand

from kanji_test.analysis import clean_data

class Command(NoArgsCommand):
    help = "Cleans usage logs."
    requires_model_validation = True

    def handle_noargs(self, **options):
        clean_data.clean_all()
