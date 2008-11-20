# -*- coding: utf-8 -*-
#
#  models.py
#  reading_alt
# 
#  Created by Lars Yencken on 09-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
Models for the reading_alt app.
"""

from django.db import models
from django.conf import settings

from hierarchy.models import HierarchicalModel

ALTERNATION_TYPES = (
        ('/', 'root node'),
        ('k', 'kanji node'),
        ('b', 'base reading'),
        ('v', 'vowel length'),
        ('s', 'sequential voicing'),
        ('g', 'sound euphony'),
        ('p', 'palatalization'),
        ('G', 'graphical similarity'),
        ('S', 'semantic similarity'),
        ('c', 'cooccurrence'),
    )

class ReadingAlternation(HierarchicalModel):
    "A single reading alternation step."

    # The surface reading form we index by.
    value = models.CharField(max_length=settings.MAX_READING_LENGTH * \
            settings.UTF8_BYTES_PER_CHAR)

    # The type of alternation which occurred.
    code = models.CharField(max_length=1, choices=ALTERNATION_TYPES)

    # The probability of this transition step.
    probability = models.FloatField()

    def __unicode__(self):
        return '<ReadingAlternation /%s/, %s, %.03f (%d, %d)>' % (
                self.value, self.code, self.probability, self.left_visit,
                self.right_visit)

    def __repr__(self):
        return unicode(self).encode('utf8')

    @staticmethod
    def get_alternation_root(kanji):
        return ReadingAlternation.objects.get(value=kanji, code='k')

class KanjiReading(models.Model):
    "A reading of a given kanji after alternations have been applied."

    reading = models.CharField(
            max_length=settings.MAX_READING_LENGTH * \
                    settings.UTF8_BYTES_PER_CHAR,
            db_index=True,
            help_text='The reading of this kanji.',
        )

    kanji = models.CharField(
            max_length=settings.UTF8_BYTES_PER_CHAR,
            help_text='The kanji from which the reading derived.',
        )

    alternations = models.CharField(max_length=len(ALTERNATION_TYPES),
            blank=True, null=True,
            help_text='The alternation codes used to get this reading.')

    probability = models.FloatField(
            help_text='The log-probability of this reading for this kanji.')

    # The final alternation step which provided this reading.
    reading_alternation = models.ForeignKey(ReadingAlternation, blank=True,
            null=True, help_text='The final alternation step which' \
            ' provided this reading.')

    def __unicode__(self):
        return u'%s /%s/ (%s)' % (self.kanji, self.reading, self.alternations)

    def get_alternation_path(self):
        """
        Determine the entire path of alternations taken to get this reading
        for this kanji. Returns a list of ReadingAlternation instances.
        """
        whole_path = list(
                ReadingAlternation.objects.filter(
                        left_visit__lt=self.reading_alternation.left_visit,
                        right_visit__gt=self.reading_alternation.right_visit
                    ).order_by('left_visit')
            )
        
        root_node = whole_path[0]
        whole_path = whole_path[1:]
        assert root_node.reading == 'root'

        return whole_path

# vim: ts=4 sw=4 sts=4 et tw=78:
