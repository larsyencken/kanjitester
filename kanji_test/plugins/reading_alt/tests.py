# -*- coding: utf-8 -*-
#
#  test.py
#  reading_alt
# 
#  Created by Lars Yencken on 24-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

import unittest

from django.test import TestCase
from django.contrib.auth.models import User

class UserModelTest(TestCase):
    pass

class QuestionTest(TestCase):
    fixtures = ['reading_alt']

    def setUp(self):
        from kanji_test.plugins.reading_alt import ReadingAlternationQuestions
        self.factory = ReadingAlternationQuestions()

    def test_word_question(self):
        user = User.objects.get(username='dummy')
        word = user.get_profile().syllabus.partiallexeme_set.all()[0]
        assert isinstance(word.surface_set.all()[0].surface, unicode)
        self.factory.get_question(word, user)

    def test_kanji_question(self):
        user = User.objects.get(username='dummy')
        kanji = user.get_profile().syllabus.partialkanji_set.all()[0]
        self.factory.get_question(kanji, user)

# vim: ts=4 sw=4 sts=4 et tw=78:

