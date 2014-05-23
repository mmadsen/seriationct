#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import logging as log


#################################################
# overlap calculations


def calc_overlap_locusallele(agent_traits, neighbor_traits):
    """
    Returns the number of features at which two lists overlap (ie., the opposite of what we normally
    calcultion for interaction).
    """
    overlap = 0.0
    for i in range(0, len(agent_traits)):
        if agent_traits[i] == neighbor_traits[i]:
            overlap += 1.0

    return overlap


def calc_overlap_setstructured(agent_traits, neighbor_traits):
    """
    Given sets, the overlap and probabilities are just Jaccard distances or coefficients, which
    are easy in python given symmetric differences and unions between set objects.  This also accounts
    for sets of different length, which is crucial in the extensible and semantic models.
    """
    overlap = len(agent_traits.intersection(neighbor_traits))
    #log.debug("overlap: %s", overlap)
    return overlap


#################################################
# differing trait/features

def get_different_feature_positions_locusallele(agent_traits, neighbor_traits):
    """
    Returns a list of the positions at which two lists of traits differ (but not the differing
    traits themselves).
    """
    features = []
    for i in range(0, len(agent_traits)):
        if agent_traits[i] != neighbor_traits[i]:
            features.append(i)
    #log.debug("differing features: %s", features)
    return features


def get_traits_differing_from_focal_setstructured(focal_traits, neighbor_traits):
    diff = neighbor_traits - focal_traits
    #log.debug("tdfrom focal: %s", diff)
    return diff

