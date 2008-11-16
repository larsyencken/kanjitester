# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-29.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import random

from django.db import models
from django.contrib.auth import models as auth_models
from django.conf import settings
from django import forms
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
        
    def add_options(self, distractor_values, answer):
        if answer in distractor_values:
            raise ValueError('answer included in distractor set')

        if len(filter(None, distractor_values)) < len(distractor_values) or \
                not answer:
            raise ValueError('all option values must be non-empty')

        if len(set(distractor_values + [answer])) < len(distractor_values) + 1:
            raise ValueError('all option values must be unique')

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

class TestSet(models.Model):
    user = models.ForeignKey(auth_models.User)
    questions = models.ManyToManyField(MultipleChoiceQuestion)
    responses = models.ManyToManyField(MultipleChoiceResponse)
    random_seed = models.IntegerField()

    def ordered_questions(self):
        question_list = list(self.questions.order_by('id'))
        random.seed(self.random_seed)
        random.shuffle(question_list)
        return question_list
    ordered_questions = property(ordered_questions)

    def ordered_responses(self):
        response_list = lits(self.responses.order_by('question__id'))
        if self.questions.count() != len(response_list):
            raise ValueError("need full coverage")
        random.seed(self.random_seed)
        random.shuffle(response_list)
        return response_list
    ordered_responses = property(ordered_responses)

    def get_coverage(self):
        try:
            return float(self.responses.count()) / self.questions.count()
        except ZeroDivisionError:
            return
    coverate = property(get_coverage)

    def get_accuracy(self):
        try:
            return float(self.responses.filter(option__is_correct=True
                    ).count()) / self.questions.count()
        except ZeroDivisionError:
            return
    accuracy = property(get_accuracy)

    @staticmethod
    def from_user(user, n_questions=settings.QUESTIONS_PER_SET):
        test_set = TestSet(user=user, random_seed=random.randrange(0, 2**30))
        test_set.save()

        from kanji_test.drill import load_plugins
        question_plugins = load_plugins()
        items = user.get_profile().syllabus.get_random_items(n_questions)
        questions = []
        for item in items:
            has_kanji = item.has_kanji()
            available_plugins = [p for p in question_plugins if \
                    p.requires_kanji == has_kanji]
            chosen_plugin = random.choice(available_plugins)
            questions.append(chosen_plugin.get_question(item, user))

        test_set.questions = questions
        return test_set

