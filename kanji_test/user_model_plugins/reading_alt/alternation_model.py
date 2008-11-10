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

import re, math
from cjktools import kanaTable
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
    An alternation model based on readings which are subsets of things. To use,
    subclass this model and implement the _buildPairs() method.
    """
    #------------------------------------------------------------------------#
    # PUBLIC
    #------------------------------------------------------------------------#

    def __init__(self, alpha):
        self.alpha = alpha
        self.pairs = self._buildPairs()
        map = {}
        for keyA, keyB in self.pairs:
            if keyA in map:
                map[keyA].append(keyB)
            else:
                map[keyA] = [keyB]

            if keyB in map:
                map[keyB].append(keyA)
            else:
                map[keyB] = [keyA]

        self.map = map

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
        uniformProb = 1.0 / self._numVariants(reading)
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
        if reading in self.map:
            variants.extend(self.map[reading])

        results = []
        for readingVariant in variants:
            results.append(
                    (readingVariant, self.log_prob(reading, readingVariant))
                )

        return results

    #------------------------------------------------------------------------#
    # PRIVATE
    #------------------------------------------------------------------------#

    def _buildPairs(self):
        """
        Builds a list of (short form, long form) pairs for this type of
        alternation.
        """
        raise AbstractMethodError

    #------------------------------------------------------------------------#

    def _numVariants(self, reading):
        """
        Returns the number of variants for this particular reading.

        Sometimes calculating this is useful without generating the
        actual candidate list, which might be exponentially large.
        """
        if reading in self.map:
            return 1 + len(self.map[reading])
        else:
            return 1

    #------------------------------------------------------------------------#

#----------------------------------------------------------------------------#

class VowelLengthModel(SimpleAlternationModel):
    """
    An alternation model for vowel length.
    """
    def __init__(self):
        SimpleAlternationModel.__init__(self, settings.VOWEL_LENGTH_ALPHA)

    def _buildPairs(self):
        """
        Builds a correspondence between palatalized and unpalatalized forms
        of kana.
        """
        vowelPairs = {
                u'あ': u'あ',
                u'い': u'い',
                u'う': u'う',
                u'え': u'い',
                u'お': u'う',
            }

        vowelToYForm = {
                u'あ':  u'ゃ',
                u'う':  u'ゅ',
                u'お':  u'ょ',
            }

        table = kanaTable.KanaTable.getCached()
        pairs = []
        for consonant in table.consonants:
            if consonant == u'あ':
                # Plain vowels double in Japanese.
                for vowel, longVowel in vowelPairs:
                    pairs.append((vowel, 2*vowel))

            else:
                # Other consonants are more limited.
                for vowel, longVowel in vowelPairs.iteritems():
                    kana = table.fromCoords(consonant, vowel)
                    pairs.append((kana, kana + longVowel))

                yPrefix = table.fromCoords(consonant, u'い')
                assert yPrefix
                for vowel, y_suffix in vowelToYForm.iteritems():
                    longVowel = vowelPairs[vowel]
                    pairs.append((
                            yPrefix + y_suffix,
                            yPrefix + y_suffix + longVowel,
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

    def _buildPairs(self):
        """
        Builds a correspondence between palatalized and unpalatalized forms
        of kana.
        """
        vowelToYForm = {
                u'あ':  u'ゃ',
                u'う':  u'ゅ',
                u'お':  u'ょ',
            }

        table = kanaTable.KanaTable.getCached()
        pairs = []
        for consonant in table.consonants:
            i_form = table.fromCoords(consonant, u'い')
            for vowel in u'あうお':
                base_form = table.fromCoords(consonant, vowel)
                y_form = i_form + vowelToYForm[vowel]
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
