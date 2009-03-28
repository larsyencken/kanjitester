# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from kanji_test.drill.models import *

class Migration:
    
    def forwards(self):
        
        # Model 'QuestionPlugin'
        db.create_table('drill_questionplugin', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('name', models.CharField(max_length=100, unique=True)),
            ('description', models.TextField()),
            ('uses_dist', models.CharField(max_length=100, null=True, blank=True)),
            ('is_adaptive', models.BooleanField()),
        ))
        
        # Mock Models
        QuestionPlugin = db.mock_model(model_name='QuestionPlugin', db_table='drill_questionplugin', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'Question'
        db.create_table('drill_question', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('pivot', models.CharField(max_length=30, db_index=True, help_text="The word or kanji this question is created for.")),
            ('pivot_id', models.IntegerField( help_text="The id of the pivot PartialKanji or PartialLexeme.")),
            ('pivot_type', models.CharField(max_length=1, choices=PIVOT_TYPES, help_text="Is this a word or a kanji question?")),
            ('question_type', models.CharField(max_length=2, choices=QUESTION_TYPES, help_text="The broad type of this question.")),
            ('question_plugin', models.ForeignKey(QuestionPlugin, help_text="The plugin which generated this question.")),
            ('annotation', models.CharField(max_length=100, null=True, blank=True, help_text="Scratch space for question plugin annotations.")),
        ))
        
        # Mock Models
        Question = db.mock_model(model_name='Question', db_table='drill_question', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'MultipleChoiceQuestion'
        db.create_table('drill_multiplechoicequestion', (
            ('question_ptr', models.OneToOneField(Question)),
            ('stimulus', models.CharField(max_length=400)),
        ))
        
        # Mock Models
        Question = db.mock_model(model_name='Question', db_table='drill_question', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        MultipleChoiceQuestion = db.mock_model(model_name='MultipleChoiceQuestion', db_table='drill_multiplechoicequestion', db_tablespace='', pk_field_name='question_ptr', pk_field_type=models.OneToOneField, pk_field_args=[Question], pk_field_kwargs={})
        
        # Model 'MultipleChoiceOption'
        db.create_table('drill_multiplechoiceoption', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(MultipleChoiceQuestion, related_name='options')),
            ('value', models.CharField(max_length=200)),
            ('is_correct', models.BooleanField(default=False)),
            ('annotation', models.CharField(max_length=100, null=True, blank=True)),
        ))
        db.create_index('drill_multiplechoiceoption', ['question_id','value'], unique=True, db_tablespace='')
        
        
        # Mock Models
        Question = db.mock_model(model_name='Question', db_table='drill_question', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        User = db.mock_model(model_name='User', db_table='auth_user', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'Response'
        db.create_table('drill_response', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(Question)),
            ('user', models.ForeignKey(auth_models.User)),
            ('timestamp', models.DateTimeField(auto_now_add=True)),
        ))
        db.create_index('drill_response', ['question_id','user_id','timestamp'], unique=True, db_tablespace='')
        
        
        # Mock Models
        Response = db.mock_model(model_name='Response', db_table='drill_response', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        MultipleChoiceOption = db.mock_model(model_name='MultipleChoiceOption', db_table='drill_multiplechoiceoption', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'MultipleChoiceResponse'
        db.create_table('drill_multiplechoiceresponse', (
            ('response_ptr', models.OneToOneField(Response)),
            ('option', models.ForeignKey(MultipleChoiceOption)),
        ))
        
        # Mock Models
        User = db.mock_model(model_name='User', db_table='auth_user', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'TestSet'
        db.create_table('drill_testset', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(auth_models.User)),
            ('random_seed', models.IntegerField()),
            ('start_time', models.DateTimeField(auto_now_add=True)),
            ('end_time', models.DateTimeField(blank=True, null=True)),
            ('set_type', models.CharField(max_length=1, choices=( ('c', 'control'), ('a', 'adaptive'), ))),
        ))
        # Mock Models
        TestSet = db.mock_model(model_name='TestSet', db_table='drill_testset', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        Question = db.mock_model(model_name='Question', db_table='drill_question', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        MultipleChoiceQuestion = db.mock_model(model_name='MultipleChoiceQuestion', db_table='drill_multiplechoicequestion', db_tablespace='', pk_field_name='question_ptr', pk_field_type=models.OneToOneField, pk_field_args=[Question], pk_field_kwargs={})
        
        # M2M field 'TestSet.questions'
        db.create_table('drill_testset_questions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('testset', models.ForeignKey(TestSet, null=False)),
            ('multiplechoicequestion', models.ForeignKey(MultipleChoiceQuestion, null=False))
        )) 
        # Mock Models
        TestSet = db.mock_model(model_name='TestSet', db_table='drill_testset', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        Response = db.mock_model(model_name='Response', db_table='drill_response', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        MultipleChoiceResponse = db.mock_model(model_name='MultipleChoiceResponse', db_table='drill_multiplechoiceresponse', db_tablespace='', pk_field_name='response_ptr', pk_field_type=models.OneToOneField, pk_field_args=[Response], pk_field_kwargs={})
        
        # M2M field 'TestSet.responses'
        db.create_table('drill_testset_responses', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('testset', models.ForeignKey(TestSet, null=False)),
            ('multiplechoiceresponse', models.ForeignKey(MultipleChoiceResponse, null=False))
        )) 
        
        db.send_create_signal('drill', ['QuestionPlugin','Question','MultipleChoiceQuestion','MultipleChoiceOption','Response','MultipleChoiceResponse','TestSet'])
    
    def backwards(self):
        db.delete_table('drill_testset_responses')
        db.delete_table('drill_testset_questions')
        db.delete_table('drill_testset')
        db.delete_table('drill_multiplechoiceresponse')
        db.delete_table('drill_response')
        db.delete_table('drill_multiplechoiceoption')
        db.delete_table('drill_multiplechoicequestion')
        db.delete_table('drill_question')
        db.delete_table('drill_questionplugin')
        
