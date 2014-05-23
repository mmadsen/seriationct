#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import logging as log

class MoranDynamics(object):

    def __init__(self, config, model, innovation_rule):
        self.config = config
        self.model = model
        self.innovation_rule = innovation_rule
        self._timestep = 0

    @property
    def timestep(self):
        return self._timestep

    def update(self):
        """
        Implements a discrete version of a continuous time model (Moran dynamics)
        by selecting a random agent, and calling the step() method of that agent
        and incrementing the timestep of the model.
        """
        random_agent = self.model.get_random_agent()
        rule = random_agent.rule
        #log.info("entering copying step %s with agent %s", self._timestep, random_agent)
        rule.step(random_agent, self._timestep)

        #log.info("entering mutation rule")
        # choose a different random agent, pass it to the innovation rule and see if it triggers this timestep
        self.innovation_rule.step(self.model.get_random_agent(), self._timestep)

        # increment the time in our dynamics
        self._timestep += 1

