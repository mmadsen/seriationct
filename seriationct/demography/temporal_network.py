#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import networkx as nx
import simuPOP as sim

class TemporalNetwork(object):
    """
    TemporalNetwork implements a full "demographic model" in simuPOP terms,
    that is, it manages the size and existence of subpopulations, and the
    migration matrix between them.  The basic data for this model is derived
    by importing a stack of NetworkX graphs in the form of GML format files.
    The stack is ordered by filename, and represents a set of subpopulations
    with unique ID's, and edges between them which are weighted.  The
    weights may be determined by any underlying model (e.g., distance,
    social interaction hierarchy, etc), but need to be interpreted here
    purely as the probability of individuals moving between two subpopulations,
    since that is the implementation of interaction.  When vertices newly appear
    in a network slice, a new subpopulation is formed by splitting an existing one
    to which the new node has an edge.  When vertices go away in a slice, the
    subpopulation is removed from the population.
    """

    def __init__(self, file_list=[], sim_length=0, initial_size=0, info_fields=[]):
        """
        :param file_list: List of full paths to a set of GML files
        :param sim_length: Number of generations to run the simulation
        :param initial_size: List of initial subpopulation sizes for populations present at time 0
        :param info_fields:
        :param ops:
        :return:
        """
        #BaseMetapopulationModel.__init__(self, numGens = sim_length, initSize = initial_size, infoFields = info_fields, ops = ops)
        self.file_list = file_list
        self.sim_length = sim_length
        self.init_size = initial_size
        self.info_fields = info_fields

        # normally this will be inferred from the NetworkX objects
        self.sub_pops = 2




    def get_info_fields(self):
        return self.info_fields

    def get_initial_size(self):
        return self.init_size

    def get_sim_length(self):
        return self.sim_length


    def migrate(self, pop):
        """
        Given the population and a tuple of parameters (importantly, the generation time), returns
        a migration matrix

        :param pop:
        :param param:
        :return:
        """
        #gen = pop.dvars().gen
        sim.migrate(pop, rate=[[0, 0.1], [0.1, 0]])
        return True


    def __call__(self, pop):
        # Call the migrator given the current population structure
        self.migrate(pop)

        # If there is a change to population structure this tick, redo the population sizes
        # for the moment, we just return the same sub population sizes
        return pop.subPopSizes()