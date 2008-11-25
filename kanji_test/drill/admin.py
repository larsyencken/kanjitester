# -*- coding: utf-8 -*-
# 
#  admin.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-30.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from django.contrib import admin

from kanji_test.drill import models
from kanji_test import settings

class OptionInline(admin.StackedInline):
    model = models.MultipleChoiceOption
    extra = 1

class MultipleChoiceAdmin(admin.ModelAdmin):
    list_display = ('pivot', 'pivot_type', 'pivot_id', 'question_type',
            'question_plugin', 'annotation')
    list_filter = ('pivot_type', 'question_type')
    search_fields = ('pivot',)
    inlines = [OptionInline]

admin.site.register(models.MultipleChoiceQuestion, MultipleChoiceAdmin)

class QuestionPluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'supports_kanji', 'supports_words')
    list_filter = ('supports_kanji', 'supports_words')

admin.site.register(models.QuestionPlugin, QuestionPluginAdmin)

class MultipleChoiceResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'option', 'timestamp')
    list_filter = ('timestamp',)

admin.site.register(models.MultipleChoiceResponse, MultipleChoiceResponseAdmin)

class MultipleChoiceOptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'value', 'annotation', 'is_correct')
    list_filter = ('is_correct',)

admin.site.register(models.MultipleChoiceOption, MultipleChoiceOptionAdmin)

class TestSetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'accuracy', 'start_time', 'end_time',
            'set_type')
    list_filter = ('end_time', 'set_type')

admin.site.register(models.TestSet, TestSetAdmin)

