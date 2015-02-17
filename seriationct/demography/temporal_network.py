#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import networkx as nx
import os
import sys
import glob
import re
import math
import simuPOP as sim
import logging as log

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

    def __init__(self, networkmodel_path=None, simulation_id=None, sim_length=0, burn_in_time=0, initial_subpop_size = 0):
        """
        :param networkmodel_path: List of full paths to a set of GML files
        :param sim_length: Number of generations to run the simulation
        :return:
        """
        #BaseMetapopulationModel.__init__(self, numGens = sim_length, initSize = initial_size, infoFields = info_fields, ops = ops)
        self.network_path = networkmodel_path
        self.sim_length = sim_length
        self.info_fields = 'migrate_to'
        self.sim_id = simulation_id
        self.burn_in_time = burn_in_time
        self.init_subpop_size = initial_subpop_size

        self.time_to_network_map = {}
        self.time_to_sliceid_map = {}
        self.sliceid_to_time_map = {}
        self.times = []

        # This will be set when we examine the network model
        self.sub_pops = 0

        self.subpopulation_names = []

        # Parse the GML files and create a list of NetworkX objects
        self._parse_network_model()

        # Determine the order and time of network slices
        self._assign_slice_times()

        # Determine the initial population configuration
        self._calculate_initial_population_configuration()

    ############### Private Initialization Methods ###############

    def _parse_network_model(self):
        """
        Given a directory, sequentially read GML files with a naming spec <name>-<integer>.gml
        and construct a sequence of NetworkX graphs from the GML files
        """
        self.network_slices = dict()

        try:
            os.chdir(self.network_path)
        except:
            log.error("Cannot change directories to %s, exiting simulation run %s", self.network_path, self.sim_id)
            sys.exit(1)

        file_list = glob.glob("*.gml")

        for filename in file_list:
            m = re.match('\w+\-(\d+)\.gml', filename)
            file_number = m.group(1)
            log.debug("Parsing GML file %s:  file %s", filename, file_number)

            slice = nx.read_gml(filename, relabel=False)
            self.network_slices[file_number] = slice

    def _assign_slice_times(self):
        """
        Calculates the times at which each network slice is applied.  At the moment, slices are
        applied evenly after burnin is removed.
        """
        sampled_time = self.sim_length - self.burn_in_time
        log.debug("Evolution occurs over %s generations after %s generations burn-in time", sampled_time, self.burn_in_time)
        self.slice_interval = int(math.ceil(sampled_time / len(self.network_slices)))
        log.debug("Slices will be applied at intervals of %s generations", self.slice_interval)

        # assign each slice to a starting generation, starting once burn in time has elapsed
        slice_time = self.burn_in_time
        for slice_id, slice in self.network_slices.items():
            self.time_to_network_map[slice_time] = slice
            self.time_to_sliceid_map[slice_time] = slice_id
            self.sliceid_to_time_map[slice_id] = slice_time
            self.times.append(slice_time)
            # advance the time by the slice interval
            slice_time += self.slice_interval


        log.debug("Map of slice_id to time: %s", self.sliceid_to_time_map)


    def _calculate_initial_population_configuration(self):
        # num subpops is just the number of vertices in the first graph slice.
        first_time = min(self.times)
        first_slice = self.time_to_network_map[first_time]
        self.sub_pops = first_slice.number_of_nodes()
        log.debug("Number of initial subpopulations: %s", self.sub_pops)

        # subpoplation names
        self.subpopulation_names =  [d["label"] for n,d in first_slice.nodes_iter(data=True)]
        log.debug("subpouplation names: %s", self.subpopulation_names)


    ############### Private Methods for Call() Interface ###############

    def _is_change_time(self, gen):
        return gen in self.time_to_network_map


    def _get_added_deleted_subpops_for_time(self, time):
        """
        Using the slice relevant to a time index, and the previous network slice,
        calculates the nodes added in the current slice, and deleted from the previous
        slice.  These lists are given as "label" attributes since these uniquely
        identify subpopulations in the simuPOP framework (the subpopulation ID's can
        change).

        The two lists are returned as a two member tuple with the addition list first,
        and the deletion list second.

        """
        sid_cur = self._get_sliceid_for_time(time)
        sid_prev = self._get_previous_sliceid_for_time(time)

        g_cur = self.time_to_network_map[self.sliceid_to_time_map[sid_cur]]
        g_prev = self.time_to_network_map[self.sliceid_to_time_map[sid_prev]]

        nodes_cur = g_cur.nodes()
        nodes_prev = g_prev.nodes()

        added_subpops = [self._get_node_label(g_cur, id) for id in list(set(nodes_cur)-set(nodes_prev))]
        deleted_subpops = [self._get_node_label(g_prev, id) for id in list(set(nodes_prev)-set(nodes_cur))]

        log.debug("time: %s add subpop: %s", time, added_subpops)
        log.debug("time: %s del subpop: %s", time, deleted_subpops)

        return (added_subpops, deleted_subpops)


    def _get_node_label(self,g, id):
        return g.node[id]["label"]


    def _get_sliceid_for_time(self, time):
        """
        Returns networkx Graph object for the state of the temporal network at the specified time
        :param time:
        :return: Graph object
        """
        index = None

        for t in self.times:
            if time > t:
                index = t
            elif time <= t and index != None:
                break
            else:
                continue

        # handle the zero equality case
        if time == 0:
            index = min(self.times)

        sliceid = self.time_to_sliceid_map[time]

        log.debug("slice id for requested time %s is: %s", time, sliceid)

        return sliceid

    def _get_previous_sliceid_for_time(self, time):
        """
        Returns networkx Graph object for the state of the temporal network just prior to the
        specified time.  This is useful in conjunction with _get_slice_for_time to calculate
        the added and deleted vertices at a given time index.
        :param time:
        :return: Graph object
        """
        current_sliceid = self._get_sliceid_for_time(time)

        # handle the case where we're on the first slice
        if current_sliceid == 1:
            sliceid = 1
        else:
            sliceid = current_sliceid - 1

        log.debug("previous slice id for requested time %s is: %s", time, sliceid)

    def _get_updated_migration_matrix_for_time(self, time):
        pass


    ###################### Public API #####################


    def get_info_fields(self):
        return self.info_fields

    def get_initial_size(self):
        return [self.init_subpop_size] * self.sub_pops

    def get_subpopulation_names(self):
        return self.subpopulation_names



    def __call__(self, pop):
        """
        Main public interface to this demography model.  When the model object is called in every time step,
        this method determines whether a new network slice is now active.  If so, the requisite changes
        to subpopulations are made (adding/deleting subpopulations), and then the new migration matrix is
        applied.

        After migration, the stat function is called to inventory the subpopulation sizes, which are then
        returned since they're handed to the RandomSelection mating operator.

        If a new network slice is not active, the migration matrix from the previous step is applied again,
        and the new subpopulation sizes are returns to the RandomSelection mating operator as before.

        :return: A list of the subpopulation sizes for each subpopulation
        """
        gen = pop.dvars().gen
        if(self._is_change_time(gen)):
            pass
        else:
            # switch to a new network slice, first handling added and deleted subpops
            # then calculate a new migration matrix
            # then migrate according to the new matrix
            (added_subpops, deleted_subpops) = self._get_added_deleted_subpops_for_time(gen)

            # delete subpopulations

            # add new subpopulations

            # update the migration matrix
            self._cached_migration_matrix = self._get_updated_migration_matrix_for_time(gen)

        # execute migration and then return the new subpopulation sizes to the mating operator
        sim.migrate(pop, self._cached_migration_matrix)
        sim.stat(pop, popSize=True)
        return pop.subPopSizes()

