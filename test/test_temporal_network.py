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
import simuPOP as sim
import os
import tempfile
import argparse

log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

class TemporalNetworkTest(unittest.TestCase):

    def setUp(self):
        network_model_dir = "data/gmltest"
        self.end_sim = 60

        self.net_model = demo.TemporalNetwork(networkmodel_path=network_model_dir,
                                         simulation_id="19387578394",
                                         sim_length=self.end_sim,
                                         burn_in_time=10,
                                         initial_subpop_size=100
                                         )
        log.info("network model has slices at %s", self.net_model.times)
        log.info("time to slice map: %s", self.net_model.time_to_sliceid_map)
        log.info("slice to time map: %s", self.net_model.sliceid_to_time_map)

    def test_get_sizes(self):

        expected = [100, 100, 100]

        init_population_sizes = self.net_model.get_initial_size()
        log.info("init_pop_sizes: %s", init_population_sizes)
        names = self.net_model.get_subpopulation_names()
        log.info("initial subpop names: %s", names)

        self.assertEqual(init_population_sizes, expected)


    def test_slice_transition(self):
        init_population_sizes = self.net_model.get_initial_size()
        log.info("init_pop_sizes: %s", init_population_sizes)
        names = self.net_model.get_subpopulation_names()
        pop = sim.Population(size = init_population_sizes, subPopNames = names, infoFields=self.net_model.get_info_fields())

        for time in range(1,self.end_sim):
            pop.dvars().gen = time
            self.net_model(pop)
            log.info("time: %s subpop names: %s subpop sizes: %s", time, self.net_model.get_subpopulation_names(), self.net_model.get_subpopulation_sizes())




if __name__ == "__main__":
    unittest.main()