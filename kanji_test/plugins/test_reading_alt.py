#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_reading_alt.py
#  kanji_test
# 
#  Created by Lars Yencken on 25-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

import unittest

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from kanji_test.user_model import models
from kanji_test.plugins import reading_alt
from kanji_test.lexicon.models import LexemeReading

def suite():
    testSuite = unittest.TestSuite((
            unittest.makeSuite(ReadingAltQuestionTest),
        ))
    return testSuite

class ReadingAltQuestionTest(unittest.TestCase):
    def setUp(self):
        User.objects.filter(username='test_user').delete()
        test_user = User(username='test_user')
        test_user.save()
        self.user = test_user

        self.factory = reading_alt.ReadingAlternationQuestions()

    def _init_syllabus(self, tag):
        self.syllabus = models.Syllabus.objects.get(tag=tag)
        self.user.userprofile_set.all().delete()
        self.user.errordist_set.all().delete()

        self.user.userprofile_set.create(syllabus=self.syllabus)
        models.ErrorDist.init_from_priors(self.user)

    def test_bug_329(self):
        "Audits every partial lexeme to find missing alignments."
        self._init_syllabus('jlpt 3')
        n_missing = 0
        for partial_lexeme in models.PartialLexeme.objects.filter(
                syllabus=self.syllabus):
            if not partial_lexeme.has_kanji():
                continue

            if partial_lexeme.alignments.count() == 0:
                n_missing += 1
            
            
        self.assertEqual(n_missing, 0)

    def test_bug_325(self):
        self._init_syllabus('jlpt 4')
        partial_kanji = models.PartialKanji.objects.get(kanji__kanji=u'後',
                syllabus=self.syllabus)
        
        # [325] an infinite loop here
        question = self.factory.get_question(partial_kanji, self.user)

        # If we get here, it worked.
        question.options.all().delete()
        question.delete()

    def test_bug_339_kanji(self):
        "Kanji questions have a unique correct answer."
        self._init_syllabus('jlpt 3')
        partial_kanji = models.PartialKanji.objects.get(kanji__kanji=u'家',
                syllabus=self.syllabus)
        real_readings = set(o.reading for o in \
                partial_kanji.kanji.reading_set.all())
        for i in xrange(100):
            question = self.factory.get_kanji_question(partial_kanji,
                    self.user)
            distractor_values = set(o.value for o in question.options.all() \
                    if not o.is_correct)
            correct_value = question.options.get(is_correct=True).value
            assert correct_value in real_readings
            self.assertEqual(
                    real_readings.intersection(distractor_values), set()
                )
            question.options.all().delete()
            question.delete()
    
    def test_bug_339_words(self):
        "Word questions have a unique correct answer."
        self._init_syllabus('jlpt 3')
        surface = u'家'
        # Include readings from homographs.
        real_readings = set(o.reading for o in LexemeReading.objects.filter(
                lexeme__surface_set__surface=surface))
        for partial_lexeme in models.PartialLexeme.objects.filter(
                lexeme__surface_set__surface=surface, syllabus=self.syllabus):
            for i in xrange(50):
                question = self.factory.get_question(partial_lexeme,
                        self.user)
                distractor_values = set(o.value for o in \
                        question.options.all() if not o.is_correct)
                correct_value = question.options.get(is_correct=True).value
                assert correct_value in real_readings
                self.assertEqual(
                        real_readings.intersection(distractor_values), set()
                    )
                question.options.all().delete()
                question.delete()

    def tearDown(self):
        pass

#----------------------------------------------------------------------------#

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())

#----------------------------------------------------------------------------#

# vim: ts=4 sw=4 sts=4 et tw=78:
