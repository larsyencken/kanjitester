# -*- coding: utf-8 -*-
# 
#  __init__.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

"""
Plugin for visual similarity.
"""

import random

from cjktools import scripts

from kanji_test import settings
from kanji_test.lexicon import models as lexicon_models
from kanji_test.plugins import api
from kanji_test.plugins.visual_similarity import models

import load_neighbours

class SimilarityWithReading(api.QuestionFactoryI):
    """
    Given a reading, makes the user choose which of similar kanji have that
    reading.
    """
    supports_kanji = True
    supports_words = False
    question_type = 'identify kanji given reading'
    question_variant = 'visual similarity'
    instructions = 'Choose the correct %s for the given reading.'
    # required_knowledge = ['pronunciation', 'recognition']
    # ambiguity = ['recognition']
    
    def get_kanji_question(self, kanji):
        assert len(kanji) == 1 and type(kanji) == unicode and \
                scripts.scriptType(kanji) == scripts.Script.Kanji
        
        # Sample a reading according to this kanji's reading distribution.
        reading = lexicon_models.KanjiReadingCondProb.sample(kanji).symbol
        answer = kanji
        
        # Get the distractor set.
        edge_set = list(models.SimilarityEdge.objects.filter(label=kanji
                ).order_by('weight'))
        
        # 4. Filter out distractors which have the given reading.
        filtered_options = []
        for edge in edge_set:
            if lexicon_models.KanjiReading.objects.filter(
                        kanji=edge.neighbour_label,
                        reading=reading
                    ).count() == 0:
                filtered_options.append(edge)
        
        # 5. Randomly choose amongst remaining distractors according to
        #    weight.
        # random.shuffle(filtered_options)
        options = [edge.neighbour_label for edge in filtered_options]
        options = options[:settings.N_DISTRACTORS]
        options.append(answer)

        return api.Question(
                instructions=self.instructions % 'kanji',
                options=options,
                pivot=kanji,
                answer=answer,
                factory=self.__class__,
                stimulus=reading,
            )
    
class SimilarityWithMeaning(api.QuestionFactoryI):
    """
    Given a gloss, makes the user choose which of similar kanji have that
    gloss.
    """
    # required_knowledge = ['meaning', 'recognition']
    # ambiguity = ['recognition']
    question_type = 'identify kanji given gloss'
    question_variant = 'visual similarity'
    supports_words = False
    supports_kanji = True
    instructions = 'Choose the %s with the given meaning.'
    
    def get_kanji_question(self, kanji):
        kanji_row = lexicon_models.Kanji.objects.get(kanji=kanji)
        neighbour_rows = models.SimilarityEdge.objects.filter(label=kanji
                ).order_by('weight')
        options = [
                    row.neighbour_label for row in neighbour_rows
                ][:settings.N_DISTRACTORS]
        options.append(kanji)        
        random.shuffle(options)
        return api.Question(
                instructions=self.instructions % 'kanji',
                options=options,
                answer=kanji,
                pivot=kanji,
                stimulus=kanji_row.gloss,
                factory=self.__class__,
            )
    
def build():
    "Load the similarity graph into the database."
    load_neighbours.load_neighbours()
