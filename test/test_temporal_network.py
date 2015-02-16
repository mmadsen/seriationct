#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import logging as log
import unittest
import seriationct.utils as utils
import seriationct.demography as demo
import os
import tempfile

log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

class ParallelTest(unittest.TestCase):


    def test_calculate_schedule(self):
        network_model_dir = "data/gmltest"

        net_model = demo.TemporalNetwork(networkmodel_path=network_model_dir,
                                         simulation_id="19387578394",
                                         sim_length=3000,
                                         burn_in_time=1000,
                                         initial_subpop_size=100
                                         )

        expected = [100, 100, 100]

        init_population_sizes = net_model.get_initial_size()
        log.info("init_pop_sizes: %s", init_population_sizes)


        self.assertEqual(init_population_sizes, expected)


if __name__ == "__main__":
    unittest.main()