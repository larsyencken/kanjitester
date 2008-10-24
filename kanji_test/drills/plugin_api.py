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

from kanji_test.plugins.api import models

class QuestionFactoryI(object):
    """An abstract interface for factories which build questions."""
    @classmethod
    def get_question_plugin(cls):
        if not hasattr(cls, '_question_plugin'):
            cls._question_plugin = models.QuestionPlugin.objects.get_or_create(
                    name=cls.__name__,
                    description=(
                            hasattr(cls, '__doc__')
                                and cls.__doc__.strip()
                                or ''
                        ),
                    supports_kanji=cls.supports_kanji,
                    supports_words=cls.supports_words,
                )[0]
        return cls._question_plugin
        
    def get_word_question(self, word):
        """Constructs and returns a new question based on the given word."""
        raise NotYetImplementedError

    def get_kanji_question(self, kanji):
        """Constructs and returns a new question based on the given kanji."""
        raise NotYetImplementedError

    def is_valid_word(self, word):
        return isinstance(word, (unicode, str)) and len(word) >= 1
    
    def is_valid_kanji(self, kanji):
        return len(kanji) == 1 and \
                scripts.scriptType(kanji) == scripts.Script.Kanji

class MultipleChoiceFactoryI(QuestionFactoryI):
    """An abstract factory for multiple choice questions."""
    @classmethod
    def build_question(cls, **kwargs):
        kwargs.setdefault('question_type', cls.question_type)
        kwargs.setdefault('question_plugin', cls.get_question_plugin())
        question = models.MultipleChoiceQuestion(**kwargs)
        question.save()
        return question
