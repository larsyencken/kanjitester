# -*- coding: utf-8 -*-
# 
#  __init__.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

import random
import itertools

from cjktools import scripts
from cjktools import sequences

from kanji_test.plugins import api
from kanji_test.lexicon import models
from kanji_test import settings

class ReadingQuestionFactory(api.QuestionFactoryI):
    """Forces the user to choose between alternative readings."""
    supports_kanji = True
    supports_words = True
    instructions = 'Choose the correct reading for the %s.'
    question_type = 'identify reading given kanji'
    question_variant = 'randomly sampled readings'
    
    def get_word_question(self, word):
        if not scripts.containsScript(scripts.Script.Kanji, word):
            raise ValueError("must pass in a word containing kanji")
        lexeme_surface = models.LexemeSurface.objects.get(surface=word)
        real_readings = [
                    o['reading'] for o in \
                    models.LexemeReading.objects.filter(
                        lexeme=lexeme_surface.lexeme
                    ).values('reading')
                ]
        answer = random.choice(real_readings)
        options = list(
                itertools.islice(
                    self._random_reading_iter(len(word), real_readings), 
                    settings.N_DISTRACTORS,
                )
            )
        options.append(answer)
        random.shuffle(options)
        return api.Question(
                instructions=self.instructions % 'word',
                options=options,
                pivot=word,
                answer=answer,
                factory=self.__class__,
                stimulus=word,
            )
            
    def get_kanji_question(self, kanji):
        if scripts.scriptType(kanji) != scripts.Script.Kanji or \
                len(kanji) != 1:
            raise ValueError("must pass in a kanji")
        real_readings = [r.reading for r in \
                models.KanjiReading.objects.filter(kanji=kanji)]
        options = list(itertools.islice(
                self._random_reading_iter(1, real_readings),
                settings.N_DISTRACTORS,
            ))
        answer = random.choice(list(real_readings))
        options.append(answer)
        random.shuffle(options)
        return api.Question(
                instructions=self.instructions % 'kanji',
                options=options,
                pivot=kanji,
                answer=answer,
                factory=self.__class__,
                stimulus=kanji,
            )
    
    def _random_reading_iter(self, length, real_reading_set):
        """Returns a random iterator over kanji readings."""
        while True:
            reading_parts = []
            for i in xrange(length):
                reading_parts.append(models.KanjiReadingProb.sample().symbol)
            reading = ''.join(reading_parts)
            if reading not in real_reading_set:
                yield reading

class SurfaceQuestionFactory(api.QuestionFactoryI):
    """
    A source of questions where the user must choose the right kanji 
    representation for a known gloss.
    """
    question_type = 'identify kanji given gloss'
    question_variant = 'randomly sampled surface, constrained by length and script'
    supports_words = True
    supports_kanji = True
    instructions = 'Choose the %s with the given meaning.'
    
    def get_kanji_question(self, kanji):
        kanji_row = models.Kanji.objects.get(kanji=kanji)
        option_set = set([kanji])
        while len(option_set) < settings.N_DISTRACTORS + 1:
            random_kanji = models.KanjiProb.sample().symbol
            option_set.add(random_kanji)
        options = list(option_set)
        random.shuffle(options)
        return api.Question(
                instructions=self.instructions % 'kanji',
                options=options,
                answer=kanji,
                pivot=kanji,
                stimulus=kanji_row.gloss,
                factory=self.__class__,
            )
        
    def get_word_question(self, word):
        lexeme = models.LexemeSurface.objects.get(surface=word).lexeme
        language = models.Language.objects.get(
                code=settings.DEFAULT_LANGUAGE_CODE)
        gloss = ', '.join(r.gloss for r in \
                lexeme.sense_set.filter(language=language))
        option_chars = map(list, [word] * settings.N_DISTRACTORS)
        for j in xrange(len(word)):
            if scripts.scriptType(word[j]) != scripts.Script.Kanji:
                continue
            
            for i in xrange(settings.N_DISTRACTORS):
                option_chars[i][j] = models.KanjiProb.sample().symbol
        
        options = [''.join(option) for option in option_chars]
        options.append(word)
        random.shuffle(options)
        return api.Question(
                instructions=self.instructions % 'word',
                options=options,
                answer=word,
                pivot=word,
                stimulus=gloss,
                factory=self.__class__,
            )

class GlossQuestionFactory(api.QuestionFactoryI):
    """Asks the user to identify the correct gloss for the stimulus."""
    supports_kanji = True
    supports_words = True
    question_type = 'identify gloss given kanji'
    question_variant = 'randomly sampled gloss'
    instructions = 'Choose the correct meaning for the given %s.'

    def get_kanji_question(self, kanji):
        kanji_row = models.Kanji.objects.get(kanji=kanji)
        answer = kanji_row.gloss
        stimulus = kanji
        options = set([answer])
        while len(options) < settings.N_DISTRACTORS + 1:
            options.add(
                    models.KanjiProb.sample().kanji.gloss,
                )
        options = list(options)
        random.shuffle(options)
        return api.Question(
                instructions=self.instructions % 'kanji',
                options=options,
                answer=answer,
                pivot=kanji,
                stimulus=kanji,
                factory=self.__class__,
            )
    
    def get_word_question(self, word):
        word_row = models.LexemeSurface.objects.get(surface=word).lexeme
        answer = word_row.random_sense.gloss
        options = set([answer])
        while len(options) < settings.N_DISTRACTORS + 1:
            while True:
                random_surface = models.LexemeSurface.sample()
                if scripts.containsScript(scripts.Script.Kanji,
                        random_surface.surface):
                    options.add(random_surface.lexeme.random_sense.gloss)
                    break
        options = list(options)
        random.shuffle(options)
        return api.Question(
                instructions=self.instructions % 'word',
                options=options,
                answer=answer,
                pivot=word,
                stimulus=word,
                factory=self.__class__,
            )
