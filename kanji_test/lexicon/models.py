# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-06-21.
#  Copyright 2008-06-21 Lars Yencken. All rights reserved.
# 

import random
from os import path

from django.db import models
from cjktools.common import sopen
from cjktools.resources import kanjidic
from cjktools import scripts

from kanji_test.util import probability, prob_models
from kanji_test import settings

#----------------------------------------------------------------------------#

class Lexeme(models.Model):
    """A single word or phrase."""
    def _get_default_sense_set(self):
        language = Language.objects.get(code=settings.DEFAULT_LANGUAGE_CODE)
        return self.sense_set.filter(language=language)
    default_sense_set = property(_get_default_sense_set)
    
    def _get_random_sense(self):
        results = list(self.default_sense_set)
        return random.choice(results)
    random_sense = property(_get_random_sense)
        
    def __unicode__(self):
        return '/'.join(
                s.surface for s in self.surface_set.order_by('surface')
            ) + ' [%d]' % self.id
        
class LexemeSurface(models.Model):
    """A surface rendering of the word."""
    lexeme = models.ForeignKey(Lexeme, related_name='surface_set')
    surface = models.CharField(max_length=60, db_index=True)
    priority_codes = models.CharField(blank=True, max_length=60, null=True)

    @staticmethod
    def sample():
        while True:
            surface = LexemeSurfaceProb.sample().symbol
            matches = LexemeSurface.objects.filter(surface=surface)
            if len(matches) > 0:
                return random.choice(matches)

    def _get_prob(self):
        return models.LexemeSurfaceProb.objects.get(symbol=self.surface)
    prob = property(_get_prob)
    
    def __unicode__(self):
        return self.surface

class LexemeReading(models.Model):
    """A valid pronunciation for a lexeme."""
    lexeme = models.ForeignKey(Lexeme, related_name='reading_set')
    reading = models.CharField(max_length=50, db_index=True)
    priority_codes = models.CharField(blank=True, max_length=60, null=True)
    
class Language(models.Model):
    """A human language."""
    code = models.CharField(max_length=10, primary_key=True)
    english_name = models.CharField(max_length=100, blank=True, null=True)
    native_name = models.CharField(max_length=100, blank=True, null=True)

    def __unicode__(self):
        return u"Language"

class LexemeSense(models.Model):
    """A word sense."""
    lexeme = models.ForeignKey(Lexeme, related_name='sense_set')
    language = models.ForeignKey(Language)
    gloss = models.CharField(max_length=400)

    def __unicode__(self):
        return u'%s [%s]' % (self.gloss, self.language.code)

#----------------------------------------------------------------------------#        

class KanjiProb(prob_models.Prob):
    """A frequency distribution over kanji."""
    _freq_dist_file = path.join(settings.DATA_DIR, 'corpus',
            'jp_char_corpus_counts.gz')

    def _get_kanji(self):
        return Kanji.objects.get(kanji=self.symbol)
    kanji = property(_get_kanji)

    class Meta(prob_models.Prob.Meta):
        verbose_name = 'probability of kanji'
        verbose_name_plural = 'distribution of kanji'

    def __unicode__(self):
        return u"KanjiProb"
        
    @classmethod
    def initialise(cls):
        dist = probability.FreqDist.from_file(cls._freq_dist_file)
        cls.from_dist(dist)
    
    @classmethod
    def sample_kanji(cls):
        return Kanji.objects.get(kanji=cls.sample().symbol)

class KanjiReadingProb(prob_models.Prob):
    """A frequency distribution of kanji pronunciations."""
    _freq_dist_file = path.join(settings.DATA_DIR, 'corpus',
            'kanji_reading_counts')
        
    class Meta(prob_models.Prob.Meta):
        verbose_name = 'probability of reading'
        verbose_name_plural = 'distribution of readings'
    
    @classmethod
    def initialise(cls):
        cond_dist = probability.ConditionalFreqDist.from_file(
                cls._freq_dist_file, format='packed')
        dist = cond_dist.without_condition()
        cls.from_dist(dist)

