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


class NeutralCopyingRule(BaseInteractionRule):
    """
    Implements a neutral copying process via Moran dynamics, taking an instance of a lattice model at construction.
    Returns control to the caller after each step(), so that other code can run to determine completion,
    take samples, etc.
    """

    def __init__(self, model):
        self.model = model
        self.sc = self.model.simconfig

    def step(self, agent, timestep):
        """
        Implements a single time step in the neutral drift Moran model, starting from a focal agent,
        and then one of the focal agent's neighbors at random (this rule knows nothing about
        how "neighbors" are represented, so the rule itself is fully generic to many
        population structures, including those with long-distance connections.

        """

        num_loci = self.sc.num_features
        rand_locus = npr.randint(0,num_loci)
        #log.info("neutrality - random locus: %s", rand_locus)

        neighbor = self.model.get_random_neighbor_for_agent(agent.id)
        neighbor_trait = neighbor.traits[rand_locus]
        agent.traits[rand_locus] = neighbor_trait

        # track the interaction and time
        self.model.update_interactions(rand_locus, timestep)




