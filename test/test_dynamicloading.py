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
import pprint as pp

log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class DynamicLoadingTest(unittest.TestCase):
    filename = "data/test.json"



    def test_parsing_irule(self):
        log.info("configuration: %s", self.filename)

        config = utils.MixtureConfiguration(self.filename)
        irule = config.INTERACTION_RULE_CLASS

        parsed = utils.parse_interaction_rule_map(irule)

        num_rules = len(parsed)
        self.assertEqual(num_rules, 3)

        log.info("parsed: %s", pp.pformat(parsed))




if __name__ == "__main__":
    unittest.main()