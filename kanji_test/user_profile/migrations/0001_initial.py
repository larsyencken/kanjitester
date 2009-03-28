# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from kanji_test.user_profile.models import *

class Migration:
    
    def forwards(self):
        
        
        # Mock Models
        User = db.mock_model(model_name='User', db_table='auth_user', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        Syllabus = db.mock_model(model_name='Syllabus', db_table='user_model_syllabus', db_tablespace='', pk_field_name='id', pk_field_type=models.AutoField, pk_field_args=[], pk_field_kwargs={})
        
        # Model 'UserProfile'
        db.create_table('user_profile_userprofile', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('user', models.ForeignKey(User, unique=True)),
            ('syllabus', models.ForeignKey(Syllabus)),
            ('first_language', models.CharField(max_length=100)),
            ('second_languages', models.CharField(max_length=200, null=True, blank=True)),
        ))
        
        db.send_create_signal('user_profile', ['UserProfile'])
    
    def backwards(self):
        db.delete_table('user_profile_userprofile')
        
