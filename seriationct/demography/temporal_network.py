#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import simuPOP.demography as demo

class TemporalNetwork(demo.DemographicModel):
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

    def __init__(self):
        pass
