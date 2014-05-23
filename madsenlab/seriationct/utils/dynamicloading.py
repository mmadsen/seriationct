#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import importlib
import pprint as pp
import logging as log

def load_class(full_class_string):
    """
    dynamically load a class from a string
    """

    class_data = full_class_string.split(".")
    module_path = ".".join(class_data[:-1])
    class_str = class_data[-1]

    module = importlib.import_module(module_path)
    # Finally, we retrieve the Class
    return getattr(module, class_str)



def parse_interaction_rule_map(rawmap):
    """
    Takes a JSON configuration dict, dynamically loads each class and stores it in a list of dicts, one
    for each rule, with the proportion of the population which should have that rule.  An example is as
    follows:

    [ {name: FooRule, class: FooRuleObj, proportion: 0.5}, {name: BarRule, class: BarObj, proportion: 0.5 } ]

    This structure is returned to the caller.
    """
    result = []
    for k,v in rawmap.items():
        block = dict()
        block["name"] = k
        block["proportion"] = v
        block["class"] = load_class(k)
        result.append(block)

    log.debug("result: %s", pp.pformat(result))
    return result

def construct_rule_objects(rulelist, model):
    """
    Given the rule list returned by parse_interaction_rule and a constructed population model,
    this method instantiates each rule class, replacing the original contents of "class".  To be used prior to initializing the
    population, since each agent gets a rule object to work with.  Returns the same rulelist after modification.
    """
    for rule in rulelist:
        list = []
        constructor = rule["class"]
        obj = constructor(model)
        rule["class"] = obj

    return rulelist
