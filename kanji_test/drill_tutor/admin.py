# -*- coding: utf-8 -*-
# 
#  admin.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-22.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from django.contrib import admin

from kanji_test.drill_tutor import models

admin.site.register(models.UserProfile)
admin.site.register(models.PartialLexeme)
admin.site.register(models.PartialKanji)
admin.site.register(models.Syllabus)
admin.site.register(models.PriorDist)
admin.site.register(models.PriorPdf)
admin.site.register(models.ErrorDist)
admin.site.register(models.ErrorPdf)
