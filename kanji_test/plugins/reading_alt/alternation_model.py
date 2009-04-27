# -*- coding: utf-8 -*-
# 
#  alternation_model.py
#  reading_alt
#  
#  Created by Lars Yencken on 2007-07-05.
#  Copyright 2007-2008 Lars Yencken. All rights reserved.
# 

"An abstract phonetic alternation model."

#----------------------------------------------------------------------------#

import math
from cjktools import kana_table
from cjktools.exceptions import AbstractMethodError

from django.conf import settings

#----------------------------------------------------------------------------#

class AlternationModelI(object):
    """
    An alternation model provides P(r'|r, k), giving both candidates and
    probabilities for r'.
    """
    def prob(kanji, reading, alternation):
        raise AbstractMethodError

    def log_prob(kanji, reading, alternation):
        raise AbstractMethodError

#----------------------------------------------------------------------------#

class SimpleAlternationModel(AlternationModelI):
    """
    An alternation model based on readings which are subsets of things. To
    use, subclass this model and implement the _build_pairs() method.
    """
    #------------------------------------------------------------------------#
    # PUBLIC
    #------------------------------------------------------------------------#

    def __init__(self, alpha):
        self.alpha = alpha
        self.pairs = self._build_pairs()
        mapping = {}
        for keyA, keyB in self.pairs:
            if keyA in mapping:
                mapping[keyA].append(keyB)
            else:
                mapping[keyA] = [keyB]

            if keyB in mapping:
                mapping[keyB].append(keyA)
            else:
                mapping[keyB] = [keyA]

        self.mapping = mapping

    #------------------------------------------------------------------------#

    def log_prob(self, reading, readingVariant):
        """
        Returns the log probability of this variant given the canonical
        reading.
        """
        return math.log(self.prob(reading, readingVariant))

    #------------------------------------------------------------------------#

    def prob(self, reading, readingVariant):
        """
        Returns the probability of the given reading variant being shown
        given the canonical reading.
        """
        uniformProb = 1.0 / self._num_variants(reading)
        if reading == readingVariant:
            return (1-self.alpha) + \
                    self.alpha*uniformProb
        else:
            return self.alpha*uniformProb

    #------------------------------------------------------------------------#

    def candidates(self, kanji, reading):
        """
        Return a list of potential reading variant candidates for this
        model.
        """
        variants = [reading]
        if reading in self.mapping:
            variants.extend(self.mapping[reading])

        results = []
        for readingVariant in variants:
            results.append(
                    (readingVariant, self.log_prob(reading, readingVariant))
                )

        return results

    #------------------------------------------------------------------------#
    # PRIVATE
    #------------------------------------------------------------------------#

    def _build_pairs(self):
        """
        Builds a list of (short form, long form) pairs for this type of
        alternation.
        """
        raise AbstractMethodError

    #------------------------------------------------------------------------#

    def _num_variants(self, reading):
        """
        Returns the number of variants for this particular reading.

        Sometimes calculating this is useful without generating the
        actual candidate list, which might be exponentially large.
        """
        if reading in self.mapping:
            return 1 + len(self.mapping[reading])
        else:
            return 1

    #------------------------------------------------------------------------#

#----------------------------------------------------------------------------#

if not (0 <= settings.VOWEL_LENGTH_ALPHA <= 1):
    raise ValueError('Bad value for vowel length alpha')

class VowelLengthModel(SimpleAlternationModel):
    """
    An alternation model for vowel length.
    """
    def __init__(self):
        SimpleAlternationModel.__init__(self, settings.VOWEL_LENGTH_ALPHA)

    def _build_pairs(self):
        """
        Builds a correspondence between palatalized and unpalatalized forms
        of kana.
        """
        vowel_pairs = {
                u'あ': u'あ',
                u'い': u'い',
                u'う': u'う',
                u'え': u'い',
                u'お': u'う',
            }

        vowel_to_y_form = {
                u'あ':  u'ゃ',
                u'う':  u'ゅ',
                u'お':  u'ょ',
            }

        table = kana_table.KanaTable.get_cached()
        pairs = []
        for consonant in table.consonants:
            if consonant == u'あ':
                # Plain vowels double in Japanese.
                for vowel, long_vowel in vowel_pairs:
                    pairs.append((vowel, 2*vowel))

            else:
                # Other consonants are more limited.
                for vowel, long_vowel in vowel_pairs.iteritems():
                    kana = table.from_coords(consonant, vowel)
                    pairs.append((kana, kana + long_vowel))

                y_prefix = table.from_coords(consonant, u'い')
                assert y_prefix
                for vowel, y_suffix in vowel_to_y_form.iteritems():
                    long_vowel = vowel_pairs[vowel]
                    pairs.append((
                            y_prefix + y_suffix,
                            y_prefix + y_suffix + long_vowel,
                        ))

        return pairs

    #------------------------------------------------------------------------#

    @classmethod
    def get_cached(cls):
        if not hasattr(cls, '_cached'):
            cls._cached = cls()
        return cls._cached

    #------------------------------------------------------------------------#

#----------------------------------------------------------------------------#

class PalatalizationModel(SimpleAlternationModel):
    """
    A probability model of palatalization for Japanese.
    """

    #------------------------------------------------------------------------#

    def __init__(self):
        SimpleAlternationModel.__init__(self, settings.PALATALIZATION_ALPHA)

    #------------------------------------------------------------------------#

    def _build_pairs(self):
        """
        Builds a correspondence between palatalized and unpalatalized forms
        of kana.
        """
        vowel_to_y_form = {
                u'あ':  u'ゃ',
                u'う':  u'ゅ',
                u'お':  u'ょ',
            }

        table = kana_table.KanaTable.get_cached()
        pairs = []
        for consonant in table.consonants:
            i_form = table.from_coords(consonant, u'い')
            for vowel in u'あうお':
                base_form = table.from_coords(consonant, vowel)
                y_form = i_form + vowel_to_y_form[vowel]
                pairs.append((base_form, y_form))

        return pairs

    #------------------------------------------------------------------------#

    @classmethod
    def get_cached(cls):
        if not hasattr(cls, '_cached'):
            cls._cached = cls()
        return cls._cached

    #------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
