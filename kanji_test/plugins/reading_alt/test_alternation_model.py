# -*- coding: utf-8 -*-
# 
#  test_alternation_model.py
#  reading_alt
#  
#  Created by Lars Yencken on 2007-07-06.
#  Copyright 2007-2008 Lars Yencken. All rights reserved.
# 

import unittest
import doctest
import alternation_model

#----------------------------------------------------------------------------#

def suite():
    testSuite = unittest.TestSuite((
            unittest.makeSuite(VowelLengthTestCase),
            doctest.DocTestSuite(alternation_model)
        ))
    return testSuite

#----------------------------------------------------------------------------#

class VowelLengthTestCase(unittest.TestCase):
    """
    This class tests the AlternationModel class. 
    """
    def setUp(self):
        self.model = alternation_model.VowelLengthModel.get_cached()
        pass

    def test_readings(self):
        pairs = [
                (u'と', u'とう'),
                (u'きょ', u'きょう'),
            ]

        for short_reading, long_reading in pairs:
            assert self.model.map[short_reading] == [long_reading]
            assert self.model.map[long_reading] == [short_reading]
            assert self.model.log_prob(short_reading, long_reading) < 0.0
            assert self.model.log_prob(long_reading, short_reading) < 0.0

    def test_y_sounds(self):
        cs = [c[0] for c in self.model.candidates(None, u'きょう')]
        assert u'ょ' not in cs
        assert u'き' not in cs
        assert set(cs) == set([u'きょう', u'きょ'])

    def tearDown(self):
        pass

#----------------------------------------------------------------------------#

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())

#----------------------------------------------------------------------------#

# vim: ts=4 sw=4 sts=4 et tw=78:

