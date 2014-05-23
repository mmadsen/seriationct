#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import madsenlab.seriationct.analysis as analysis
import madsenlab.seriationct.data as data
import logging as log

def sample_mixture_model(model, args, config, timestep):
    tfa = analysis.PopulationTraitFrequencyAnalyzer(model)
    tfa.update()


    data.store_stats_mixture_model(config.popsize,config.sim_id,config.num_features,
                                   config.num_traits,config.sample_size,config.POPULATION_STRUCTURE_CLASS,config.NETWORK_FACTORY_CLASS,
                                   config.TRAIT_FACTORY_CLASS,config.INNOVATION_RULE_CLASS,config.INTERACTION_RULE_CLASS,
                                   config.script,tfa.get_number_configurations(),timestep,tfa.get_unlabeled_configuration_counts(),
                                   config.conformism_strength,config.anticonformism_strength,config.innovation_rate,
                                   tfa.get_slatkin_exact_probability(),tfa.get_trait_evenness_entropy(),
                                   tfa.get_trait_evenness_iqv(),tfa.get_unlabeled_frequency_lists(),tfa.get_unlableled_count_lists(),
                                   tfa.get_configuration_slatkin_test())


