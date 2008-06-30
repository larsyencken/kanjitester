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
from cjktools.resources import kanjidic

import plugins.api
from lexicon import models

class ReadingQuestionFactory(plugins.api.QuestionFactoryI):
    """Forces the user to choose between alternative readings."""
    supports_kanji = True
    supports_words = True
    instructions = 'Choose the correct reading for the %s.'
    verbose_name = 'reading question factory'
    
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
        options = list(
                itertools.islice(
                    self._random_reading_iter(len(word), real_readings), 
                    5,
                )
            )
        answer = random.choice(real_readings)
        options.append(answer)
        random.shuffle(options)
        return plugins.api.Question(
                instructions=self.instructions % 'word',
                options=options,
                pivot=word,
                answer=answer,
                factory_name=self.verbose_name,
                stimulus=word,
            )
            
    def get_kanji_question(self, kanji):
        if scripts.scriptType(kanji) != scripts.Script.Kanji:
            raise ValueError("must pass in a kanji")
        kjd = kanjidic.Kanjidic.getCached()
        real_readings = kjd[kanji].allReadings
        options = list(itertools.islice(
                self._random_reading_iter(1, real_readings),
                5,
            ))
        answer = random.choice(list(real_readings))
        options.append(answer)
        random.shuffle(options)
        return plugins.api.Question(
                instructions=self.instructions % 'kanji',
                options=options,
                pivot=kanji,
                answer=answer,
                factory_name=self.verbose_name,
                stimulus=kanji,
            )
    
    def _random_reading_iter(self, length, real_reading_set):
        """Returns a random iterator over kanji readings."""
        kjd = kanjidic.Kanjidic.getCached()
        all_kanji = kjd.keys()
        while True:
            readings = []
            for _i in xrange(length):
                kanji = random.choice(all_kanji)
                reading = random.choice(list(kjd[kanji].allReadings))
                readings.append(reading)
            result = ''.join(readings)
            if result not in real_reading_set:
                yield result
