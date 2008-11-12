# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-24.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

import random

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from cjktools.stats import mean

from kanji_test.lexicon import models as lexicon_models
from kanji_test.util import models as util_models

class Syllabus(models.Model):
    tag = models.CharField(max_length=100, unique=True,
        help_text="A unique name for this syllabus.")
    
    class Meta:
        verbose_name_plural = 'syllabi'
    
    def __unicode__(self):
        return self.tag

    def get_random_item(self):
        "Returns a random item from this syllabus, either kanji or lexeme."
        if random.random() < self._get_word_proportion():
            return self.partiallexeme_set.order_by('?')[0]
        else:
            return self.partialkanji_set.order_by('?')[0]

    def get_random_kanji_item(self):
        if random.random() < self._get_kanji_word_proportion():
            return self.partiallexeme_set.filter(
                    surface_set__has_kanji=True).order_by('?')[0]
        else:
            return self.partialkanji_set.order_by('?')[0]

    def _get_word_proportion(self):
        "Determine the raw proportion of syllabus items which are words."
        if not hasattr(self, '_cached_word_prop'):
            n_words = self.partiallexeme_set.count()
            n_kanji = self.partialkanji_set.count()
            self._cached_word_prop = float(n_words) / (n_words + n_kanji)
        
        return self._cached_word_prop

    def _get_kanji_word_proportion(self):
        if not hasattr(self, '_cached_kanji_word_prop'):
            n_words = self.partiallexeme_set.filter(
                    surface_set__has_kanji=True).count()
            n_kanji = self.partialkanji_set.count()
            self._cached_kanji_word_prop = float(n_words) / (n_words + n_kanji)

        return self._cached_kanji_word_prop

class PartialLexeme(models.Model):
    """A subset of an individual lexeme."""
    syllabus = models.ForeignKey(Syllabus)
    lexeme = models.ForeignKey(lexicon_models.Lexeme,
            help_text="The word under consideration.")
    reading_set = models.ManyToManyField(lexicon_models.LexemeReading)
    sense_set = models.ManyToManyField(lexicon_models.LexemeSense)
    surface_set = models.ManyToManyField(lexicon_models.LexemeSurface)
    
    def __unicode__(self):
        return '/'.join(s.surface for s in self.surface_set.all()) + ' ' + \
            '[%s]' % '/'.join(r.reading for r in self.reading_set.all())
        return self.lexeme.surface_set.all()[0].surface

    def random_surface():
        def fget(self):
            try:
                return self.surface_set.all().order_by('?')[0].surface
            except IndexError:
                raise ObjectDoesNotExist
        return locals()
    random_surface = property(**random_surface())

    def random_kanji_surface():
        "Returns a random surface for this lexeme containing kanji."
        def fget(self):
            try:
                return self.surface_set.filter(has_kanji=True).order_by(
                    '?')[0].surface
            except IndexError:
                raise ObjectDoesNotExist
        return locals()
    random_kanji_surface = property(**random_kanji_surface())

    class Meta:
        unique_together = (('syllabus', 'lexeme'),)

class SenseNote(models.Model):
    """
    Additional notes provided with the syllabus about which senses were
    intended for a lexeme.
    """
    partial_lexeme = models.ForeignKey(PartialLexeme)
    note = models.CharField(max_length=300)

class PartialKanji(models.Model):
    syllabus = models.ForeignKey(Syllabus)
    kanji = models.ForeignKey(lexicon_models.Kanji,
            help_text='The kanji itself.')
    reading_set = models.ManyToManyField(lexicon_models.KanjiReading,
            help_text='The readings in this syllabus.')

    def n_readings(self):
        return self.reading_set.count()
    n_readings = property(n_readings)
    
    class Meta:
        verbose_name_plural = 'partial kanji'
        unique_together = (('syllabus', 'kanji'),)

#----------------------------------------------------------------------------#

class PriorDist(models.Model):
    "A syllabus-specific prior distribution."
    syllabus = models.ForeignKey(Syllabus)
    tag = models.CharField(max_length=100)

    class Meta:
        unique_together = (('syllabus', 'tag'),)
        verbose_name = 'prior distribution'
        verbose_name_plural = 'prior distributions'

    def __unicode__(self):
        return self.tag

    def get_accuracy(self):
        return mean(o['pdf'] for o in self.density.values('pdf'))

class PriorPdf(util_models.CondProb):
    "Individual densities for a prior distribution."
    dist = models.ForeignKey(PriorDist, related_name='density')
    is_correct = models.BooleanField(default=False)        

    class Meta:
        unique_together = (('dist', 'condition', 'symbol'),)
        verbose_name_plural = 'prior density'

#----------------------------------------------------------------------------#

class ErrorDist(models.Model):
    "A user-specific prior disribution."
    user = models.ForeignKey(User, unique=True)
    tag = models.CharField(max_length=100, unique=True)

    def prior_dist(self):
        return PriorDist.objects.get(tag=self.tag)
    prior_dist = property(prior_dist)

    class Meta:
        unique_together = (('user', 'tag'),)
        verbose_name = 'error distribution'
        verbose_name_plural = 'error distributions'

    def __unicode__(self):
        return '%s: %s' % (self.user.username, self.tag)
        
    @classmethod
    def init_from_priors(cls, user):
        """Initialise user copies of prior dists."""
        user.errordist_set.all().delete()
        prior_dists = PriorDist.objects.filter(
                syllabus=user.get_profile().syllabus)
        for prior_dist in prior_dists:
            user_dist = user.errordist_set.create(tag=prior_dist.tag)
            for prior_pdf in prior_dist.density.all():
                user_dist.density.create(
                        pdf=prior_pdf.pdf,
                        cdf=prior_pdf.cdf,
                        condition=prior_pdf.condition,
                        symbol=prior_pdf.symbol,
                        is_correct=prior_pdf.is_correct,
                    )

    def sample(self, condition):
        target_cdf = random.random()
        return self.density.filter(condition=condition,
                cdf__gte=target_cdf).order_by('cdf')[0]

    def get_accuracy(self):
        return mean(o['pdf'] for o in self.density.filter(
                is_correct=True).values('pdf'))

    def get_normalized_accuracy(self):
        prior_accuracy = self.prior_dist.get_accuracy()
        user_accuracy = self.get_accuracy()
        norm_accuracy = (user_accuracy - prior_accuracy) / \
                (1.0 - prior_accuracy)
        return (norm_accuracy > 0.0 and norm_accuracy or 0.0)

    @classmethod
    def from_dist(cls):
        raise Exception('not supported')

class ErrorPdf(util_models.CondProb):
    dist = models.ForeignKey(ErrorDist, related_name='density')
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = (('dist', 'condition', 'symbol'),)
        verbose_name_plural = 'error density'

    @classmethod
    def update(cls, dist, condition, options, selected_option):
        # TODO redistribute mass to the chosen option
        raise Exception('not implemented')

    @classmethod
    def rescore_cdf(cls, dist, condition):
        """Rescores the cdf values after the pdf values have changed."""
        cdf = 0.0
        for density in cls.objects.filter(dist=dist,
                condition=condition).order_by('symbol'):
            cdf += density.pdf
            density.cdf = cdf
            density.save()
        return

    @classmethod
    def sample(cls):
        raise Exception('not supported')

    @classmethod
    def from_dist(cls):
        raise Exception('not supported')

