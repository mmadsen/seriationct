#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import logging as log
import networkx as nx
import madsenlab.seriationct.utils.configuration
import numpy as np
import math as m
import pprint as pp
import matplotlib.pyplot as plt
from numpy.random import RandomState
from collections import defaultdict

###################################################################################

class BaseGraphPopulation(object):
    """
    Base class for model populations that use a graph (NetworkX) representation to
    store the relations between agents.  Methods here need to be independent of the trait representation,
    but can assume that the agents are nodes in a Graph.  Thus, most of the "agent selection" and
    "neighbor" methods are concentrated here.
    """

    def __init__(self,simconfig,graph_factory,trait_factory):
        self.simconfig = simconfig
        self.interactions = 0
        self.interactions_locus = defaultdict(int)
        self.innovations_locus = defaultdict(int)
        self.innovations = 0
        self.losses = 0
        self.time_step_last_interaction = 0
        self.prng = RandomState()  # allow the library to choose a seed via OS specific mechanism
        self.graph_factory = graph_factory
        self.trait_factory = trait_factory
        self._interaction_rules = None

        # initialize the graph structure via the factory object
        self.agentgraph = self.graph_factory.get_graph()

    @property
    def interaction_rules(self):
        return self._interaction_rules

    @interaction_rules.setter
    def interaction_rules(self,r):
        self._interaction_rules = r


    def get_agent_by_id(self, agent_id):
        return self.agentgraph.node[agent_id]['agent']

    def get_random_agent(self):
        """
        Returns a random agent chosen from the population, in the form of a tuple of two elements
        (node_id, array_of_traits).  This allows operations on the agent and its traits without additional calls.

        To modify the traits, change one or more elements in the array, and then call set_agent_traits(agent_id, new_list)
        """
        rand_agent_id = self.prng.randint(0, self.simconfig.popsize)
        return self.get_agent_by_id(rand_agent_id)

    def get_random_neighbor_for_agent(self, agent_id):
        """
        Returns a random agent chosen from among the neighbors of agent_id.  The format is the same as
        get_random_agent -- a two element tuple with the neighbor's ID and their trait list.
        """
        neighbor_list = self.agentgraph.neighbors(agent_id)
        num_neighbors = len(neighbor_list)
        rand_neighbor_id = neighbor_list[self.prng.randint(0,num_neighbors)]
        return self.get_agent_by_id(rand_neighbor_id)

    def get_all_neighbors_for_agent(self, agent_id):
        agents = self.agentgraph.neighbors(agent_id)
        agent_list = []
        for agent in agents:
            agent_list.append(self.get_agent_by_id(agent))
        return agent_list


    def get_coordination_number(self):
        return self.graph_factory.get_lattice_coordination_number()

    def update_interactions(self, locus, timestep):
        self.interactions += 1
        self.interactions_locus[locus] += 1
        self.time_step_last_interaction = timestep

    def update_innovations(self, locus):
        self.innovations += 1
        self.innovations_locus[locus] += 1

    def update_loss_events(self):
        self.losses += 1

    def get_time_last_interaction(self):
        return self.time_step_last_interaction

    def get_interactions(self):
        return self.interactions

    def get_interactions_by_locus(self):
        return self.interactions_locus.values()

    def get_innovations_by_locus(self):
        return self.innovations_locus.values()

    def get_innovations(self):
        return self.innovations

    def get_losses(self):
        return self.losses

    def initialize_population(self):
        self.trait_factory.initialize_population(self.agentgraph,self._interaction_rules)


    ### Abstract methods - derived classes need to override
    def draw_network_colored_by_culture(self):
        raise NotImplementedError

    def get_traits_packed(self,agent_traits):
        raise NotImplementedError

    def set_agent_traits(self, agent_id, trait_list):
        raise NotImplementedError



###################################################################################

class FixedTraitStructurePopulation(BaseGraphPopulation):
    """
    Base class for models with a fixed number of features and number of traits per feature.
    Specifies no specific graph, lattice, or network model,
    but defines operations usable on any specific model as long as the graph is represented by the
    NetworkX library and API.  Agents are given by nodes, and edges define "neighbors".

    Important operations on a model include choosing a random agent, finding a random neighbor,
    updating an agent's traits, and updating statistics such as the time the last interaction occurred
    (which is used to know when (or if) we've reached a fully absorbing state and can stop.

    """

    def __init__(self, simconfig,graph_factory, trait_factory):
        super(FixedTraitStructurePopulation, self).__init__(simconfig, graph_factory, trait_factory)

    def draw_network_colored_by_culture(self):
        nodes, colors = zip(*nx.get_node_attributes(self.agentgraph, 'traits').items())
        nodes, pos = zip(*nx.get_node_attributes(self.agentgraph, 'pos').items())
        color_tupled_compressed = [int(''.join(str(i) for i in t)) for t in colors]
        nx.draw(self.agentgraph, pos=pos, nodelist=nodes, node_color=color_tupled_compressed)
        plt.show()

    def get_traits_packed(self,agent_traits):
        return ''.join(str(i) for i in agent_traits)


    def set_agent_traits(self, agent_id, trait_list):
        """
        Stores a modified version of the trait list for an agent.
        """
        #old_traits = self.model.node[agent_id]['traits']
        self.agentgraph.node[agent_id]['traits'] = trait_list
        #new_traits = self.model.node[agent_id]['traits']
        #log.debug("setting agent %s: target traits: %s  old: %s new: %s", agent_id, trait_list, old_traits, new_traits)

    def __repr__(self):
        rep = 'FixedTraitStructurePopulation: ['
        for nodename in self.agentgraph.nodes():
            rep += "{node %s: " % nodename
            agent = self.agentgraph.node[nodename]["agent"]
            rep += pp.pformat(agent.traits)
            rep += " rule: %s " % agent.rule
            rep += "},\n"
        rep += ' ]'
        return rep




