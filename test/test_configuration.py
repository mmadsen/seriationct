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
import os
import tempfile

log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class ConfigurationTest(unittest.TestCase):
    filename = "data/test.json"



    def test_configuration(self):
        log.info("configuration: %s", self.filename)

        config = utils.MixtureConfiguration(self.filename)
        log.info("configured REPLICATIONS_PER_PARAM_SET: %s", config.REPLICATIONS_PER_PARAM_SET)
        self.assertEqual(10, config.REPLICATIONS_PER_PARAM_SET, "Config file value does not match")



    def test_latex_output(self):

        config = utils.MixtureConfiguration(self.filename)
        table = config.to_latex_table("test")

        log.info("%s", table)

    def test_pandoc_output(self):

        config = utils.MixtureConfiguration(self.filename)
        table = config.to_pandoc_table("test")

        log.info("%s", table)


    def test_interaction_rule(self):
        config = utils.MixtureConfiguration(self.filename)
        irule = config.INTERACTION_RULE_CLASS

        prop = irule["madsenlab.seriationct.rules.NeutralCopyingRule"]
        self.assertAlmostEqual(prop, 0.3, None, None, 0.1)



if __name__ == "__main__":
    unittest.main()