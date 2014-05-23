#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
.. module:: simulation_data
    :platform: Unix, Windows
    :synopsis: Data object for storing metadata and parameter about a simulation run in MongoDB, via the Ming ORM.

.. moduleauthor:: Mark E. Madsen <mark@madsenlab.org>

"""

import logging as log
from ming import Session, Field, schema
from ming.declarative import Document
from dbutils import generate_collection_id


__author__ = 'mark'

def _get_dataobj_id():
    """
        Returns the short handle used for this data object in Ming configuration
    """
    return 'simulations'

def _get_collection_id():
    """
    :return: returns the collection name for this data object
    """
    return generate_collection_id("_samples_raw")



def store_stats_mixture_model(popsize,sim_id,nf,nt,sample_size,
                                 popclass,networkclass,
                                 traitclass,innovationclass,interaction_rule,
                                 script,num_configs,sampletime,config_counts,
                                 conformismstrength,anticonformismstrength,
                                 innovation_rate,slatkin,entropy,iqv,
                                 unlabeled_freq, unlabeled_count, conf_slatkin):
    """Stores the parameters and metadata for a simulation run in the database.


    """
    MixtureModelStats(dict(
        simulation_run_id = sim_id,
        sample_time = sampletime,
        script_filename = script,
        interaction_rule_classes = str(interaction_rule),
        pop_class = popclass,
        network_class = networkclass,
        trait_class = traitclass,
        innovation_class = innovationclass,
        num_features = nf,
        init_traits_per_feature = nt,
        conformism_strength = anticonformismstrength,
        innovation_rate = innovation_rate,
        sample_size = sample_size,
        population_size = popsize,
        slatkin_exact = slatkin,
        shannon_entropy = entropy,
        iqv_diversity = iqv,
        num_trait_configurations = num_configs,
        trait_configuration_counts = config_counts,
        unlabeled_frequencies = unlabeled_freq,
        unlabeled_counts = unlabeled_count,
        configuration_slatkin = conf_slatkin,
        )).m.insert()
    return True


class MixtureModelStats(Document):

    class __mongometa__:
        session = Session.by_name(_get_dataobj_id())
        name = 'mixture_model_stats'

    _id = Field(schema.ObjectId)
    simulation_run_id = Field(str)
    sample_time = Field(int)
    script_filename = Field(str)
    interaction_rule_classes = Field(str)
    pop_class = Field(str)
    network_class = Field(str)
    trait_class = Field(str)
    innovation_class = Field(str)
    num_features = Field(int)
    init_traits_per_feature = Field(int)
    conformism_strength = Field(float)
    anticonformism_strength = Field(float)
    innovation_rate = Field(float)
    sample_size = Field(int)
    population_size = Field(int)
    slatkin_exact = Field([float])
    shannon_entropy = Field([float])
    iqv_diversity = Field([float])
    num_trait_configurations = Field(int)
    trait_configuration_counts = Field([])
    unlabeled_frequencies = Field([])
    unlabeled_counts = Field([])
    configuration_slatkin = Field(float)


