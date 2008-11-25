# -*- coding: utf-8 -*-
#
#  __init__.py
#  reading_alt
# 
#  Created by Lars Yencken on 09-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

"""
A django app for modelling kanji reading alternations.
"""

import consoleLog
from django.db import connection
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from checksum.models import Checksum
from cjktools import scripts

from kanji_test.user_model import plugin_api as usermodel_api
from kanji_test.user_model import models as usermodel_models
from kanji_test.drill import plugin_api as drill_api
from kanji_test.drill import support
from kanji_test.util.probability import CondProbDist, ProbDist
from kanji_test.lexicon import models as lexicon_models

_log = consoleLog.default

class KanjiReadingModel(usermodel_api.SegmentedSeqPlugin):
    dist_name = 'reading | kanji'

    def __init__(self):
        pass

    def init_priors(self, syllabus, force=False):
        _log.start('Building %s dist' % self.dist_name, nSteps=4)

        # Ensure the reading database is pre-built
        import reading_database
        reading_database.ReadingDatabase.build()

        prior_dist, created = usermodel_models.PriorDist.objects.get_or_create(
                tag=self.dist_name, syllabus=syllabus)
        if not created:
            if force:
                prior_dist.density.all().delete()
            else:
                return

        _log.log('Fetching syllabus kanji')
        kanji_set = self._fetch_syllabus_kanji(syllabus)

        _log.log('Storing readings')
        self._import_readings(prior_dist, kanji_set)

        _log.start('Padding reading lists')
        self._pad_readings(prior_dist)
        _log.finish()

    
        _log.finish()

    #------------------------------------------------------------------------#

    def _fetch_syllabus_kanji(self, syllabus):
        kanji_set = set(row['kanji'] for row in \
                lexicon_models.Kanji.objects.filter(
                    partialkanji__syllabus=syllabus
                ).values('kanji')
            )
        return kanji_set

    def _import_readings(self, prior_dist, kanji_set):
        "Copies the reading database directly into an prior distribution."
        cursor = connection.cursor()
        quote_name = connection.ops.quote_name
        fields_a = ', '.join(map(quote_name, ['dist_id', 'condition',
                'symbol', 'pdf', 'cdf']))
        fields_b = ', '.join(map(quote_name, ['condition', 'symbol', 'pdf',
                'cdf']))
        fields_c = quote_name('condition')
        cursor.execute("""
                INSERT INTO user_model_priorpdf (%s)
                SELECT %s as `dist_id`, %s
                FROM reading_alt_kanjireading
                WHERE %s IN (%s)
            """ % (fields_a, str(prior_dist.id), fields_b, fields_c,
                    u', '.join(u'"%s"' % k for k in kanji_set)))
        cursor.execute('COMMIT')
        return

    def _pad_readings(self, prior_dist):
        """
        Once the reading distribution has been copied over, we still have the
        problem that there may not be enough erroneous readings to meet the
        minimum number of distractors we wish to generate.

        To circumvent this problem, we pad with random distractors.
        """
        _log.log('Padding results ', newLine=False)
        conditions = set(o['condition'] for o in \
                prior_dist.density.all().values('condition'))
        for (condition,) in consoleLog.withProgress(conditions):
            if condition == u'後':
                import pdb; pdb.set_trace()
            exclude_set = set(
                    o.reading for o in \
                    lexicon_models.KanjiReading.objects.filter(
                        kanji__kanji=condition)
                )
            n_stored = prior_dist.density.filter(condition=condition).exclude(
                    symbol__in=exclude_set).count()

            sub_dist = ProbDist.from_query_set(prior_dist.density.filter(
                    condition=condition))
            exclude_set.update(sub_dist.keys())
            n_needed = settings.MIN_TOTAL_DISTRACTORS - n_stored
            min_prob = min(sub_dist.itervalues()) / 2
            while n_needed > 0:
                for row in lexicon_models.KanjiReadingProb.sample_n(n_needed):
                    if row.symbol not in exclude_set:
                        sub_dist[row.symbol] = min_prob
                        exclude_set.add(row.symbol)
                        n_needed -= 1

                    if n_needed == 0:
                        break

            sub_dist.normalise()
            sub_dist.save_to(prior_dist.density, condition=condition)

        return

#----------------------------------------------------------------------------#

class ReadingAlternationQuestions(drill_api.MultipleChoiceFactoryI):
    "An alternation model generates distractor readings."
    question_type = 'pr'
    requires_kanji = True
    supports_kanji = True
    supports_words = True
    uses_dist = 'reading | kanji'

    def get_word_question(self, partial_lexeme, user):
        try:
            surface = partial_lexeme.random_kanji_surface
        except ObjectDoesNotExist:
            raise drill_api.UnsupportedItem(partial_lexeme)

        error_dist = usermodel_models.ErrorDist.objects.get(user=user,
                tag=self.uses_dist)
        exclude_set = set(r.reading for r in 
                partial_lexeme.lexeme.reading_set.all())
        answer = partial_lexeme.reading_set.all().order_by('?')[0]
        answer_reading = answer.reading
        answer_segments = answer.segments.get().segments
        assert answer_reading in exclude_set
        pivot = surface
        question = self.build_question(
                pivot=pivot,
                pivot_id=partial_lexeme.id,
                pivot_type='w',
                stimulus=surface,
            )
        self._add_distractors(question, answer_reading, answer_segments,
                error_dist, exclude_set)
        return question
            
    def get_kanji_question(self, partial_kanji, user):
        error_dist = usermodel_models.ErrorDist.objects.get(user=user,
                tag=self.uses_dist)
        exclude_set = set(row['reading'] for row in \
                partial_kanji.kanji.reading_set.values('reading'))
        answer = partial_kanji.reading_set.order_by('?').values(
                'reading')[0]['reading']
        pivot = partial_kanji.kanji.kanji
        question = self.build_question(
                pivot=pivot,
                pivot_id=partial_kanji.id,
                pivot_type='k',
                stimulus=partial_kanji.kanji.kanji,
            )
        self._add_distractors(question, answer, answer,
                error_dist, exclude_set)
        return question
    
    def _add_distractors(self, question, answer, answer_segments, error_dist,
            exclude_set):
        """
        Builds distractors for the question with appropriate annotations so
        that we can easily update the error model afterwards.   
        """
        assert answer in exclude_set
        distractors, annotation_map = support.build_options(question.pivot,
                self._build_sampler(error_dist), exclude_set)
        annotation_map[answer] = answer_segments
        question.add_options(distractors, answer,
                annotation_map=annotation_map)
        question.annotation = u'|'.join(question.pivot)
        question.save()
        return

    def _build_sampler(self, error_dist):
        def sample(char, n, exclude_set):
            if scripts.scriptType(char) == scripts.Script.Kanji:
                return error_dist.sample_n(char, n, exclude_set=exclude_set)

            if char in exclude_set:
                raise ValueError('unfulfillable request')

            return [char] * n

        return sample

# vim: ts=4 sw=4 sts=4 et tw=78:
