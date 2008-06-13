# -*- coding: utf-8 -*-
# 
#  api.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-13.
#  Copyright 2008-06-13 Lars Yencken. All rights reserved.
# 

"""Interfaces for drill tutor plugins."""

from html import *

class Question(object):
    """
    A single question which is asked of the user.
    
    >>> Question(options=['One'], answer='One', pivot='1').as_html(0)
    '<ul><li><input type="radio" name="question_0_0">One</input></li></ul>'
    """
    def __init__(self, options=None, answer=None, pivot=None, stimulus=None):
        if not (options and answer and pivot):
            raise ValueError('need options, answer and pivot as arguments')
            
        self.options = options
        self.answer = answer
        self.pivot = pivot
        self.stimulus = stimulus
    
    def as_html(self, question_id):
        """Builds and returns an html version of the question."""
        output = []
        if self.stimulus:
            output.append(P(stimulus))

        option_choices = []
        for i, option in enumerate(self.options):
            option_name = 'question_%d_%d' % (question_id, i)
            option_choices.append(
                    LI(INPUT(option, type='radio', name=option_name))
                )
        output.append(UL(*option_choices))
        return '\n'.join(output)
        
class QuestionFactoryI(object):
    """An abstract interface for factories which build questions."""
    def getName(self):
        """Returns the name of this factory."""
        raise Exception
    
    def supportsKanjiQuestions(self):
        """Returns True if kanji questions are supported, False otherwise."""
        raise Exception
            
    def supportsWordQuestions(self):
        """Returns True if word questions are supported, False otherwise."""
        raise Exception
        
    def getWordQuestion(self, word):
        """Constructs and returns a new question based on the given word."""
        raise Exception
    
    def getKanjiQuestion(self, kanji):
        """Constructs and returns a new question based on the given kanji."""
        raise Exception
