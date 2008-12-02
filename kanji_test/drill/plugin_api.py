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

from kanji_test.drill import models
from kanji_test.user_model import models as usermodel_models

class UnsupportedItem(Exception): pass

class QuestionFactoryI(object):
    """An abstract interface for factories which build questions."""
    @classmethod
    def get_question_plugin(cls):
        if not hasattr(cls, '_question_plugin'):
            if hasattr(cls, 'description'):
                description = cls.description
            elif hasattr(cls, '__doc__'):
                description = cls.__doc__.strip()
            else:
                description = ''

            cls._question_plugin = models.QuestionPlugin.objects.get_or_create(
                    name=cls.__name__,
                    description=description,
                    supports_kanji=cls.supports_kanji,
                    supports_words=cls.supports_words,
                    uses_dist=cls.uses_dist,
                    is_adaptive=cls.is_adaptive,
                )[0]
        return cls._question_plugin

    def get_question(self, syllabus_item, user):
        "Fetches a question based on the given syllabus item."
        if isinstance(syllabus_item, usermodel_models.PartialLexeme):
            return self.get_word_question(syllabus_item, user)

        elif isinstance(syllabus_item, usermodel_models.PartialKanji):
            return self.get_kanji_question(syllabus_item, user)

        else:
            raise ValueError('bad syllabus item %s' % syllabus_item)

    def supports_item(self, syllabus_item):
        if isinstance(syllabus_item, usermodel_models.PartialLexeme):
            return self.supports_words
        elif isinstance(syllabus_item, usermodel_models.PartialKanji):
            return self.supports_kanji
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
