# -*- coding: utf-8 -*-
# 
#  raw_reading_model.py
#  reading_alt
#  
#  Created by Lars Yencken on 2007-05-29.
#  Copyright 2007-2008 Lars Yencken. All rights reserved.
#

"A raw reading model, without any normalization."

from os.path import join

from cjktools.common import sopen
from cjktools import scripts
from django.conf import settings

from kanji_test.util.probability import ConditionalFreqDist
from kanji_test.util.alignment import Alignment

_edict_aligned_file = join(settings.DATA_DIR, 'aligned', 'je_edict.aligned.gz')

class RawReadingModel(ConditionalFreqDist):
    """
    A reading model based on exact segment counts, without normalization.
    """

    def __init__(self):
        ConditionalFreqDist.__init__(self)

        kanji_script = scripts.Script.Kanji
        i_stream = sopen(_edict_aligned_file, 'r')
        for line in i_stream:
            alignment = Alignment.from_line(line)
            for (g, p) in alignment:
                if scripts.containsScript(kanji_script, g):
                    self[g].inc(scripts.toHiragana(p))
        i_stream.close()
        return
