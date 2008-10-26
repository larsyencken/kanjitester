# -*- coding: utf-8 -*-
# 
#  models.py
#  kanji_test
#  
#  Created by Lars Yencken on 2008-10-24.
#  Copyright 2008 Lars Yencken. All rights reserved.
# 

from django.db import models
from django.contrib.auth.models import User

from kanji_test.lexicon import models as lexicon_models
from kanji_test.util import models as util_models

class Syllabus(models.Model):
    tag = models.CharField(max_length=100, unique=True,
        help_text="A unique name for this syllabus.")
    
    class Meta:
        verbose_name_plural = 'syllabi'
    
    def __unicode__(self):
        return self.tag

class UserProfile(models.Model):
    """Basic model of the user's kanji knowledge and study goals."""
    user = models.ForeignKey(User, unique=True)
    syllabus = models.ForeignKey(Syllabus)

    def __unicode__(self):
        return u"UserProfile for %s" % user.username

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

class PartialKanji(models.Model):
    syllabus = models.ForeignKey(Syllabus)
    kanji = models.ForeignKey(lexicon_models.Kanji,
            help_text='The kanji itself.')
    
    class Meta:
        verbose_name_plural = 'partial kanji'

#----------------------------------------------------------------------------#

class PriorDist(models.Model):
    "A syllabus-specific prior distribution."
    syllabus = models.ForeignKey(Syllabus)
    tag = models.CharField(max_length=100)
    
    class Meta:
        unique_together = (('syllabus', 'tag'),)
        verbose_name = 'prior distribution'
        verbose_name_plural = 'prior distributions'

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

    class Meta:
        unique_together = (('user', 'tag'),)
        verbose_name = 'error distribution'
        verbose_name_plural = 'error distributions'
        
    @classmethod
    def init_from_priors(cls, user):
        """Initialise user copies of prior dists."""
        prior_dists = PriorDist.objects.filter(
                syllabus=user.get_profile().syllabus)
        for prior_dist in prior_dists:
            user_dist = user.errordist_set.create(tag=prior_dist.tag)
            for prior_pdf in prior_dist.density.all():
                user_dist.density.create(pdf=prior_pdf.pdf, cdf=prior_pdf.cdf,
                        is_correct=prior_pdf.is_correct)

    @classmethod
    def sample(cls):
        raise Exception('not supported')

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

