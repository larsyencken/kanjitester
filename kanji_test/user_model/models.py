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
from django.conf import settings
from cjktools.stats import mean
from cjktools import scripts

from kanji_test.lexicon import models as lexicon_models
from kanji_test.util import models as util_models
from kanji_test.util.probability import ProbDist
from kanji_test.util import alignment

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

    def get_random_items(self, n):
        if n < 1:
            raise ValueError(n)
        n_words = 0
        n_kanji = 0
        word_proportion = self._get_word_proportion()
        for i in xrange(n):
            if random.random() < word_proportion:
                n_words += 1
            else:
                n_kanji += 1

        items = []
        if n_words > 0:
            items.extend(self.partiallexeme_set.order_by('?')[:n_words])

        if n_kanji > 0:
            items.extend(self.partialkanji_set.order_by('?')[:n_kanji])

        return items

    def sample_senses(self, n):
        return lexicon_models.LexemeSense.objects.filter(
                lexeme__partiallexeme__syllabus=self).order_by('?')[:n]

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

    @classmethod
    def validate(cls):
        for syllabus in cls.objects.all():
            kanji_set = set(k.kanji for k in \
                    lexicon_models.Kanji.objects.filter(
                            partialkanji__syllabus=syllabus)
                )
            for partial_lexeme in syllabus.partiallexeme_set.all():
                for lexeme_surface in partial_lexeme.surface_set.all():
                    if not scripts.uniqueKanji(lexeme_surface.surface
                            ).issubset(kanji_set):
                        raise Exception('invalid surface')

class Alignment(models.Model):
    """A segmentation of a lexeme reading."""
    syllabus = models.ForeignKey(Syllabus)
    reading = models.ForeignKey(lexicon_models.LexemeReading)
    surface = models.ForeignKey(lexicon_models.LexemeSurface)
    alignment = models.CharField(max_length=100)

    def alignment_obj(self):
        return alignment.Alignment.from_short_form(self.alignment)
    alignment_obj = property(alignment_obj)

    def __unicode__(self):
        return self.alignment

    class Meta:
        unique_together = (('syllabus', 'reading', 'surface', 'alignment'),)
        verbose_name_plural = 'lexeme reading segments'

class PartialLexeme(models.Model):
    """A subset of an individual lexeme."""
    syllabus = models.ForeignKey(Syllabus)
    lexeme = models.ForeignKey(lexicon_models.Lexeme,
            help_text="The word under consideration.")
    reading_set = models.ManyToManyField(lexicon_models.LexemeReading)
    sense_set = models.ManyToManyField(lexicon_models.LexemeSense)
    surface_set = models.ManyToManyField(lexicon_models.LexemeSurface)

    def alignments(self):
        return Alignment.objects.filter(
                syllabus=self.syllabus,
                reading__in=[o['id'] for o in self.reading_set.all().values(
                        'id')],
                surface__in=[o['id'] for o in self.surface_set.all().values(
                        'id')],
            )
    alignments = property(alignments)
    
    def __unicode__(self):
        return '/'.join(s.surface for s in self.surface_set.all()) + ' ' + \
            '[%s]' % '/'.join(r.reading for r in self.reading_set.all())
        return self.lexeme.surface_set.all()[0].surface

    def has_kanji(self):
        "Does this item have a kanji surface?"
        return self.surface_set.filter(has_kanji=True).count() > 0

    def random_surface(self):
        try:
            return self.surface_set.all().order_by('?')[0].surface
        except IndexError:
            raise ObjectDoesNotExist
    random_surface = property(random_surface)

    def random_reading(self):
        return self.reading_set.order_by('?')[0].reading
    random_reading = property(random_reading)

    def random_kanji_surface(self):
        try:
            return self.surface_set.filter(has_kanji=True).order_by(
                '?')[0].surface
        except IndexError:
            raise ObjectDoesNotExist
    random_kanji_surface = property(random_kanji_surface)

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

    def has_kanji(self):
        "Does this item have a kanji surface? Always."
        return True

    def __unicode__(self):
        return self.kanji.kanji
    
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

    def from_dist(self, dist):
        rows = []
        for condition in dist.keys():
            sub_dist = dist[condition]
            cdf = 0.0
            for symbol in sub_dist.keys():
                pdf = sub_dist[symbol]
                cdf += pdf
                rows.append((self.id, condition, symbol, pdf, cdf))
        cursor = connection.cursor()
        cursor.executemany("""
                INSERT INTO user_model_priorpdf
                (dist, condition, symbol, pdf, cdf)
                VALUES (%s, %s, %s, %s, %s)
        """, rows)
        cursor.execute('COMMIT')
        return

class PriorPdf(util_models.CondProb):
    "Individual densities for a prior distribution."
    dist = models.ForeignKey(PriorDist, related_name='density')

    class Meta:
        unique_together = (('dist', 'condition', 'symbol'),)
        verbose_name_plural = 'prior density'

#----------------------------------------------------------------------------#

class ErrorDist(models.Model):
    "A user-specific prior disribution."
    user = models.ForeignKey(User)
    tag = models.CharField(max_length=100)

    def prior_dist(self):
        return PriorDist.objects.get(tag=self.tag)
    prior_dist = property(prior_dist)

    def differs_from_priors(self):
        priors = self.prior_dist
        diff_map = {}
        for condition in set(o['condition'] for o in 
                self.density.all().values('condition')):
            error_hash = self._error_hash(self.density.filter(
                    condition=condition))
            prior_hash = self._error_hash(priors.density.filter(
                    condition=condition))
            diff_map[condition] = (error_hash == prior_hash)

        return diff_map

    def _error_hash(self, query_set):
        return hash(tuple(o['pdf'] for o in query_set.order_by('symbol'
                ).values('pdf')))
 
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
                    )

    def sample(self, condition):
        return self.density.filter(condition=condition).order_by('?')[0]

    def sample_n(self, condition, n, exclude_set=None):
        dist = ProbDist.from_query_set(self.density.filter(
                condition=condition))
        return dist.sample_n(n, exclude_set=exclude_set)

    def get_normalized_accuracy(self):
        prior_accuracy = self.prior_dist.get_accuracy()
        user_accuracy = self.get_accuracy()
        norm_accuracy = (user_accuracy - prior_accuracy) / \
                (1.0 - prior_accuracy)
        return (norm_accuracy > 0.0 and norm_accuracy or 0.0)

    @classmethod
    def from_dist(cls):
        raise Exception('not supported')

    def update(self, condition, symbol, symbol_set):
        query = self.density.filter(condition=condition)
        whole_dist = ProbDist.from_query_set(query)

        sub_dist = ProbDist.from_query_set(query.filter(symbol__in=symbol_set))
        assert sub_dist
        m = max(v for (s, v) in sub_dist.iteritems() if s != symbol) + \
                settings.UPDATE_EPSILON

        if sub_dist[symbol] >= m:
            # Nothing to say here.
            return

        # Increase the likelihood of seeing the symbol
        sub_dist[symbol] = m
        sub_dist.normalise()

        sub_dist_mass = sum(map(whole_dist.__getitem__, sub_dist.keys()))
        for s in sub_dist:
            whole_dist[s] = sub_dist[s] * sub_dist_mass

        assert abs(sum(whole_dist.values()) - 1.0) < 1e-6
        whole_dist.save_to(self.density, condition=condition)
        return

class ErrorPdf(util_models.CondProb):
    dist = models.ForeignKey(ErrorDist, related_name='density')

    class Meta:
        unique_together = (('dist', 'condition', 'symbol'),)
        verbose_name_plural = 'error density'

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

