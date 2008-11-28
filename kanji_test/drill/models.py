# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-09-29.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import random
import traceback

from django.db import models
from django.core.mail import send_mail
from django.contrib.auth import models as auth_models
from django.conf import settings
from django import forms
from cjktools.exceptions import NotYetImplementedError
from cjktools import scripts

from kanji_test.util import html
from kanji_test.user_model import models as usermodel_models
from kanji_test.user_model import plugin_api

class QuestionPlugin(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    supports_kanji = models.BooleanField()
    supports_words = models.BooleanField()
    uses_dist = models.CharField(max_length=100, null=True, blank=True)
    
    def __unicode__(self):
        return self.name
    
    def update(self, response):
        """
        Update our error model given this response. May fail silently
        and attempt to notify admins of an error.
        """
        if not self.uses_dist:
            return
        plugin_map = plugin_api.load_plugins()
        try:
            plugin_map[self.uses_dist].update(response)
        except:
            error_message = "In updating %s:\n\n%s" % (
                    self.uses_dist,
                    traceback.format_exc(),
                )
            send_mail('Error at jlpt.gakusha.info', error_message,
                    settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL],
                    fail_silently=True)
        return

PIVOT_TYPES = (
        ('k', 'kanji'),
        ('w', 'word'),
    )

QUESTION_TYPES = (
        ('rp', 'from reading determine pivot'),
        ('gp', 'from gloss determine pivot'),
        ('pg', 'from pivot determine gloss'),
        ('pr', 'from pivot determine reading'),
    )

INSTRUCTIONS = {
        'rp': 'Choose the %s which matches the given reading.',
        'gp': 'Choose the %s which matches the given gloss.',
        'pg': 'Choose the gloss which matches the given %s.',
        'pr': 'Choose the reading which matches the given %s.',
    }

class Question(models.Model):
    pivot = models.CharField(max_length=30, db_index=True,
        help_text="The word or kanji this question is created for.")
    pivot_id = models.IntegerField(
        help_text="The id of the pivot PartialKanji or PartialLexeme.")
    pivot_type = models.CharField(max_length=1, choices=PIVOT_TYPES,
        help_text="Is this a word or a kanji question?")
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES,
        help_text="The broad type of this question.")
    question_plugin = models.ForeignKey(QuestionPlugin,
        help_text="The plugin which generated this question.")
    annotation = models.CharField(max_length=100, null=True, blank=True,
        help_text="Scratch space for question plugin annotations.")
    
    class Meta:
        abstract = False

    def __unicode__(self):
        return 'type %s about %s %s' % (
                self.question_type,
                self.get_pivot_type_display(),
                self.pivot,
            )

    def instructions():
        def fget(self):
            return INSTRUCTIONS[self.question_type] % \
                    self.get_pivot_type_display()
        return locals()
    instructions = property(**instructions())

    def get_pivot_item(self):
        if self.pivot_type == 'k':
            return usermodel_models.PartialKanji.objects.get(id=self.pivot_id)

        assert self.pivot_type == 'w'
        return usermodel_models.PartialLexeme.objects.get(id=self.pivot_id)

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
        
    def add_options(self, distractor_values, answer, annotation_map=None):
        if answer in distractor_values:
            raise ValueError('answer included in distractor set')

        if len(filter(None, distractor_values)) < len(distractor_values) or \
                not answer:
            raise ValueError('all option values must be non-empty')

        annotation_map = annotation_map or {}
        if annotation_map and len(annotation_map) != len(distractor_values) + 1:
            raise ValueEror('need annotation_map for every distractor')

        if len(set(distractor_values + [answer])) < len(distractor_values) + 1:
            raise ValueError('all option values must be unique')

        for i, option_value in enumerate(distractor_values):
            self.options.create(
                    value=option_value,
                    is_correct=False,
                    annotation=annotation_map.get(option_value),
                )
        self.options.create(value=answer, is_correct=True,
                annotation=annotation_map.get(answer))

class MultipleChoiceOption(models.Model):
    """A single option in a multiple choice question."""
    question = models.ForeignKey(MultipleChoiceQuestion,
            related_name='options')
    value = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    annotation = models.CharField(max_length=100, null=True, blank=True)

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

    def save(self, *args, **kwargs):
        """
        Save this response, and update the error model which generated it as
        a side-effect.
        """
        super(MultipleChoiceResponse, self).save(*args, **kwargs)
        self.question.question_plugin.update(self)

class TestSet(models.Model):
    user = models.ForeignKey(auth_models.User)
    questions = models.ManyToManyField(MultipleChoiceQuestion)
    responses = models.ManyToManyField(MultipleChoiceResponse)
    random_seed = models.IntegerField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    set_type = models.CharField(max_length=1, choices=(
            ('c', 'control'),
            ('a', 'adaptive'),
        ))

    @staticmethod
    def get_latest(user):
        return TestSet.objects.filter(user=user).order_by('-end_time')[0]

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
        """
        Generate a new test set for this user using their profile to determine
        the appropriate syllabus.
        """
        set_type, plugin_set = TestSet._get_plugin_set(user)
        test_set = TestSet(user=user, random_seed=random.randrange(0, 2**30),
                set_type=set_type)
        test_set.save()

        from kanji_test.drill import load_plugins
        from kanji_test.drill.plugin_api import UnsupportedItem
        question_plugins = load_plugins(plugin_set)
        items = user.get_profile().syllabus.get_random_items(n_questions)
        questions = []
        for item in items:
            has_kanji = item.has_kanji()
            available_plugins = [p for p in question_plugins if \
                    p.requires_kanji == has_kanji]
            question = None
            while question == None and available_plugins:
                i = random.randrange(len(available_plugins))
                chosen_plugin = available_plugins[i]
                try:
                    question = chosen_plugin.get_question(item, user)
                    questions.append(question)
                except UnsupporedItem:
                    # Oh well, try again with another plugin
                    del available_plugins[i]

        test_set.questions = questions
        return test_set

    @staticmethod
    def _get_plugin_set(user):
        "Determine the set type and the plugins to use for the next test set."
        try:
            previous_set = TestSet.get_latest(user)
        except IndexError:
            # Start with the adaptive set
            set_type = 'a'
            plugin_set = settings.ADAPTIVE_DRILL_PLUGINS
            return set_type, plugin_set

        # Alternate between control and adaptive sets
        if previous_set.set_type == 'a':
            set_type = 'c'
            plugin_set = settings.CONTROL_DRILL_PLUGINS
        else:
            set_type = 'a'
            plugin_set = settings.ADAPTIVE_DRILL_PLUGINS

        return set_type, plugin_set

