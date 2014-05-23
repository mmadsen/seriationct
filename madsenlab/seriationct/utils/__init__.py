#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
from configuration import MixtureConfiguration
from dynamicloading import load_class, parse_interaction_rule_map, construct_rule_objects
from sampling import sample_mixture_model