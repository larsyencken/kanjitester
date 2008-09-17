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

import settings
import lexicon.models
import plugins.api
from plugins.visual_similarity import load_neighbours
from plugins.visual_similarity import models

class SimilarityWithReading(plugins.api.QuestionFactoryI):
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
        reading = lexicon.models.KanjiReadingCondProb.sample(kanji).symbol
        answer = kanji
        
        # Get the distractor set.
        edge_set = list(models.SimilarityEdge.objects.filter(label=kanji
                ).order_by('weight'))
        
        # 4. Filter out distractors which have the given reading.
        filtered_options = []
        for edge in edge_set:
            if lexicon.models.KanjiReading.objects.filter(
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

        return plugins.api.Question(
                instructions=self.instructions % 'kanji',
                options=options,
                pivot=kanji,
                answer=answer,
                factory=self.__class__,
                stimulus=reading,
            )
    
class SimilarityWithMeaning(plugins.api.QuestionFactoryI):
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
        kanji_row = lexicon.models.Kanji.objects.get(kanji=kanji)
        neighbour_rows = models.SimilarityEdge.objects.filter(label=kanji
                ).order_by('weight')
        options = [
                    row.neighbour_label for row in neighbour_rows
                ][:settings.N_DISTRACTORS]
        options.append(kanji)        
        random.shuffle(options)
        return plugins.api.Question(
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
