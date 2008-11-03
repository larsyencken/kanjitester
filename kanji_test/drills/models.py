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

QUESTION_TYPES = (
        ('rp', 'from reading determine pivot'),
        ('gp', 'from gloss determine pivot'),
        ('pg', 'from pivot determine gloss'),
        ('pr', 'from pivot determine reading')
    )

INSTRUCTIONS = {
        'rp': 'Choose the %s which matches the given reading.',
        'gp': 'Choose the %s which matches the given gloss.',
        'pg': 'Choose the gloss which matches the given %s.',
        'pr': 'Choose the reading which matches the given %s.',
    }

class Question(models.Model):
    pivot = models.CharField(max_length=30, db_index=True)
    pivot_type = models.CharField(max_length=1, choices=PIVOT_TYPES)
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES)
    question_plugin = models.ForeignKey(QuestionPlugin)

    def pivot_type_verbose():
        def fget(self):
            return [vd for (d, vd) in PIVOT_TYPES if d == self.pivot_type][0]
        return locals()
    pivot_type_verbose = property(**pivot_type_verbose())

    def question_type_verbose():
        def fget(self):
            return [vd for (d, vd) in QUESTION_TYPES 
                    if d == self.question_type][0]
        return locals()
    question_type_verbose = property(**question_type_verbose())

    def instructions():
        def fget(self):
            return INSTRUCTIONS[self.question_type] % self.pivot_type_verbose
        return locals()
    instructions = property(**instructions())

    class Meta:
        abstract = False

    def __unicode__(self):
        return 'type %s about %s %s' % (
                self.question_type,
                self.pivot_type_verbose,
                self.pivot,
            )

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
    
    def _get_stimulus_class(self, stimulus):
        if scripts.scriptType(stimulus) == scripts.Script.Ascii:
            return 'stimulus_roman'
        else:
            return 'stimulus_cjk'
        
    def as_html(self):
        if not self.id:
            raise Exception('Need a database id to display')            
        output = []
        output.append(html.P(self.instructions,
                **{'class': 'instructions'}))
        if self.stimulus:
            output.append(html.P(self.stimulus, 
                    **{'class': self._get_stimulus_class(self.stimulus)}))
            
        option_choices = []
        question_name = 'question_%d' % self.id
        for option in self.options.order_by('?'):
            if scripts.scriptType(option.value) == scripts.Script.Ascii:
                separator = html.BR()
                option_class = 'option_choices_roman'
            else:
                separator = '&nbsp;' * 3
                option_class = 'option_choices_cjk'
            
            if option_choices:
                option_choices.append(separator)
            
            option_choices.append(
                    html.INPUT('&nbsp;' + html.SPAN(option.value,
                            **{'class': option_class}), type='radio',
                            name=question_name, value=option.id)
                )
        output.append(html.P(*option_choices, **{'class': 'option_choices'}))
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
    value = models.CharField(max_length=200)
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
