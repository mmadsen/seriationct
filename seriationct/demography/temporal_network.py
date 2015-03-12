#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import networkx as nx
import numpy as np
import os
import sys
import glob
import re
import math
import simuPOP as sim
from simuPOP.utils import migrIslandRates
import logging as log
import random
import zipfile

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

    def __init__(self,
                 networkmodel_path=None,
                 simulation_id=None,
                 sim_length=0,
                 burn_in_time=0,
                 initial_subpop_size = 0,
                 migrationfraction = 0.2):
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
        self.migration_fraction = migrationfraction

        self.time_to_network_map = {}
        self.time_to_sliceid_map = {}
        self.sliceid_to_time_map = {}
        self.times = []

        self.node_origin_time = dict()
        self.node_exit_time = dict()

        self._cached_migration_matrix = None

        # This will be set when we examine the network model
        self.sub_pops = 0

        self.subpopulation_names = []

        # Parse the GML files and create a list of NetworkX objects
        self._parse_network_model()

        # Determine the order and time of network slices
        self._assign_slice_times()

        # Determine the initial population configuration
        self._calculate_initial_population_configuration()

        # prime the migration matrix
        self._cached_migration_matrix = self._calculate_migration_matrix(min(self.times))

    ############### Private Initialization Methods ###############

    def _parse_network_model(self):
        """
        Given a directory, sequentially read GML files with a naming spec <name>-<integer>.gml
        and construct a sequence of NetworkX graphs from the GML files
        """
        self.network_slices = dict()

        # file_list = []
        # for file in os.listdir(self.network_path):
        #     if file.endswith(".gml"):
        #         file_list.append(file)
        #
        # log.debug("file list: %s", file_list)
        #
        # for filename in file_list:
        #     m = re.search('(?!\-)(\d+)\.gml', filename)
        #     file_number = m.group(1)
        #     log.debug("Parsing GML file %s:  file number %s", filename, file_number)
        #     full_fname = self.network_path + "/" + filename
        #     slice = nx.read_gml(full_fname, relabel=False)
        #     self.network_slices[file_number] = slice


        zf = zipfile.ZipFile(self.network_path, 'r')

        for file in [f for f in zf.namelist() if f.endswith(".gml")]:
            m = re.search('(?!\-)(\d+)\.gml', file)
            file_number = m.group(1)
            log.debug("Parsing GML file %s:  file number %s", file, file_number)

            gml = zf.read(file)
            slice = nx.parse_gml(gml)
            #log.debug("slice nodes: %s", '|'.join(sorted(slice.nodes())))
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
        for slice_id in sorted(self.network_slices.keys()):
            slice = self.network_slices[slice_id]
            self.time_to_network_map[slice_time] = slice
            self.time_to_sliceid_map[slice_time] = slice_id
            self.sliceid_to_time_map[slice_id] = slice_time
            self.times.append(slice_time)
            # advance the time by the slice interval
            slice_time += self.slice_interval


        #log.debug("Map of slice_id to time: %s", self.sliceid_to_time_map)


    def _calculate_initial_population_configuration(self):
        # num subpops is just the number of vertices in the first graph slice.
        first_time = min(self.times)
        first_slice = self.time_to_network_map[first_time]
        self.sub_pops = first_slice.number_of_nodes()
        #log.debug("Number of initial subpopulations: %s", self.sub_pops)

        # subpoplation names - have to switch them to plain strings from unicode or simuPOP won't use them as subpop names
        self.subpopulation_names =  [d["label"].encode('utf-8', 'ignore') for n,d in first_slice.nodes_iter(data=True)]
        #log.debug("calc_init_config:  subpopulation names: %s", self.subpopulation_names)


    ############### Private Methods for Call() Interface ###############




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

        #log.debug("time: %s sid cur: %s  sid prev: %s", time, sid_cur, sid_prev)

        g_cur = self.time_to_network_map[self.sliceid_to_time_map[sid_cur]]
        g_prev = self.time_to_network_map[self.sliceid_to_time_map[sid_prev]]

        nodes_cur = g_cur.nodes()
        nodes_prev = g_prev.nodes()

        #log.debug("nodes_cur: %s", nodes_cur)
        #log.debug("nodes_prev: %s", nodes_prev)

        node_labels_cur = [id.encode('utf-8', 'ignore') for id in nodes_cur]
        node_labels_prev = [id.encode('utf-8', 'ignore') for id in nodes_prev]


        added_subpops = list(set(node_labels_cur)-set(node_labels_prev))
        deleted_subpops = list(set(node_labels_prev)-set(node_labels_cur))


        # now do tracking of origin and exit times for assemblage durations
        for sp in added_subpops:
            self.node_origin_time[sp] = time

        for sp in deleted_subpops:
            self.node_exit_time[sp] = time

        return (added_subpops, deleted_subpops)


    def _get_node_label(self,g, id):
        return g.node[id]["label"].encode('utf-8', 'ignore')


    def _get_sliceid_for_time(self, time):
        """
        Returns networkx Graph object for the state of the temporal network at the specified time
        :param time:
        :return: Graph object
        """
        index = None

        # Case 1:  does time == one of the actual change points?
        if time in self.times:
            #log.debug("time %s is time of actual slice", time)
            return self.time_to_sliceid_map[time]

        # Case 2:  does time < the smallest of the change point times?
        if time <= min(self.times):
            return min(self.times)

        # Case 3:  does time > the largest of the change point times?
        if time > max(self.times):
            return max(self.times)

        # Case 3:  does time fit between a pair of the change points?
        first = 0
        second = 1
        length = len(self.times)

        while(length > 0):
            if self.times[first] <= time <= self.times[second]:
                index = self.times[first]
                #log.debug("(%s <= %s <= %s)", self.times[first], time, self.times[second])
                break
            first += 1
            second += 1

        return self.time_to_sliceid_map[index]

    def _get_previous_sliceid_for_time(self, time):
        """
        Returns networkx Graph object for the state of the temporal network just prior to the
        specified time.  This is useful in conjunction with _get_slice_for_time to calculate
        the added and deleted vertices at a given time index.
        :param time:
        :return: Graph object
        """
        current_sliceid = self._get_sliceid_for_time(time)

        #log.debug("current sliceid: %s", current_sliceid)

        # handle the case where we're on the first slice
        if current_sliceid == '1':
            sliceid = '1'
        else:
            sliceid = str(int(current_sliceid) - 1)

        #log.debug("previous slice id for requested time %s is: %s", time, sliceid)
        return sliceid


    # def _get_origin_subpop_for_new_subpopulation(self,time,pop,newpop):
    #     """
    #     Given the name/label of a new subpopulation, this finds the networkx node id
    #     of the parent subpopulation,
    #     """
    #     g_cur = self.time_to_network_map[self.sliceid_to_time_map[self._get_sliceid_for_time(time)]]
    #     g_prev = self.time_to_network_map[self.sliceid_to_time_map[self._get_previous_sliceid_for_time(time)]]
    #     newpop_nodeid = None
    #
    #     for n,d in g_cur.nodes_iter(data=True):
    #         if d["label"] == newpop:
    #             newpop_nodeid = n
    #
    #     newpop_neighbors = g_cur.neighbors(newpop_nodeid)
    #     preexisting_neighbors = []
    #     for n in newpop_neighbors:
    #         if n in g_prev:
    #             preexisting_neighbors.append(self._get_node_label(g_prev,n))
    #
    #     #log.debug("neighbors for new subpop %s: %s pre-existing neighbors: %s", newpop, newpop_neighbors, preexisting_neighbors)
    #
    #     random_neighbor_label = random.choice(preexisting_neighbors)
    #     random_neighbor_id = pop.subPopByName(random_neighbor_label)
    #     return (random_neighbor_id, random_neighbor_label)


    def _get_origin_subpop_for_new_subpopulation(self,time,pop,newpop_name):
        """
        Given the name/label of a new subpopulation, query the "parent" attribute of the node to determine the
        parent subpopulation which needs to be split to form this new subpopulation.
        """
        g_cur = self.time_to_network_map[self.sliceid_to_time_map[self._get_sliceid_for_time(time)]]

        parent_name = self._get_node_parent(g_cur,newpop_name)
        parent_name = parent_name.encode('utf-8', 'ignore')
        parent_id = pop.subPopByName(parent_name)

        #log.debug("parent of %s is %s, id = %s", newpop_name,parent_name,parent_id)

        return (parent_id, parent_name)







    def _get_id_for_subpop_name(self,pop,name):
        return pop.subPopByName(name)

    def _get_node_parent(self,g, id):
        return g.node[id]["parent_node"].encode('utf-8', 'ignore')


    def _get_subpop_idname_map(self, pop):
        names = pop.subPopNames()
        name_id_map = dict()
        for name in names:
            id = pop.subPopByName(name)
            name_id_map[id] = name
        return name_id_map


    def _calculate_migration_matrix(self, time):
        g_cur = self.time_to_network_map[self.sliceid_to_time_map[self._get_sliceid_for_time(time)]]
        g_mat = nx.to_numpy_matrix(g_cur)

        # get the column totals
        rtot = np.sum(g_mat, axis = 1)
        scaled = (g_mat / rtot) * self.migration_fraction
        diag = np.eye(np.shape(g_mat)[0]) * (1.0 - self.migration_fraction)
        g_mat_scaled = diag + scaled

        return g_mat_scaled.tolist()



    ###################### Debug Methods ##################

    def _dbg_slice_pop_start(self,pop,time):
        """
        Debug method for comparing the assemblages in a network model slice versus the simuPOP population.
        """
        g_prev = self.time_to_network_map[self.sliceid_to_time_map[self._get_previous_sliceid_for_time(time)]]
        slice_str = '|'.join(sorted(g_prev.nodes()))
        pop_str = '|'.join(sorted(pop.subPopNames()))
        log.debug("start slice: %s", slice_str)
        log.debug("start smpop: %s", pop_str)


    def _dbg_slice_pop_end(self,pop,time):
        """
        Debug method for comparing the assemblages in a network model slice versus the simuPOP population.
        """
        g_cur = self.time_to_network_map[self.sliceid_to_time_map[self._get_sliceid_for_time(time)]]
        slice_str = '|'.join(sorted(g_cur.nodes()))
        pop_str = '|'.join(sorted(pop.subPopNames()))
        log.debug("end slice: %s", slice_str)
        log.debug("end smpop: %s", pop_str)



    ###################### Public API #####################

    def is_change_time(self, gen):
        return gen in self.times

    def get_info_fields(self):
        return self.info_fields

    def get_initial_size(self):
        return [self.init_subpop_size] * self.sub_pops

    def get_subpopulation_names(self):
        return self.subpopulation_names

    def get_subpopulation_sizes(self):
        return self.subpop_sizes

    def get_subpopulation_durations(self):
        """
        Returns a map with subpopulation name as key, and duration as value.  Burn-in time is NOT
        included in the duration, so the durations are relative to the simlength - burnin.
        """
        duration = dict()
        for sp in self.node_exit_time:
            duration[sp] = int(self.node_exit_time[sp]) - int(self.node_origin_time[sp])
            #log.debug("duration sp %s: %s - from %s to %s", sp, duration[sp], self.node_origin_time[sp], self.node_exit_time[sp])
        return duration

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
        if 'gen' not in pop.vars():
            gen = 0
        else:
            gen = pop.dvars().gen


        # At the first time slice, start tracking duration for assemblages that exist at min(self.times)
        # which is also the end of the burn-in time
        # After this point, further changes are recorded as nodes are added/deleted
        if gen == min(self.times):
            starting_subpops = pop.subPopNames()
            for subpop in starting_subpops:
                self.node_origin_time[subpop] = min(self.times)

        # At the very end of the simulation, after the last slice time, we finish off the
        # duration times of assemblages that exist at sim_length.
        if gen == self.sim_length:
            ending_subpops = pop.subPopNames()
            for subpop in ending_subpops:
                self.node_exit_time[subpop] = self.sim_length


        ######### Do the per tick processing ##########

        if self.is_change_time(gen) == False:
            pass
        else:
            slice_for_time = self.time_to_sliceid_map[gen]
            log.debug("========= Processing network slice %s at time %s =============", slice_for_time, gen)
            #self._dbg_slice_pop_start(pop,gen)


            # switch to a new network slice, first handling added and deleted subpops
            # then calculate a new migration matrix
            # then migrate according to the new matrix
            (added_subpops, deleted_subpops) = self._get_added_deleted_subpops_for_time(gen)

            # add new subpopulations
            #log.debug("time %s adding subpops: %s", gen, added_subpops)
            for sp in added_subpops:
                (origin_sp, origin_sp_name) = self._get_origin_subpop_for_new_subpopulation(gen,pop,sp)

                log.debug("time %s new node: %s parent id: %s  parent name: %s", gen, sp, origin_sp, origin_sp_name)

                sp_names = [origin_sp_name, sp]
                #log.debug("spnames: %s", sp_names)
                split_ids = pop.splitSubPop(origin_sp, [0.5, 0.5], sp_names)
                #log.debug("split return: %s", split_ids)
                # make sure all subpopulations are the same size, sampling from existing individuals with replacement
                numpops = pop.numSubPop()
                sizes = [self.init_subpop_size] * numpops
                pop.resize(sizes, propagate=True)

            # delete subpopulations
            #log.debug("time %s deleting subpops: %s", gen, deleted_subpops)
            for sp in deleted_subpops:
                #log.debug("pops: %s", pop.subPopNames())
                log.debug("time %s deleted subpop: %s", gen, sp)
                pop.removeSubPops(pop.subPopByName(sp))

            # update the migration matrix
            self._cached_migration_matrix = self._calculate_migration_matrix(gen)

            #self._dbg_slice_pop_end(pop,gen)


        sim.migrate(pop, self._cached_migration_matrix)
        sim.stat(pop, popSize=True)
        # cache the new subpopulation names and sizes for debug and logging purposes
        # before returning them to the calling function
        self.subpopulation_names = sorted(pop.subPopNames())
        self.subpop_sizes = pop.subPopSizes()
        return pop.subPopSizes()

