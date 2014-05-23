#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import pprint as pp

class Agent(object):
    """
    Since each agent may implement a different social learning rule, we need a structure
    to keep track of agents beyond just putting things into the networkx node (although that's
    easily possible too).

    The agent ID should be the same as their networkx node ID (although this is mainly useful for
    debugging and keeping things straight).

    The goal here is to have agents share rule objects to the extent possible, so that we scale
    memory usage more like O(N) than O(2N) or whatever.  So rule code is generic, but can
    refer to parameters that are agent-specific.  The latter are held in a dict called params.

    An example of a parameter might be an agent-specific conformism tendency:  {conformism: 0.1}

    Some rule implementations may not use any parameters whatsoever (e.g., a homogeneous random copying model)
    """

    def __init__(self, simconfig, id):
        self.simconfig = simconfig
        self._id = id
        self._rule = None
        self._traits = None
        self._params = dict()

    @property
    def traits(self):
        return self._traits

    @traits.setter
    def traits(self, t):
        self._traits = t

    @property
    def rule(self):
        return self._rule

    @rule.setter
    def rule(self,r):
        self._rule = r

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self,i):
        self._id = i

    @property
    def params(self):
        return self._params

    def set_param(self,key,value):
        self._params[key] = value


    def __repr__(self):
        rep = 'Agent: ['
        rep += pp.pformat(self._rule)
        rep += ","
        rep += pp.pformat(self._traits)
        rep += ' ]'
        return rep

