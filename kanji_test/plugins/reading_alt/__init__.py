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
from checksum.models import Checksum

from kanji_test.user_model import plugin_api as usermodel_api
from kanji_test.user_model import models as usermodel_models
from kanji_test.util.probability import CondProbDist
from kanji_test.lexicon import models as lexicon_models

_log = consoleLog.default

def build():
    import reading_database
    _log.start('Building reading database', nSteps=1)
    reading_database.ReadingDatabase.build()
    _log.finish()

class KanjiReadingModel(usermodel_api.UserModelPlugin):
    dist_name = 'reading | kanji'

    def __init__(self):
        pass

    def init_priors(self, syllabus, force=False):
        import reading_database
        reading_database.ReadingDatabase.build()

        prior_dist, created = usermodel_models.PriorDist.objects.get_or_create(
                tag=self.dist_name, syllabus=syllabus)
        if not created:
            if force:
                prior_dist.density.all().delete()
            else:
                return

        _log.start('Building %s dist' % self.dist_name, nSteps=2)
        from kanji_test.plugins.reading_alt import models
        _log.log('Fetching syllabus kanji')
        kanji_set = set(row['kanji'] for row in \
                lexicon_models.Kanji.objects.filter(
                    partialkanji__syllabus=syllabus
                ).values('kanji')
            )

        _log.log('Storing readings')
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
                        u', '.join(u'"%s"' % k for k in kanji_set)),
            )
        cursor.execute('COMMIT')
        _log.finish()

    def update(self, response):
        # TODO do something
        pass

# vim: ts=4 sw=4 sts=4 et tw=78:
