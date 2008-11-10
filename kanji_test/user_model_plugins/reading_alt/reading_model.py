# -*- coding: utf-8 -*-
# 
#  reading_model.py
#  reading_alt
#  
#  Created by Lars Yencken on 2007-05-18.
#  Copyright 2007-2008 Lars Yencken. All rights reserved.
# 

"A reading model for FOKS search."

from os.path import join
import math

from django.conf import settings
from cjktools.common import sopen
from cjktools import kanaTable, scripts, smartCache

from kanji_test.util.probability import ConditionalFreqDist
import raw_reading_model

#----------------------------------------------------------------------------#

_reading_counts_file = join(settings.DATA_DIR, 'corpus',
        'kanji_readings__edict')
_reading_counts_map_file = join(settings.DATA_DIR, 'corpus',
        'kanji_readings__edict.map')

#----------------------------------------------------------------------------#

class VoicingAndGeminationModel(object):
    "A reading model giving P(r|k) = aP_freq(r|k) + (1-a)P(r|r*)P(r*|k)."

    def __init__(self):
        # Loads up the frequency distribution for P(r*|k).
        self.normalized_freq_dist = ConditionalFreqDist.from_file(
                _reading_counts_file)

        # Load up the alternation probabilities P(r|r*).
        self.alternation_dist = self._load_alternation_dist(
                _reading_counts_map_file)

        # Build a mapping from (k, r) to r*.
        self.from_canonical_reading = self._build_alternation_map()

        # Build a frequency distribution for P(r|k).
        self.raw_freq_dist = raw_reading_model.RawReadingModel()

        self.reverse_mapping = self.get_reverse_mapping()

        return

    def prob(self, grapheme, reading, alt_reading):
        """
        Returns the probability of P(r|k), using the formula:
        P(r|k) ~ (alpha)P_raw(r|k) + (1-alpha)P(r|r*)P(r*|k).
        """
        if scripts.toHiragana(grapheme) == scripts.toHiragana(alt_reading):
            # Special case: where the segment is phonetic.
            return 1.0

        # We only handle entire kanji segments.
        assert scripts.scriptTypes(grapheme) == set([scripts.Script.Kanji])

        alpha = settings.ALTERNATION_ALPHA
        assert 0 <= alpha <= 1
        try:
            rawProb = self.raw_freq_dist.prob(grapheme, alt_reading)
        except KeyError:
            rawProb = 0.0

        normalizedProb = self.normalized_freq_dist.prob(grapheme, reading)
        alternationProb = self.alternation_dist.prob(reading, alt_reading)

        result = alpha*rawProb + (1-alpha)*normalizedProb*alternationProb

        return result

    def log_prob(self, grapheme, reading, alt_reading):
        return math.log(self.prob(grapheme, reading, alt_reading))

    def candidates(self, grapheme, reading):
        """
        Returns a list of (alt_reading, log_prob) pairs.
        """
        results = []

        key = grapheme, reading

        if key not in self.from_canonical_reading:
            return [(reading, 0.0)]

        for alt_reading in self.from_canonical_reading[key]:
            results.append(
                    (alt_reading, self.log_prob(grapheme, reading, alt_reading))
                )

        return results

    def __repr__(self):
        return '<VoicingAndGeminationModel: %d entries>' % \
                len(self.normalized_freq_dist)

    def get_reverse_mapping(self):
        """
        Generates and returns a map from a reading to the set of possible
        grapheme candidates for that reading.
        """
        reverse_mapping = {}

        # Get the canonical reading pairs.
        for grapheme, reading, count in self.normalized_freq_dist.itercounts():
            if not reverse_mapping.has_key(reading):
                reverse_mapping[reading] = set([grapheme])
            else:
                reverse_mapping[reading].add(grapheme)

        # Get the alternation reading pairs.
        for (grapheme, reading), alt_readings in \
                self.from_canonical_reading.iteritems():
            for alt_reading in alt_readings:
                if not reverse_mapping.has_key(alt_reading):
                    reverse_mapping[alt_reading] = set([grapheme])
                else:
                    reverse_mapping[alt_reading].add(grapheme)

        return reverse_mapping

    def get_valid_reading_set(self):
        """
        Returns a set of readings which are valid for a segment.
        """
        valid_readings = set()
        for alt_readings in self.from_canonical_reading.itervalues():
            valid_readings.update(alt_readings)

        return valid_readings

    #------------------------------------------------------------------------#

    def _load_alternation_dist(self, filename):
        """
        Loads an alternation distribution and returns it. This
        distribution gives P(r|r*).
        """
        alternation_dist = ConditionalFreqDist()
        i_stream = sopen(_reading_counts_map_file, 'r')
        for line in i_stream:
            line = line.rstrip().split()
            kanji = line.pop(0)
            for data in line:
                data = data.split(":")
                if len(data) == 2:
                    reading, count = data
                    count = int(count)
                    alt_reading = reading
                else:
                    reading, alt_reading, count = data
                    count = int(count)

                alternation_dist[reading].inc(alt_reading)

        i_stream.close()
        return alternation_dist
    
    def _build_alternation_map(self):
        """
        Calculates and returns an alternation map, from alternation to
        canonical reading. In other words, it maps (k, r) to r*.
        """
        # Generate an alternation distribution.
        from_canonical_reading = {}
        i_stream = sopen(_reading_counts_map_file, 'r')
        for line in i_stream:
            line = line.rstrip().split()
            kanji = line.pop(0)
            assert line

            for lineSeg in line:
                lineSeg = lineSeg.split(':')
                if len(lineSeg) == 2:
                    reading, count = lineSeg
                    alt_reading = reading
                elif len(lineSeg) == 3:
                    reading, alt_reading, count = lineSeg
                else:
                    raise Exception, "File %s is badly formatted" % \
                            _reading_counts_map_file

                key = (kanji, reading)
                if key in from_canonical_reading:
                    from_canonical_reading[key].add(alt_reading)
                else:
                    from_canonical_reading[key] = set([alt_reading])

        i_stream.close()

        return from_canonical_reading

