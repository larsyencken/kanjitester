# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------#
# testStroke.py
# Lars Yencken <lars.yencken@gmail.com>
# vim: ts=4 sw=4 sts=4 et tw=78:
# Fri Feb 29 12:44:51 2008
#
#----------------------------------------------------------------------------# 

import unittest
from cjktools.resources import kanjidic

import stroke

#----------------------------------------------------------------------------#

def suite():
    testSuite = unittest.TestSuite((
            unittest.makeSuite(StrokeTestCase),
        ))
    return testSuite

#----------------------------------------------------------------------------#

class StrokeTestCase(unittest.TestCase):
    def setUp(self):
        self.dist = stroke.StrokeEditDistance()
        pass

    def testData(self):
        """Verifies the stroke data using kanjidic."""
        kjd = kanjidic.Kanjidic.get_cached()
        signatures = self.dist.signatures
        for kanji, signature in signatures.iteritems():
            actualCount = len(signature)
            expectedCount = kjd[kanji].strokeCount
            assert abs(actualCount - expectedCount) <= 1, \
                "%s has incorrect signature length %d (expected %d)" % \
                (kanji, actualCount, expectedCount)

    def testBasics(self):
        hi = u'日' # 4 strokes
        me = u'目' # 5 strokes
        shiro = u'白' # 5 strokes
        self.assertEqual(0, self.dist.raw_distance(hi, hi))
        self.assertEqual(1, self.dist.raw_distance(hi, me))
        self.assertEqual(1, self.dist.raw_distance(me, hi))
        self.assertEqual(1, self.dist.raw_distance(hi, shiro))
        self.assertEqual(1, self.dist.raw_distance(shiro, hi))
        self.assertEqual(2, self.dist.raw_distance(shiro, me))
        self.assertEqual(2, self.dist.raw_distance(me, shiro))

        self.assertAlmostEqual(0.0, self.dist(hi, hi))
        self.assertAlmostEqual(0.2, self.dist(hi, me))
        self.assertAlmostEqual(0.2, self.dist(me, hi))
        self.assertAlmostEqual(0.2, self.dist(hi, shiro))
        self.assertAlmostEqual(0.2, self.dist(shiro, hi))
        self.assertAlmostEqual(0.4, self.dist(shiro, me))
        self.assertAlmostEqual(0.4, self.dist(me, shiro))
    
    def tearDown(self):
        pass

#----------------------------------------------------------------------------#

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=1).run(suite())

#----------------------------------------------------------------------------#

# vim: ts=4 sw=4 sts=4 et tw=78:

