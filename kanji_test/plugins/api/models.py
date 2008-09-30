# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-29.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from django.db import models
from django.contrib.auth import models as auth_models
from cjktools.exceptions import NotYetImplementedError
from cjktools import scripts

from kanji_test.util import html

class QuestionPlugin(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    supports_kanji = models.BooleanField()
    supports_words = models.BooleanField()
    
    def __unicode__(self):
        return self.name

PIVOT_TYPES = (
        ('k', 'kanji'),
        ('w', 'word'),
    )

MC_QUESTION_TYPES = (
        ('rp', 'from reading determine pivot'),
        ('gp', 'from gloss determine pivot'),
        ('pg', 'from pivot determine gloss'),
        ('pr', 'from pivot determine reading')
    )

MC_INSTRUCTIONS = (
        ('rp', 'Choose the %s which matches the given reading.'),
        ('gp', 'Choose the %s which matches the given gloss.'),
        ('pg', 'Choose the gloss which matches the given %s.'),
        ('pr', 'Choose the reading which matches the given %s.'),
    )

class QuestionType(models.Model):
    description = models.CharField(max_length=2, choices=MC_QUESTION_TYPES, 
            primary_key=True)
    instructions = models.CharField(max_length=500)

    def __unicode__(self):
        return [full_desc for (desc, full_desc) in MC_QUESTION_TYPES if \
                desc == self.description][0]

class Question(models.Model):
    pivot = models.CharField(max_length=3, db_index=True)
    pivot_type = models.CharField(max_length=1, choices=PIVOT_TYPES)
    question_type = models.ForeignKey(QuestionType)
    question_plugin = models.ForeignKey(QuestionPlugin)

    class Meta:
        abstract = False

    def __init__(self, *args, **kwargs):
        models.Model.__init__(self, *args, **kwargs)
        # Some extra sanity-checking of the pivot at construction time.
        if self.pivot_type == 'k':
            if len(self.pivot) != 1 and \
                    scripts.ScriptType(self.pivot) != scripts.Script.Kanji:
                raise ValueError(self.pivot)
        elif self.pivot_type == 'w':
            if len(self.pivot) < 1:
                raise ValueError(self.pivot)
    
    def as_html(self):
        """Renders an html form element for the question."""
        raise NotYetImplementedError

class MultipleChoiceQuestion(Question):
    """A single question about a kanji or a word."""
    stimulus = models.CharField(max_length=400)
    
    def answer():
        doc = "The correct answer to this question."
        def fget(self):
            return self.options.get(is_correct=True)
        return locals()
    answer = property(**answer())
    
    def as_html(self):
        if not self.id:
            raise Exception('Need a database id to display')            
        output = []
        output.append(html.P(self.question_type.instructions,
                **{'class': 'instructions'}))
        if self.stimulus:
            output.append(html.P(self.stimulus, **{'class': 'stimulus'}))
            
        option_choices = []
        question_name = 'question_%d' % self.id
        for option in self.options.order_by('?'):
            if option_choices:
                option_choices.append(html.BR())
            option_choices.append(
                    html.INPUT('&nbsp;' + option.value, type='radio',
                            name=question_name)
                )
        output.append(html.P(*option_choices, **{'class': 'option_choices'}))
        output.append(html.INPUT(
                type="hidden",
                name="answer_%d" % self.id,
                value=self.answer.value,
            ))
        return '\n'.join(output)

    def add_options(self, distractor_values, answer):
        if answer in distractor_values:
            raise ValueError('answer included in distractor set')
        for option_value in distractor_values:
            self.options.create(
                    value=option_value,
                    is_correct=False,
                )
        self.options.create(value=answer, is_correct=True)

class MultipleChoiceOption(models.Model):
    """A single option in a multiple choice question."""
    question = models.ForeignKey(MultipleChoiceQuestion,
            related_name='options')
    value = models.CharField(max_length=100)
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        unique_together = (('question', 'value'),)

class Response(models.Model):
    """A generic response to the user."""
    question = models.ForeignKey(Question)
    user = models.ForeignKey(auth_models.User)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = (('question', 'user', 'timestamp'),)
        abstract = False
        
    def is_correct(self):
        raise NotYetImplementedError

class MultipleChoiceResponse(Response):
    """A response to a multiple choice question."""
    option = models.ForeignKey(MultipleChoiceOption)
        
    def is_correct(self):
        return self.option.is_correct
