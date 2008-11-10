# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------#
# test_readingModel.py
# Lars Yencken <lars.yencken@gmail.com>
# vim: ts=4 sw=4 sts=4 et tw=78:
# Mon May 21 17:19:27 2007
#
#----------------------------------------------------------------------------# 

import unittest
from reading_model import *

#----------------------------------------------------------------------------#

def suite():
    testSuite = unittest.TestSuite((
            unittest.makeSuite(KanjiReadingModelTestCase)
        ))
    return testSuite

#----------------------------------------------------------------------------#

class KanjiReadingModelTestCase(unittest.TestCase):
    """
    This class tests the ReadingModel class. 
    """
    def setUp(self):
        self.model = VoicingAndGeminationModel()
        pass

    def testBasicProbability(self):
        g = u'国'
        base_reading = u'こく'
        alternation = u'ごく'

        assert self.model.log_prob(g, base_reading, base_reading) < 0.0
        assert self.model.log_prob(g, base_reading, alternation) < 0.0
        assert self.model.log_prob(g, base_reading, base_reading) > \
                self.model.log_prob(g, base_reading, alternation)

        return

    def testReverseMap(self):
        reverseMap = self.model.get_reverse_mapping()

        assert u'校' in reverseMap[u'こう']
        assert u'高' in reverseMap[u'こう']
        return

    def testCaching(self):
        doppleganger = VoicingAndGeminationModel()

        assert self.model is doppleganger
        return

    def testBug159(self):
        """Tests for bug [159]: hatsu"""
        assert self.model.prob(u'発', u'はつ', u'はっ') > 0.0
        assert u'はっ' in [c[0] for c in self.model.candidates(u'発', u'はつ')]

    def tearDown(self):
        pass

#----------------------------------------------------------------------------#

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())

#----------------------------------------------------------------------------#

# vim: ts=4 sw=4 sts=4 et tw=78:

