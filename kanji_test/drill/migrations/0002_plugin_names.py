# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from kanji_test.drill.models import *
from kanji_test.drill import load_plugins

class Migration:
    
    def forwards(self, orm):
        "Write your forwards migration here"
        renames = {}
        for plugin in load_plugins():
            old_name = str(plugin.__class__.__name__)
            renames[old_name] = plugin.verbose_name

        for question_plugin in QuestionPlugin.objects.all():
            if question_plugin.name in renames:
                new_name = renames[question_plugin.name]
                print "%s -> %s" % (question_plugin.name, new_name)
                try:
                    existing_rename = QuestionPlugin.objects.get(name=new_name)
                    question_plugin.question_set.update(
                            question_plugin=existing_rename)
                    question_plugin.delete()
                except ObjectDoesNotExist:
                    question_plugin.name = new_name
                    question_plugin.save()
    
    def backwards(self, orm):
        "Write your backwards migration here"
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'drill.multiplechoiceoption': {
            'Meta': {'unique_together': "(('question', 'value'),)"},
            'annotation': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_correct': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': "orm['drill.MultipleChoiceQuestion']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'drill.multiplechoicequestion': {
            'question_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['drill.Question']", 'unique': 'True', 'primary_key': 'True'}),
            'stimulus': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        },
        'drill.multiplechoiceresponse': {
            'option': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['drill.MultipleChoiceOption']"}),
            'response_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['drill.Response']", 'unique': 'True', 'primary_key': 'True'})
        },
        'drill.question': {
            'annotation': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pivot': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'pivot_id': ('django.db.models.fields.IntegerField', [], {}),
            'pivot_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'question_plugin': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['drill.QuestionPlugin']"}),
            'question_type': ('django.db.models.fields.CharField', [], {'max_length': '2'})
        },
        'drill.questionplugin': {
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_adaptive': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'uses_dist': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'drill.response': {
            'Meta': {'unique_together': "(('question', 'user', 'timestamp'),)"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['drill.Question']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'drill.testset': {
            'end_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'questions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['drill.MultipleChoiceQuestion']"}),
            'random_seed': ('django.db.models.fields.IntegerField', [], {}),
            'responses': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['drill.MultipleChoiceResponse']"}),
            'set_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'start_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }
    
    complete_apps = ['drill']
