# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

from django.db import models

class Lexeme(models.Model):
    """A single word or phrase."""

    class Admin:
        pass
        
    def __unicode__(self):
        return '/'.join(
                s.surface for s in self.surface_set.order_by('surface')
            ) + ' [%d]' % self.id
        
class LexemeSurface(models.Model):
    """A surface rendering of the word."""
    lexeme = models.ForeignKey(Lexeme, related_name='surface_set')
    surface = models.CharField(max_length=60, db_index=True, core=True)
    priority_codes = models.CharField(blank=True, max_length=60, null=True)
    
    class Admin:
        list_display = 'lexeme', 'surface', 'priority_codes'
        search_fields = 'surface',

class LexemeReading(models.Model):
    """A valid pronunciation for a lexeme."""
    lexeme = models.ForeignKey(Lexeme, related_name='reading_set')
    reading = models.CharField(max_length=30, db_index=True, core=True)
    priority_codes = models.CharField(blank=True, max_length=60, null=True)
    
    class Admin:
        list_display = 'lexeme', 'reading', 'priority_codes'
        search_fields = 'reading',
    
class Language(models.Model):
    """A human language."""
    code = models.CharField(max_length=10, primary_key=True)
    english_name = models.CharField(max_length=100, blank=True, null=True)
    native_name = models.CharField(max_length=100, blank=True, null=True)

    class Admin:
        list_display = ('code', 'english_name', 'native_name')
        search_fields = ('code', 'english_name', 'native_name')
    
    def __unicode__(self):
        return u"Language"

class LexemeSense(models.Model):
    """A word sense."""
    lexeme = models.ForeignKey(Lexeme, related_name='sense_set')
    language = models.ForeignKey(Language)
    gloss = models.CharField(max_length=300, core=True)

    class Admin:
        list_display = ('lexeme', 'language', 'gloss')
        search_fields = ('gloss',)

    def __unicode__(self):
        return u"LexemeSense"
