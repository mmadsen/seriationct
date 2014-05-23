#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import networkx as nx
from numpy.random import RandomState
import logging as log
import random as random
import pprint as pp
import madsenlab.seriationct.population as pop
import math

class LocusAlleleTraitFactory(object):
    """
    A trait factory for models where agents have F loci and T possible traits per locus.
    Individuals are initialized with a list of F random integers, each chosen from 0 to T-1.
    The result is given as a Python list, and stored as the individual's initial trait set.

    This factory may be dynamically loaded from its fully qualified name in a configuration file,
     and passed the simulation configuration object in its constructor.  The instantiating
     code then calls initialize_population(graph), passing it a NetworkX graph of nodes, previously
     constructed

    The second argument is a list of interaction rule dicts(), where each dict is the output from
    utils.parse_interaction_rule_map() and utils.construct_rule_objects().  This list will be in the
    form:  [ {name: FooRule, class: FooRuleObj, proportion: 0.5}, {name: BarRule, class: BarObj, proportion: 0.5 } ]
    """

    def __init__(self, simconfig):
        self.simconfig = simconfig
        self.prng = RandomState()  # allow the library to choose a seed via OS specific mechanism

    def initialize_population(self,graph,rule_list):
        nf = self.simconfig.num_features
        nt = self.simconfig.num_traits

        order = graph.number_of_nodes()
        shuffled_rules = self._initialize_random_mixture(order,rule_list)

        id = 0
        for nodename in graph.nodes():
            agent = pop.Agent(self.simconfig,id)
            agent.rule = shuffled_rules[id]
            agent.traits = self.prng.randint(0, nt, size=nf)

            graph.node[nodename]['agent'] = agent
            id += 1




    def _initialize_random_mixture(self,n,rule_list):
        """
        Takes a list of rules and proportions, and returns a shuffled list of rule objects in the correct
        proportions
        """
        obj_list = []
        for rule in rule_list:
            prop = float(rule["proportion"])
            num = int(math.ceil(n * prop))
            log.debug("creating %s obj for rule %s", num, rule["name"])
            for i in xrange(num):
                obj_list.append(rule["class"])

        # check if the result has the right number of entries, it could be off by one, say if the proportions are
        # 0.3, 0.3, 0.3.  Arbitrarily we add an extra of the first rule to break such ties.

        if (len(obj_list) < n):
            log.debug("obj_list size %s vs requested size %s", len(obj_list), n)
            obj_list.append(rule_list[0]["class"])

        random.shuffle(obj_list)
        #log.debug("%s", pp.pformat(obj_list))
        return obj_list