class KanjiReadingCondProb(prob_models.CondProb):
    """
    A conditional frequency distribution over kanji readings.
    
    >>> KanjiReadingCondProb.initialise()
    >>> KanjiReadingCondProb.objects.filter(condition=unicode('日')).count()
    45
    """
    _freq_dist_file = path.join(settings.DATA_DIR, 'corpus',
            'kanji_reading_counts')
    
    def _get_kanji_reading(self):
        return KanjiReading.objects.get(kanji=self.condition,
                reading=self.symbol)
    kanji_reading = property(_get_kanji_reading)
    
    class Meta(prob_models.CondProb.Meta):
        verbose_name = 'probability of reading given kanji'
        verbose_name_plural = 'distribution of readings given kanji'
    
    @classmethod
    def fetch_dist(cls, condition):
        return probability.FixedProb((o.symbol, o.pdf) for o in
                cls.objects.filter(condition=condition).all())
    
    @classmethod
    def initialise(cls):
        dist = probability.ConditionalFreqDist.from_file(cls._freq_dist_file,
                format='packed')
        cls.from_dist(dist)
    
    @classmethod
    def sample_kanji_reading(cls):
        row = cls.sample()
        return models.KanjiReading.objects.get(kanji=row.condition,
                reading=row.symbol)

    def __unicode__(self):
        return u'%s /%s/ %g' % (
                self.condition,
                self.symbol,
                self.pdf,
            )

class LexemeSurfaceProb(prob_models.Prob):
    """A probability distribution over lexical surface items."""
    _freq_dist_file = path.join(settings.DATA_DIR, 'corpus',
            'jp_word_corpus_counts.gz')

    class Meta(prob_models.Prob.Meta):
        verbose_name = 'probability of lexeme surface'
        verbose_name_plural = 'distribution of lexeme surfaces'

    def __unicode__(self):
        return u'%s %g' % (self.symbol, self.pdf)

    @classmethod
    def initialise(cls):
        dist = probability.FreqDist.from_file(cls._freq_dist_file)
        cls.from_dist(dist)
        
class LexemeReadingProb(prob_models.CondProb):
    """A probability distribution over lexeme readings."""    
    class Meta(prob_models.CondProb.Meta):
        verbose_name = 'probability of reading given lexeme'
        verbose_name_plural = 'distribution of readings given lexeme'
    
    def __unicode__(self):
        return u'%s /%s/ %g' % (self.condition, self.symbol, self.pdf)
    
    @classmethod
    def initialise(cls):
        # TODO Find a data source for lexeme reading probabilities.
        pass

#----------------------------------------------------------------------------#

class Kanji(models.Model):
    """A single unique kanji and its meaning."""
    kanji = models.CharField(max_length=3, primary_key=True)
    gloss = models.CharField(max_length=200)
    
    def _get_prob(self):
        return KanjiProb.objects.get(symbol=kanji)
    prob = property(_get_prob)
    
    class Meta:
        ordering = ['kanji']
        verbose_name_plural = 'kanji'

    def __unicode__(self):
        return self.kanji
    
    @classmethod
    def initialise(cls):
        KanjiReading.objects.all().delete()
        Kanji.objects.all().delete()
        kjd = kanjidic.Kanjidic.getCached()
        max_gloss_len = [f for f in cls._meta.fields \
                if f.name == 'gloss'][0].max_length
        for entry in kjd.itervalues():
            truncated_gloss = ', '.join(entry.gloss)[:max_gloss_len]
            kanji = Kanji(kanji=entry.kanji, gloss=truncated_gloss)
            kanji.save()
            for reading in cls._clean_readings(entry.onReadings):
                kanji.reading_set.create(reading=reading, reading_type='o')
            for reading in cls._clean_readings(entry.kunReadings):
                kanji.reading_set.create(reading=reading, reading_type='k')
        return
    
    @staticmethod
    def _clean_readings(reading_list):
        return set(
                scripts.toHiragana(r.split('.')[0]) for r in reading_list
            )
    
class KanjiReading(models.Model):
    """A reading for a single kanji."""
    kanji = models.ForeignKey(Kanji, related_name='reading_set')
    reading = models.CharField(max_length=21, db_index=True)
    READING_TYPES = (('o', 'on'), ('k', 'kun'))
    reading_type = models.CharField(max_length=1, choices=READING_TYPES)
    
    def _get_prob(self):
        return KanjiReadingCondProb.objects.get(condition=kanji,
                symbol=reading)
    prob = property(_get_prob)
    
    class Meta:
        unique_together = (('reading', 'kanji', 'reading_type'),)

    def __unicode__(self):
        return u'%s /%s/' % (self.kanji, self.reading)

def initialise():
    Kanji.initialise()
    KanjiProb.initialise()
    KanjiReadingProb.initialise()
    KanjiReadingCondProb.initialise()
    LexemeSurfaceProb.initialise()
    LexemeReadingProb.initialise()
