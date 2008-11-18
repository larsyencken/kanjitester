# -*- coding: utf-8 -*-
#
#  tests.py
#  kanji_test
# 
#  Created by Lars Yencken on 18-11-2008.
#  Copyright 2008 Lars Yencken. All rights reserved.
#

from django.test import TestCase 
from django.contrib.auth import models as auth_models

from kanji_test.user_model import models

class RegistrationTest(TestCase):
    fixtures = ['test_register']
    def test_registration(self):
        user = auth_models.User.objects.get(username="dummy")
        models.ErrorDist.init_from_priors(user)
        prior_dist = models.PriorDist.objects.get(tag="dummy")
        error_dist = models.ErrorDist.objects.get(user=user, tag="dummy")

        for prior_row in prior_dist.density.all():
            error_row = error_dist.density.get(condition=prior_row.condition,
                    symbol=prior_row.symbol)
            self.assertEqual(prior_row.cdf, error_row.cdf)
            self.assertEqual(prior_row.pdf, error_row.pdf)

class UpdateTest(TestCase):
    fixtures = ['test_update']
    def test_update(self):
        user = auth_models.User.objects.get(username="dummy")
        error_dist = models.ErrorDist.objects.get(user=user, tag="dummy")
        error_dist.update("land", "kangaroo", ["cat", "kangaroo", "koala"])
        self.assertAlmostEqual(error_dist.density.get(condition="land",
                symbol="kangaroo").pdf, 0.36666667)
        self.assertAlmostEqual(error_dist.density.get(condition="land",
                symbol="cat").pdf, 0.25)
        self.assertAlmostEqual(error_dist.density.get(condition="land",
                symbol="koala").pdf, 0.08333333) 
        self.assertAlmostEqual(error_dist.density.get(condition="land",
                symbol="dog").pdf, 0.3) 
        self.assertAlmostEqual(error_dist.density.get(condition="sea",
                symbol="fish").pdf, 1.0) 

# vim: ts=4 sw=4 sts=4 et tw=78:
