# -*- coding: utf-8 -*-
# 
#  admin.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-26.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from django.contrib import admin

from kanji_test.user_model import models

class PartialLexemeAdmin(admin.ModelAdmin):
    list_display = ('lexeme',)
    list_filter = ('syllabus',)

class SenseNoteAdmin(admin.ModelAdmin):
    list_display = ('partial_lexeme', 'note')

class PartialKanjiAdmin(admin.ModelAdmin):
    list_display = ('kanji', 'syllabus')
    list_filter = ('syllabus',)

admin.site.register(models.UserProfile)
admin.site.register(models.PartialLexeme, PartialLexemeAdmin)
admin.site.register(models.PartialKanji, PartialKanjiAdmin)
admin.site.register(models.Syllabus)
admin.site.register(models.PriorDist)
admin.site.register(models.PriorPdf)
admin.site.register(models.ErrorDist)
admin.site.register(models.ErrorPdf)
admin.site.register(models.SenseNote, SenseNoteAdmin)
