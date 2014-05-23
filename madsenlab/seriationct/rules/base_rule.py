#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

class BaseInteractionRule(object):
    """
    Abstract base class for interaction rules.  Each rule needs to implement step(agent, timestep).
    """


    def __init__(self,simconfig):
        self.simconfig = simconfig

    def step(self, agent, timestep):
        raise NotImplementedError