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

from util import probability
import settings

#----------------------------------------------------------------------------#

class Lexeme(models.Model):
    """A single word or phrase."""

    class Admin:
        pass
        
    def __unicode__(self):
        return '/'.join(
                s.surface for s in self.surface_set.order_by('surface')
            ) + ' [%d]' % self.id
        
class LexemeSurface(models.Model):
    """A surface rendering of the word."""
    lexeme = models.ForeignKey(Lexeme, related_name='surface_set',
            raw_id_admin=True)
    surface = models.CharField(max_length=60, db_index=True, core=True)
    priority_codes = models.CharField(blank=True, max_length=60, null=True)
    
    class Admin:
        list_display = 'lexeme', 'surface', 'priority_codes'
        search_fields = 'surface',

class LexemeReading(models.Model):
    """A valid pronunciation for a lexeme."""
    lexeme = models.ForeignKey(Lexeme, related_name='reading_set',
            raw_id_admin=True)
    reading = models.CharField(max_length=30, db_index=True, core=True)
    priority_codes = models.CharField(blank=True, max_length=60, null=True)
    
    class Admin:
        list_display = 'lexeme', 'reading', 'priority_codes'
        search_fields = 'reading',
    
class Language(models.Model):
    """A human language."""
    code = models.CharField(max_length=10, primary_key=True)
    english_name = models.CharField(max_length=100, blank=True, null=True)
    native_name = models.CharField(max_length=100, blank=True, null=True)

    class Admin:
        list_display = ('code', 'english_name', 'native_name')
        search_fields = ('code', 'english_name', 'native_name')
    
    def __unicode__(self):
        return u"Language"

class LexemeSense(models.Model):
    """A word sense."""
    lexeme = models.ForeignKey(Lexeme, related_name='sense_set')
    language = models.ForeignKey(Language)
    gloss = models.CharField(max_length=300, core=True)

    class Admin:
        list_display = ('lexeme', 'language', 'gloss')
        search_fields = ('gloss',)

    def __unicode__(self):
        return u"LexemeSense"

#----------------------------------------------------------------------------#        

class ProbI(models.Model):
    """A probabilty distribution."""
    pdf = models.FloatField()
    cdf = models.FloatField()
        
    class Meta:
        abstract = True

    @classmethod
    def sample(cls):
        """Samples and returns an object from this distribution."""
        target_cdf = random.random()
        result = cls.objects.filter(cdf__gte=target_cdf).order_by('cdf')[0]
        return result

class Prob(ProbI):
    """A basic probability distribution."""
    symbol = models.CharField(max_length=50, db_index=True, unique=True)
    
    class Admin:
        list_display = ('symbol', 'pdf', 'cdf')
        search_fields = ('symbol',)
    
    class Meta:
        abstract = True
    
    @classmethod
    def from_dist(cls, prob_dist):
        cls.objects.all().delete()
        cdf = 0.0
        for symbol in prob_dist.samples():
            pdf = prob_dist.freq(symbol)
            cdf += pdf
            row = cls(symbol=symbol, pdf=pdf, cdf=cdf)
            row.save()
        return

class CondProb(ProbI):
    """A conditional probability distribution."""
    condition = models.CharField(max_length=50, db_index=True)
    symbol = models.CharField(max_length=50, db_index=True)

    class Meta:
        abstract = True
        unique_together = (('condition', 'symbol'),)

    @classmethod
    def sample(cls, condition):
        """
        Samples and returns an object from this distribution given the 
        condition.
        """
        target_cdf = random.random()
        result = cls.objects.filter(condition=condition, cdf__gte=target_cdf
                ).order_by('cdf')[0]
        return result

    @classmethod
    def from_dist(cls, cond_prob_dist):
        cls.objects.all().delete()
        for condition in cond_prob_dist.conditions():
            cdf = 0.0
            prob_dist = cond_prob_dist[condition]
            for symbol in prob_dist.samples():
                pdf = prob_dist.freq(symbol)
                cdf += pdf
                row = cls(condition=condition, symbol=symbol, pdf=pdf,
                        cdf=cdf)
                row.save()
        return    

#----------------------------------------------------------------------------#

class KanjiReadingProb(CondProb):
    _freq_dist_file = path.join(settings.DATA_DIR, 'corpus',
            'kanji_reading_counts')
            
    class Admin:
        list_display = ('condition', 'symbol', 'pdf', 'cdf')
        search_fields = ('condition', 'symbol')
    
    class Meta:
        verbose_name = 'kanji reading probability'
        verbose_name_plural = 'kanji reading distribution'
    
    @classmethod
    def fetch_dist(cls, condition):
        return probability.FixedProb((o.symbol, o.pdf) for o in
                cls.objects.filter(condition=condition).all())
    
    @classmethod
    def initialise(cls):
        # Build the frequency distribution from our data source.
        i_stream = sopen(cls._freq_dist_file)
        dist = probability.ConditionalFreqDist()
        for line in i_stream:
            kanji, reading_counts = line.split()
            if len(kanji) != 1:
                raise ValueError('bad file format; symbol is not a kanji')

            reading_dist = dist[kanji]
            for reading_count in reading_counts.split(','):
                reading, count = reading_count.split(':')
                reading_dist.inc(reading, int(count))
        i_stream.close()
        
        # Store it to the database.
        cls.from_dist(dist)
                
    def __unicode__(self):
        return u'%s /%s/ %g' % (
                self.condition,
                self.symbol,
                self.pdf,
            )

class LexemeSurfaceProb(Prob):
    """A probability distribution over lexical surface items."""
    _freq_dist_file = path.join(settings.DATA_DIR, 'corpus',
            'jp_word_corpus_counts.gz')
            
    class Admin:
        list_display = ('symbol', 'pdf', 'cdf')
        search_fields = ('symbol',)

    class Meta:
        verbose_name = 'lexeme surface probability'
        verbose_name_plural = 'lexeme surface distribution'

    def __unicode__(self):
        return u'%s %g' % (self.symbol, self.pdf)

    @classmethod
    def initialise(cls):
        # Build the frequency distribution from our data source.
        dist = probability.FreqDist.from_file(cls._freq_dist_file)
        
        # Store it to the database.
        cls.from_dist(dist)
        
class LexemeReadingProb(CondProb):
    """A probability distribution over lexeme readings."""
    class Admin:
        list_display = ('condition', 'symbol', 'pdf', 'cdf')
        search_fields = ('condition', 'symbol')
    
    class Meta:
        verbose_name = 'lexeme reading probability'
        verbose_name_plural = 'lexeme reading distribution'
    
    def __unicode__(self):
        return u'%s /%s/ %g' % (self.condition, self.symbol, self.pdf)
