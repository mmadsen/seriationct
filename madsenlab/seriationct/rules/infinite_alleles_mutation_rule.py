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
from collections import defaultdict
import random


class InfiniteAllelesMutationRule(object):
    """
    Implements a neutral copying process via Moran dynamics, taking an instance of a lattice model at construction.
    Returns control to the caller after each step(), so that other code can run to determine completion,
    take samples, etc.
    """

    def __init__(self, model):
        self.model = model
        self.sc = self.model.simconfig

        # the highest value used for each locus is initialized to the num_traits, since population initialization
        # does not give out values higher than this.
        self.highest_trait = defaultdict(int)
        for locus in xrange(self.sc.num_features):
            self.highest_trait[locus] = self.sc.num_traits

    def step(self, agent, timestep):
        """
        Implements infinite-alleles mutation for a locus, taking a randomly chosen agent, and giving them
        a new (never before seen) trait at a random locus.

        """

        if npr.random() < self.sc.innovation_rate:
            num_loci = self.sc.num_features
            rand_locus = npr.randint(0,num_loci)
            # create new trait
            self.highest_trait[rand_locus] += 1
            agent.traits[rand_locus] = self.highest_trait[rand_locus]

            # track the interaction and time
            self.model.update_innovations(rand_locus)




