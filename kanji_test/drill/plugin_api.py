# -*- coding: utf-8 -*-
# 
#  factory.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-29.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

"The basic api for generating questions."

from cjktools.exceptions import NotYetImplementedError
from cjktools import scripts
from django.core.exceptions import ObjectDoesNotExist

from kanji_test.drill import models
from kanji_test.user_model import models as usermodel_models

class UnsupportedItem(Exception): pass

class QuestionFactoryI(object):
    """An abstract interface for factories which build questions."""
    @classmethod
    def get_question_plugin(cls):
        if hasattr(cls, '_question_plugin'):
            return cls._question_plugin

        try:
            obj = models.QuestionPlugin.objects.get(name=cls.get_name())
            cls._update_existing(obj)
        except ObjectDoesNotExist:
            obj = models.QuestionPlugin(
                    name=cls.get_name(),
                    description=cls.get_description(),
                    uses_dist=cls.uses_dist,
                    is_adaptive=cls.is_adaptive,
                )
            obj.save()

        cls._question_plugin = obj
        return cls._question_plugin

    @classmethod
    def get_description(cls):
        if hasattr(cls, 'description'):
            return cls.description
        elif hasattr(cls, '__doc__'):
            return cls.__doc__.strip()
        else:
            return ''

    @classmethod
    def get_name(cls):
        if hasattr(cls, 'verbose_name'):
            return cls.verbose_name
        return cls.__name__

    @classmethod
    def _update_existing(cls, obj):
        "Updates all fields of this plugin object."
        dirty = False
        description = cls.get_description()
        if obj.description != description:
            obj.description = description
            dirty = True

        if obj.is_adaptive != cls.is_adaptive:
            obj.is_adaptive = cls.is_adaptive
            dirty = True

        if obj.uses_dist != cls.uses_dist:
            obj.uses_dist = cls.uses_dist
            dirty = True

        if dirty:
            obj.save()
        return

    def get_question(self, syllabus_item, user):
        "Fetches a question based on the given syllabus item."
        if isinstance(syllabus_item, usermodel_models.PartialLexeme):
            return self.get_word_question(syllabus_item, user)

        elif isinstance(syllabus_item, usermodel_models.PartialKanji):
            return self.get_kanji_question(syllabus_item, user)

        else:
            raise ValueError('bad syllabus item %s' % syllabus_item)

    def get_word_question(self, partial_lexeme, user):
        """Constructs and returns a new question based on the given word."""
        raise NotYetImplementedError

    def get_kanji_question(self, partial_kanji, user):
        """Constructs and returns a new question based on the given kanji."""
        raise NotYetImplementedError

class MultipleChoiceFactoryI(QuestionFactoryI):
    """An abstract factory for multiple choice questions."""
    @classmethod
    def build_question(cls, **kwargs):
        kwargs.setdefault('question_type', cls.question_type)
        kwargs.setdefault('question_plugin', cls.get_question_plugin())
        question = models.MultipleChoiceQuestion(**kwargs)
        question.save()
        return question
