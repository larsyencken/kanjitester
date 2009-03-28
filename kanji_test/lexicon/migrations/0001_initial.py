# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from kanji_test.lexicon.models import *

class Migration:
    
    def forwards(self):
        
        # Model 'Lexeme'
        db.create_table('lexicon_lexeme', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
        ))
        
        # Mock Models
        Lexeme = db.mock_model(model_name='Lexeme', db_table='lexicon_lexeme', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'LexemeSurface'
        db.create_table('lexicon_lexemesurface', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('lexeme', models.ForeignKey(Lexeme, related_name='surface_set')),
            ('surface', models.CharField(max_length=60, db_index=True)),
            ('priority_codes', models.CharField(blank=True, max_length=60, null=True, help_text='Any annotations the original dictionary provided')),
            ('has_kanji', models.BooleanField( help_text='Does this entry contain any kanji characters?')),
            ('in_lexicon', models.BooleanField(default=True, help_text='Is this part of the original lexicon?')),
        ))
        db.create_index('lexicon_lexemesurface', ['lexeme_id','surface'], unique=True, db_tablespace='')
        
        
        # Mock Models
        Lexeme = db.mock_model(model_name='Lexeme', db_table='lexicon_lexeme', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'LexemeReading'
        db.create_table('lexicon_lexemereading', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('lexeme', models.ForeignKey(Lexeme, related_name='reading_set')),
            ('reading', models.CharField(max_length=60, db_index=True)),
            ('priority_codes', models.CharField(blank=True, max_length=60, null=True)),
        ))
        db.create_index('lexicon_lexemereading', ['lexeme_id','reading'], unique=True, db_tablespace='')
        
        
        # Mock Models
        Lexeme = db.mock_model(model_name='Lexeme', db_table='lexicon_lexeme', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'LexemeSense'
        db.create_table('lexicon_lexemesense', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('lexeme', models.ForeignKey(Lexeme, related_name='sense_set')),
            ('gloss', models.CharField(max_length=500)),
            ('is_first_sense', models.BooleanField()),
        ))
        # Model 'KanjiProb'
        db.create_table('lexicon_kanjiprob', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pdf', models.FloatField()),
            ('cdf', models.FloatField()),
            ('symbol', models.CharField(max_length=50, db_index=True, unique=True)),
        ))
        # Model 'KanjiReadingProb'
        db.create_table('lexicon_kanjireadingprob', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pdf', models.FloatField()),
            ('cdf', models.FloatField()),
            ('symbol', models.CharField(max_length=50, db_index=True, unique=True)),
        ))
        # Model 'KanjiReadingCondProb'
        db.create_table('lexicon_kanjireadingcondprob', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pdf', models.FloatField()),
            ('cdf', models.FloatField()),
            ('condition', models.CharField(max_length=50, db_index=True)),
            ('symbol', models.CharField(max_length=50, db_index=True)),
        ))
        db.create_index('lexicon_kanjireadingcondprob', ['condition','symbol'], unique=True, db_tablespace='')
        
        # Model 'LexemeSurfaceProb'
        db.create_table('lexicon_lexemesurfaceprob', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pdf', models.FloatField()),
            ('cdf', models.FloatField()),
            ('symbol', models.CharField(max_length=50, db_index=True, unique=True)),
        ))
        # Model 'LexemeReadingProb'
        db.create_table('lexicon_lexemereadingprob', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pdf', models.FloatField()),
            ('cdf', models.FloatField()),
            ('condition', models.CharField(max_length=50, db_index=True)),
            ('symbol', models.CharField(max_length=50, db_index=True)),
        ))
        db.create_index('lexicon_lexemereadingprob', ['condition','symbol'], unique=True, db_tablespace='')
        
        # Model 'Kanji'
        db.create_table('lexicon_kanji', (
            ('kanji', models.CharField(max_length=3, primary_key=True)),
            ('gloss', models.CharField(max_length=200)),
        ))
        
        # Mock Models
        Kanji = db.mock_model(model_name='Kanji', db_table='lexicon_kanji', db_tablespace='', pk_field_name='kanji', pk_field_type=models.CharField, pk_field_args=[], pk_field_kwargs={'max_length': 3})
        
        # Model 'KanjiReading'
        READING_TYPES = (('o', 'on'), ('k', 'kun'))
        db.create_table('lexicon_kanjireading', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('kanji', models.ForeignKey(Kanji, related_name='reading_set')),
            ('reading', models.CharField(max_length=21, db_index=True)),
            ('reading_type', models.CharField(max_length=1, choices=READING_TYPES)),
        ))
        db.create_index('lexicon_kanjireading', ['reading','kanji_id','reading_type'], unique=True, db_tablespace='')
        
        
        db.send_create_signal('lexicon', ['Lexeme','LexemeSurface','LexemeReading','LexemeSense','KanjiProb','KanjiReadingProb','KanjiReadingCondProb','LexemeSurfaceProb','LexemeReadingProb','Kanji','KanjiReading'])
    
    def backwards(self):
        db.delete_table('lexicon_kanjireading')
        db.delete_table('lexicon_kanji')
        db.delete_table('lexicon_lexemereadingprob')
        db.delete_table('lexicon_lexemesurfaceprob')
        db.delete_table('lexicon_kanjireadingcondprob')
        db.delete_table('lexicon_kanjireadingprob')
        db.delete_table('lexicon_kanjiprob')
        db.delete_table('lexicon_lexemesense')
        db.delete_table('lexicon_lexemereading')
        db.delete_table('lexicon_lexemesurface')
        db.delete_table('lexicon_lexeme')
        
