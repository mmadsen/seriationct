#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import logging as log
import unittest
import madsenlab.seriationct.utils as utils
import madsenlab.seriationct.traits as traits
import madsenlab.seriationct.population as pop
import os
import tempfile
import pprint as pp


class PopulationInitializationTest(unittest.TestCase):
    filename = "data/test.json"

    def test_shuffled_irules(self):
        log.info("entering test_shuffled_irules")

        config = utils.MixtureConfiguration(self.filename)


        irule = config.INTERACTION_RULE_CLASS
        parsed = utils.parse_interaction_rule_map(irule)

        # skipping the object constructors because we don't need them for this test and we don't
        # have a population handy yet.
        n = 20
        tf = traits.LocusAlleleTraitFactory(config)
        srulelist = tf._initialize_random_mixture(n,parsed)

        log.info("shuffed rule list with %s individuals: %s", n, srulelist)
        self.assertTrue(True)


    def test_full_initialization(self):
        log.info("entering test_full_initialization")
        log.debug("configuration: %s", self.filename)

        config = utils.MixtureConfiguration(self.filename)
        config.popsize = 100
        config.num_features = 2
        config.num_traits = 10
        irule = config.INTERACTION_RULE_CLASS
        parsed = utils.parse_interaction_rule_map(irule)

        tf = traits.LocusAlleleTraitFactory(config)
        lf = pop.SquareLatticeFactory(config)
        p = pop.FixedTraitStructurePopulation(config,lf,tf)

        constructed = utils.construct_rule_objects(parsed,p)
        p.interaction_rules = constructed

        p.initialize_population()

        log.debug("initialized population: %s", p)



if __name__ == "__main__":
    unittest.main()