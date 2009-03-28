# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from kanji_test.user_model.models import *

class Migration:
    
    def forwards(self):
        
        # Model 'Syllabus'
        db.create_table('user_model_syllabus', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tag', models.CharField(max_length=100, unique=True, help_text="A unique name for this syllabus.")),
        ))
        
        # Mock Models
        Syllabus = db.mock_model(model_name='Syllabus', db_table='user_model_syllabus', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        LexemeReading = db.mock_model(model_name='LexemeReading', db_table='lexicon_lexemereading', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        LexemeSurface = db.mock_model(model_name='LexemeSurface', db_table='lexicon_lexemesurface', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'Alignment'
        db.create_table('user_model_alignment', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('syllabus', models.ForeignKey(Syllabus)),
            ('reading', models.ForeignKey(lexicon_models.LexemeReading)),
            ('surface', models.ForeignKey(lexicon_models.LexemeSurface)),
            ('alignment', models.CharField(max_length=100)),
        ))
        db.create_index('user_model_alignment', ['syllabus_id','reading_id','surface_id','alignment'], unique=True, db_tablespace='')
        
        
        # Mock Models
        Syllabus = db.mock_model(model_name='Syllabus', db_table='user_model_syllabus', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        Lexeme = db.mock_model(model_name='Lexeme', db_table='lexicon_lexeme', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'PartialLexeme'
        db.create_table('user_model_partiallexeme', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('syllabus', models.ForeignKey(Syllabus)),
            ('lexeme', models.ForeignKey(lexicon_models.Lexeme, help_text="The word under consideration.")),
        ))
        # Mock Models
        PartialLexeme = db.mock_model(model_name='PartialLexeme', db_table='user_model_partiallexeme', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        LexemeReading = db.mock_model(model_name='LexemeReading', db_table='lexicon_lexemereading', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # M2M field 'PartialLexeme.reading_set'
        db.create_table('user_model_partiallexeme_reading_set', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('partiallexeme', models.ForeignKey(PartialLexeme, null=False)),
            ('lexemereading', models.ForeignKey(LexemeReading, null=False))
        )) 
        # Mock Models
        PartialLexeme = db.mock_model(model_name='PartialLexeme', db_table='user_model_partiallexeme', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        LexemeSense = db.mock_model(model_name='LexemeSense', db_table='lexicon_lexemesense', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # M2M field 'PartialLexeme.sense_set'
        db.create_table('user_model_partiallexeme_sense_set', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('partiallexeme', models.ForeignKey(PartialLexeme, null=False)),
            ('lexemesense', models.ForeignKey(LexemeSense, null=False))
        )) 
        # Mock Models
        PartialLexeme = db.mock_model(model_name='PartialLexeme', db_table='user_model_partiallexeme', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        LexemeSurface = db.mock_model(model_name='LexemeSurface', db_table='lexicon_lexemesurface', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # M2M field 'PartialLexeme.surface_set'
        db.create_table('user_model_partiallexeme_surface_set', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('partiallexeme', models.ForeignKey(PartialLexeme, null=False)),
            ('lexemesurface', models.ForeignKey(LexemeSurface, null=False))
        )) 
        db.create_index('user_model_partiallexeme', ['syllabus_id','lexeme_id'], unique=True, db_tablespace='')
        
        
        # Mock Models
        PartialLexeme = db.mock_model(model_name='PartialLexeme', db_table='user_model_partiallexeme', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'SenseNote'
        db.create_table('user_model_sensenote', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('partial_lexeme', models.ForeignKey(PartialLexeme)),
            ('note', models.CharField(max_length=300)),
        ))
        
        # Mock Models
        Syllabus = db.mock_model(model_name='Syllabus', db_table='user_model_syllabus', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        Kanji = db.mock_model(model_name='Kanji', db_table='lexicon_kanji', db_tablespace='', pk_field_name='kanji', pk_field_type=models.CharField, pk_field_args=[], pk_field_kwargs={'max_length': 3})
        
        # Model 'PartialKanji'
        db.create_table('user_model_partialkanji', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('syllabus', models.ForeignKey(Syllabus)),
            ('kanji', models.ForeignKey(lexicon_models.Kanji, help_text='The kanji itself.')),
        ))
        # Mock Models
        PartialKanji = db.mock_model(model_name='PartialKanji', db_table='user_model_partialkanji', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        KanjiReading = db.mock_model(model_name='KanjiReading', db_table='lexicon_kanjireading', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # M2M field 'PartialKanji.reading_set'
        db.create_table('user_model_partialkanji_reading_set', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('partialkanji', models.ForeignKey(PartialKanji, null=False)),
            ('kanjireading', models.ForeignKey(KanjiReading, null=False))
        )) 
        db.create_index('user_model_partialkanji', ['syllabus_id','kanji_id'], unique=True, db_tablespace='')
        
        
        # Mock Models
        Syllabus = db.mock_model(model_name='Syllabus', db_table='user_model_syllabus', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'PriorDist'
        db.create_table('user_model_priordist', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('syllabus', models.ForeignKey(Syllabus)),
            ('tag', models.CharField(max_length=100)),
        ))
        db.create_index('user_model_priordist', ['syllabus_id','tag'], unique=True, db_tablespace='')
        
        
        # Mock Models
        PriorDist = db.mock_model(model_name='PriorDist', db_table='user_model_priordist', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'PriorPdf'
        db.create_table('user_model_priorpdf', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pdf', models.FloatField()),
            ('cdf', models.FloatField()),
            ('condition', models.CharField(max_length=50, db_index=True)),
            ('symbol', models.CharField(max_length=50, db_index=True)),
            ('dist', models.ForeignKey(PriorDist, related_name='density')),
        ))
        db.create_index('user_model_priorpdf', ['dist_id','condition','symbol'], unique=True, db_tablespace='')
        
        
        # Mock Models
        User = db.mock_model(model_name='User', db_table='auth_user', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'ErrorDist'
        db.create_table('user_model_errordist', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(User)),
            ('tag', models.CharField(max_length=100)),
        ))
        db.create_index('user_model_errordist', ['user_id','tag'], unique=True, db_tablespace='')
        
        
        # Mock Models
        ErrorDist = db.mock_model(model_name='ErrorDist', db_table='user_model_errordist', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'ErrorPdf'
        db.create_table('user_model_errorpdf', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pdf', models.FloatField()),
            ('cdf', models.FloatField()),
            ('condition', models.CharField(max_length=50, db_index=True)),
            ('symbol', models.CharField(max_length=50, db_index=True)),
            ('dist', models.ForeignKey(ErrorDist, related_name='density')),
        ))
        db.create_index('user_model_errorpdf', ['dist_id','condition','symbol'], unique=True, db_tablespace='')
        
        
        db.send_create_signal('user_model', ['Syllabus','Alignment','PartialLexeme','SenseNote','PartialKanji','PriorDist','PriorPdf','ErrorDist','ErrorPdf'])
    
    def backwards(self):
        db.delete_table('user_model_errorpdf')
        db.delete_table('user_model_errordist')
        db.delete_table('user_model_priorpdf')
        db.delete_table('user_model_priordist')
        db.delete_table('user_model_partialkanji_reading_set')
        db.delete_table('user_model_partialkanji')
        db.delete_table('user_model_sensenote')
        db.delete_table('user_model_partiallexeme_surface_set')
        db.delete_table('user_model_partiallexeme_sense_set')
        db.delete_table('user_model_partiallexeme_reading_set')
        db.delete_table('user_model_partiallexeme')
        db.delete_table('user_model_alignment')
        db.delete_table('user_model_syllabus')
        
