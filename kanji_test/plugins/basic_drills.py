# -*- coding: utf-8 -*-
# 
#  basic_drills.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

import random

from cjktools import scripts
from cjktools import sequences
from django.core.exceptions import ObjectDoesNotExist

from kanji_test.drill import models as api_models
from kanji_test.drill import plugin_api, support
from kanji_test.lexicon import models as lexicon_models
from kanji_test.user_model import models as usermodel_models
from kanji_test import settings

#----------------------------------------------------------------------------#

class ReadingQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    """
    Generates questions based on identifying the correct reading for a word or
    kanji amongst distractors. For each kanji which needs a reading, we use
    the candidates provided from a user's (reading | kanji) error distribution.
    """
    "Distractor readings are randomly sampled."
    question_type = 'pr'
    description = 'Generates random distractor readings.'
    requires_kanji = True
    uses_dist = 'reading | kanji'
    is_adaptive = False
    verbose_name = 'random readings'

    def get_word_question(self, partial_lexeme, user):
        "See parent."
        try:
            surface = partial_lexeme.random_kanji_surface
        except ObjectDoesNotExist:
            raise plugin_api.UnsupportedItem(partial_lexeme)

        answer = partial_lexeme.reading_set.all().order_by('?')[0].reading
        question = self.build_question(pivot=surface, pivot_type='w',
                pivot_id=partial_lexeme.id, stimulus=surface,
                annotation=u'|'.join(surface))
        segments = list(surface)
        # [339] Include homographs in real reading set
        real_readings = set([
                r.reading for r in lexicon_models.LexemeReading.objects.filter( 
                        lexeme__surface_set__surface=surface)
            ])
        error_dist = usermodel_models.ErrorDist.objects.get(user=user,
                tag=self.uses_dist)
        distractor_values, annotation_map = support.build_word_options(
                segments, error_dist, adaptive=self.is_adaptive,
                exclude_set=real_readings)
        annotation_map[answer] = u'|'.join(answer)
        question.add_options(distractor_values, answer, annotation_map)
        return question

    def get_kanji_question(self, partial_kanji, user):
        "See parent."
        real_readings = set([r.reading for r in \
                partial_kanji.kanji.reading_set.all()])
        answer = partial_kanji.reading_set.order_by('?')[0].reading
        kanji = partial_kanji.kanji.kanji
        question = self.build_question(pivot=kanji, pivot_id=partial_kanji.id,
                pivot_type='k', stimulus=kanji, annotation=kanji)
        question.save()
        error_dist = usermodel_models.ErrorDist.objects.get(user=user,
                tag=self.uses_dist)
        distractor_values, annotation_map = support.build_kanji_options(kanji,
                error_dist, adaptive=self.is_adaptive,
                exclude_set=real_readings)
        annotation_map[answer] = u'|'.join(answer)
        question.add_options(distractor_values, answer, annotation_map)
        return question

#----------------------------------------------------------------------------#

class SurfaceQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    "Distractors sampled randomly from a naive surface distribution."
    question_type = 'gp'
    requires_kanji = True
    uses_dist = "kanji' | kanji"
    is_adaptive = False
    verbose_name = 'random surfaces'

    def get_kanji_question(self, partial_kanji, user):
        kanji_row = partial_kanji.kanji
        kanji = kanji_row.kanji
        error_dist = user.errordist_set.get(tag=self.uses_dist)
        distractors, _annotations = support.build_kanji_options(
                kanji, error_dist, exclude_set=set([kanji]))
        question = self.build_question(
                pivot=kanji,
                pivot_id=partial_kanji.id,
                pivot_type='k',
                stimulus=kanji_row.gloss,
            )
        question.add_options(distractors, kanji)
        return question
        
    def get_word_question(self, partial_lexeme, user):
        lexeme = partial_lexeme.lexeme
        try:
            surface = partial_lexeme.random_kanji_surface
        except ObjectDoesNotExist:
            raise plugin_api.UnsupportedItem(partial_lexeme)

        # Assume the first sense is the most frequent
        gloss = lexeme.sense_set.get(is_first_sense=True).gloss

        error_dist = user.errordist_set.get(tag=self.uses_dist)
        distractors, _annotations = support.build_word_options(
                list(surface), error_dist, exclude_set=set([surface]))
        question = self.build_question(
                pivot=surface,
                pivot_id=partial_lexeme.id,
                pivot_type='w',
                stimulus=gloss
            )
        question.add_options(distractors, surface)
        return question

#----------------------------------------------------------------------------#

class GlossQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    """Distractor glosses are sampled randomly."""
    requires_kanji = False
    question_type = 'pg'
    uses_dist = None
    is_adaptive = False
    verbose_name = 'random glosses'

    def get_kanji_question(self, partial_kanji, user):
        kanji_row = partial_kanji.kanji
        answer = kanji_row.gloss
        syllabus = user.get_profile().syllabus
        distractor_values = set()
        while len(distractor_values) < settings.N_DISTRACTORS:
            for kanji in lexicon_models.Kanji.objects.filter(
                        partialkanji__syllabus=syllabus
                    ).order_by('?')[:settings.N_DISTRACTORS]:
                distractor = kanji.gloss
                if distractor != answer:
                    distractor_values.add(distractor)
                    if len(distractor_values) > settings.N_DISTRACTORS:
                        break

        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=kanji_row.kanji,
                pivot_id=partial_kanji.id,
                pivot_type='k',
                stimulus=kanji_row.kanji,
            )
        question.add_options(distractor_values, answer)
        return question
    
    def get_word_question(self, partial_lexeme, user):
        try:
            surface = partial_lexeme.random_surface
        except ObjectDoesNotExist:
            surface = partial_lexeme.random_reading

        word_row = partial_lexeme.lexeme
        
        answer = word_row.first_sense.gloss
        syllabus = user.get_profile().syllabus

        distractor_values = set()
        exclude_set = set(s.gloss for s in word_row.sense_set.all())
        while len(distractor_values) < settings.N_DISTRACTORS:
            for sense in syllabus.sample_senses(settings.N_DISTRACTORS):
                gloss = sense.gloss
                if gloss not in exclude_set:
                    distractor_values.add(gloss)
                    if len(distractor_values) == settings.N_DISTRACTORS:
                        break

        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=surface,
                pivot_id=partial_lexeme.id,
                pivot_type='w',
                stimulus=surface,
            )
        question.add_options(distractor_values, answer)
        return question

