# -*- coding: utf-8 -*-
# 
#  basic_drills.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

import random
import itertools

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
    "Distractor readings are randomly sampled."
    question_type = 'pr'
    requires_kanji = True
    supports_kanji = True
    supports_words = True
    uses_dist = None

    def get_word_question(self, partial_lexeme, _user):
        try:
            surface = partial_lexeme.random_kanji_surface
        except ObjectDoesNotExist:
            raise plugin_api.UnsupportedItem(partial_lexeme)

        real_readings = [r.reading for r in 
                partial_lexeme.lexeme.reading_set.all()]
        answer = partial_lexeme.reading_set.all().order_by('?')[0].reading
        distractor_values = list(itertools.islice(
                    self._random_reading_iter(len(surface), real_readings), 
                    settings.N_DISTRACTORS,
                ))
        while len(distractor_values) > len(set(distractor_values)):
            distractor_values = list(itertools.islice(
                        self._random_reading_iter(len(surface), real_readings), 
                        settings.N_DISTRACTORS,
                    ))

        question = self.build_question(
                pivot=surface,
                pivot_type='w',
                stimulus=surface,
            )
        question.add_options(distractor_values, answer)
        return question
            
    def get_kanji_question(self, partial_kanji, _user):
        real_readings = [r.reading for r in \
                partial_kanji.kanji.reading_set.all()]
        distractor_values = list(itertools.islice(
                self._random_reading_iter(1, real_readings),
                settings.N_DISTRACTORS,
            ))
        answer = random.choice(list(real_readings))
        question = self.build_question(
                pivot=partial_kanji.kanji.kanji,
                pivot_type='k',
                stimulus=partial_kanji.kanji.kanji,
            )
        question.save()
        question.add_options(distractor_values, answer)
        return question
    
    def _random_reading_iter(self, length, real_reading_set):
        """Returns a random iterator over kanji readings."""
        previous_set = set(real_reading_set)
        while True:
            reading_parts = []
            for i in xrange(length):
                reading_parts.append(
                        lexicon_models.KanjiReadingProb.sample().symbol
                    )
            reading = ''.join(reading_parts)
            if reading not in previous_set:
                yield reading
                previous_set.add(reading)

#----------------------------------------------------------------------------#

class SurfaceQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    "Distractors sampled randomly from a naive surface distribution."
    question_type = 'gp'
    requires_kanji = True
    supports_words = True
    supports_kanji = True
    uses_dist = None

    def get_kanji_question(self, partial_kanji, user):
        kanji_row = partial_kanji.kanji
        kanji = kanji_row.kanji
        distractors, _annotations = support.build_options(kanji,
                self._build_sampler(user))
        question = self.build_question(
                pivot=kanji,
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

        language = lexicon_models.Language.get_default()

        # Assume the first sense is the most frequent
        gloss = lexeme.sense_set.filter(language=language).order_by(
                'id')[0].gloss
        distractors, _annotations = support.build_options(surface,
                self._build_sampler(user))
        question = self.build_question(
                pivot=surface,
                pivot_type='w',
                stimulus=gloss
            )
        question.add_options(distractors, surface)
        return question

    def _build_sampler(self, user):
        if not hasattr(self, '_kanji_set'):
            self._kanji_set = [row.kanji for row in \
                    lexicon_models.Kanji.objects.filter(
                        partialkanji__syllabus__userprofile__user=user)
                ]

        def sample(char):
            if scripts.scriptType(char) == scripts.Script.Kanji:
                return random.choice(self._kanji_set)
            else:
                return char

        return sample
    
#----------------------------------------------------------------------------#

# TODO Limit random glosses to within the user's syllabus.
class GlossQuestionFactory(plugin_api.MultipleChoiceFactoryI):
    """Distractor glosses are sampled randomly."""
    supports_kanji = True
    supports_words = True
    requires_kanji = False
    question_type = 'pg'
    uses_dist = None

    def get_kanji_question(self, partial_kanji, _user):
        kanji_row = partial_kanji.kanji
        answer = kanji_row.gloss
        distractor_values = set()
        while len(distractor_values) < settings.N_DISTRACTORS:
            candidate = lexicon_models.KanjiProb.sample().kanji.gloss
            if candidate != answer:
                distractor_values.add(candidate)
        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=kanji_row.kanji,
                pivot_type='k',
                stimulus=kanji_row.kanji,
            )
        question.add_options(distractor_values, answer)
        return question
    
    def get_word_question(self, partial_lexeme, _user):
        try:
            surface = partial_lexeme.random_surface
        except ObjectDoesNotExist:
            surface = partial_lexeme.random_reading

        word_row = partial_lexeme.lexeme
        
        # Use only the first sense
        answer = word_row.first_sense.gloss

        distractor_values = set()
        exclude_set = set(s.gloss for s in word_row.sense_set.all())
        while len(distractor_values) < settings.N_DISTRACTORS:
            # Find a random gloss by sampling a random surface and taking
            # its gloss. Only surfaces containing kanji are eligible.
            random_surface = lexicon_models.LexemeSurface.sample()
            if random_surface != answer and \
                    scripts.containsScript(scripts.Script.Kanji,
                            random_surface.surface):
                gloss = random_surface.lexeme.first_sense.gloss
                if gloss not in exclude_set:
                    distractor_values.add(gloss)

        distractor_values = list(distractor_values)
        question = self.build_question(
                pivot=surface,
                pivot_type='w',
                stimulus=surface,
            )
        question.add_options(distractor_values, answer)
        return question

