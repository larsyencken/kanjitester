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
    list_display = ('lexeme', 'syllabus')
    list_filter = ('syllabus',)
    search_fields = ('lexeme__reading_set__reading',
            'lexeme__surface_set__surface')

class AlignmentAdmin(admin.ModelAdmin):
    list_display = ('syllabus', 'surface', 'reading', 'alignment')
    list_filter = ('syllabus',)
    search_fields = ('reading__reading', 'surface__surface')
admin.site.register(models.Alignment, AlignmentAdmin)

class SenseNoteAdmin(admin.ModelAdmin):
    list_display = ('partial_lexeme', 'note')

class PartialKanjiAdmin(admin.ModelAdmin):
    list_display = ('kanji', 'syllabus', 'n_readings')
    list_filter = ('syllabus',)

class PriorDistAdmin(admin.ModelAdmin):
    list_display = ('syllabus', 'tag')
    list_filter = ('syllabus',)

class PriorPdfAdmin(admin.ModelAdmin):
    list_display = ('dist', 'condition', 'symbol', 'pdf', 'cdf')
    list_filter = ('dist',)
    search_fields = ('condition',)

class ErrorPdfAdmin(admin.ModelAdmin):
    list_display = ('dist', 'condition', 'symbol', 'pdf', 'cdf')
    search_fields = ('dist__user__username',)

class ErrorDistAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag')
    list_filter = ('tag',)
    search_fields = ('user__username',)

admin.site.register(models.PartialLexeme, PartialLexemeAdmin)
admin.site.register(models.PartialKanji, PartialKanjiAdmin)
admin.site.register(models.Syllabus)
admin.site.register(models.PriorDist, PriorDistAdmin)
admin.site.register(models.PriorPdf, PriorPdfAdmin)
admin.site.register(models.ErrorDist, ErrorDistAdmin)
admin.site.register(models.ErrorPdf, ErrorPdfAdmin)
admin.site.register(models.SenseNote, SenseNoteAdmin)

