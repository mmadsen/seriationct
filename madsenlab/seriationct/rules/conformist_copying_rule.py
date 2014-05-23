#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
This rule implements the original Axelrod model on a lattice, given descriptions in Axelrod (1997) and:

@book{Barrat2009,
    Author = {Barrat, A and Barth\'elemy, M and Vespignani, A},
    Publisher = {Cambridge University Press},
    Title = {Dynamical processes on complex networks},
    Year = {2009}}


"""

import logging as log
import numpy.random as npr
import madsenlab.seriationct.analysis as analysis
from base_rule import BaseInteractionRule
from collections import defaultdict
import random
import numpy.random as npr



class BaseNeighborConformismRule(BaseInteractionRule):
    """
    Implements the common logic for conformist and anticonformist transmission.  If the CONFORMISM_FLAG is
    set to True, then this is pro-conformism, if False, then anticonformism.

    """

    def step(self, agent, timestep):
        """
        Implements a single time step in the neutral drift Moran model, starting from a focal agent,
        and then one of the focal agent's neighbors at random (this rule knows nothing about
        how "neighbors" are represented, so the rule itself is fully generic to many
        population structures, including those with long-distance connections.

        """

        prob = 0

        if npr.random() < self.sc.conformism_strength:
            # execute a local conformism rule among neighbors
                # choose a random locus
            num_loci = self.sc.num_features
            rand_locus = npr.randint(0,num_loci)
            #log.info("conformism - random locus: %s", rand_locus)

            # get the traits from all neighbors at that locus
            neighbors = self.model.get_all_neighbors_for_agent(agent.id)
            trait_cnts = defaultdict(int)
            for neighbor in neighbors:
                ntrait = neighbor.traits[rand_locus]
                trait_cnts[ntrait] += 1
            sorted_cnts = sorted(trait_cnts, reverse=self.CONFORMISM_FLAG)
            #log.debug("sorted traits: %s", sorted_cnts)

            # the most frequent trait will be the first item in the sorted trait list
            selected_trait = sorted_cnts[0]
            #log.debug("selected trait: %s", selected_trait)
            agent.traits[rand_locus] = selected_trait

        else:
            # execute a normal random copy
            neighbor = self.model.get_random_neighbor_for_agent(agent.id)
            num_loci = self.sc.num_features
            rand_locus = npr.randint(0,num_loci)
            #log.info("a/conformism but below rate, copy randomly - random locus: %s", rand_locus)

            neighbor_trait = neighbor.traits[rand_locus]
            agent.traits[rand_locus] = neighbor_trait

        # track the interaction and time
        self.model.update_interactions(rand_locus, timestep)






class ConformistCopyingRule(BaseNeighborConformismRule):
    """
    Implements a neutral copying process via Moran dynamics, taking an instance of a lattice model at construction.
    Returns control to the caller after each step(), so that other code can run to determine completion,
    take samples, etc.
    """

    def __init__(self, model):
        self.model = model
        self.sc = self.model.simconfig
        self.CONFORMISM_FLAG = True




class AntiConformistCopyingRule(BaseNeighborConformismRule):
    """
    Implements a neutral copying process via Moran dynamics, taking an instance of a lattice model at construction.
    Returns control to the caller after each step(), so that other code can run to determine completion,
    take samples, etc.
    """

    def __init__(self, model):
        self.model = model
        self.sc = self.model.simconfig
        self.CONFORMISM_FLAG = False




