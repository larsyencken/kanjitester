# -*- coding: utf-8 -*-
# 
#  admin.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-17.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from django.contrib import admin

from kanji_test.lexicon import models

class KanjiAdmin(admin.ModelAdmin):
    list_display = ('kanji', 'gloss',)
    search_fields = ('kanji', 'gloss')
admin.site.register(models.Kanji, KanjiAdmin)    

class KanjiReadingAdmin(admin.ModelAdmin):
    list_display = ('kanji', 'reading', 'reading_type')
    search_fields = ('kanji', 'reading')
    list_filter = ('reading_type',)
admin.site.register(models.KanjiReading, KanjiReadingAdmin)

admin.site.register(models.Lexeme)

class LexemeSurfaceAdmin(admin.ModelAdmin):
    list_display = ('lexeme', 'surface', 'priority_codes')
    search_fields = ('surface',)
    list_filter = ('has_kanji', 'in_lexicon')
admin.site.register(models.LexemeSurface, LexemeSurfaceAdmin)

class LexemeReadingAdmin(admin.ModelAdmin):
    list_display = ('lexeme', 'reading', 'priority_codes')
    search_fields = ('reading',)
admin.site.register(models.LexemeReading, LexemeReadingAdmin)

class LexemeSenseAdmin(admin.ModelAdmin):
    list_display = ('lexeme', 'gloss')
    search_fields = ('gloss',)
admin.site.register(models.LexemeSense, LexemeSenseAdmin)

#----------------------------------------------------------------------------#

class ProbAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'pdf', 'cdf')
    search_fields = ('symbol',)

class CondProbAdmin(admin.ModelAdmin):
    list_display = ('condition', 'symbol', 'pdf', 'cdf')
    search_fields = ('condition', 'symbol')

admin.site.register(models.KanjiProb, ProbAdmin)
admin.site.register(models.KanjiReadingProb, ProbAdmin)
admin.site.register(models.KanjiReadingCondProb, CondProbAdmin)

#----------------------------------------------------------------------------#
