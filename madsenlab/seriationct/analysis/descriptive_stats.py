#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import logging as log
from collections import defaultdict
import slatkin
import numpy as np
import math as m
import pprint as pp





## GOOD BELOW HERE


def slatkin_exact_test(count_list):
    (prob, theta) = slatkin.montecarlo(100000, count_list, len(count_list))
    #log.debug("slatkin prob: %s  theta: %s", prob, theta)
    return prob


def diversity_shannon_entropy(freq_list):
    k = len(freq_list)
    sw = 0.0
    for i in range(0, k):
        sw += freq_list[i] * m.log(freq_list[i])
    if sw == 0:
        return 0.0
    else:
        return sw * -1.0


def diversity_iqv(freq_list):
    k = len(freq_list)

    if k <= 1:
        return 0.0

    isum = 1.0 - _sum_squares(freq_list)
    factor = float(k) / (float(k) - 1.0)
    iqv = factor * isum

    #logger.debug("k: %s  isum: %s  factor: %s  iqv:  %s", k, isum, factor, iqv)
    return iqv


def _sum_squares(freq_list):
    ss = 0.0
    for p in freq_list:
        ss += p ** 2.0
    return ss


class PopulationTraitFrequencyAnalyzer(object):
    """
    Analyzer for trait frequencies across the entire population.  At each
    call to calculate_trait_frequencies(), the analyzer looks at the state
    of the agent population and stores frequencies.  Subsequent calls to
    get methods will return frequencies, richness, or the Shannon entropy
    measure of evenness for the frequencies.

    To use this over time, call calculate_trait_frequencies() when you
    want a sample, and then the various get_* methods to return the
    desired metrics.

    """

    def __init__(self, model):
        self.model = model
        self.total_traits = model.agentgraph.number_of_nodes()

    def get_trait_frequencies(self):
        return self.freq

    def get_trait_frequencies_dbformat(self):
        # transform into the list of dicts that's more convenient to stuff into mongodb
        db_freq = []
        for locus in self.freq:
            l = []
            for key,val in locus.items():
                l.append(dict(trait=str(key),freq=val))
            db_freq.append(l)
        #log.debug("counts: %s", stored_counts)
        return db_freq

    def get_trait_richness(self):
        """
        Returns the number of traits with non-zero frequencies
        """
        richness = []
        for locus in self.freq:
            richness.append(len([freq for freq in locus.values() if freq > 0]))
        return richness

    def get_trait_evenness_entropy(self):
        entropy = []
        for locus in self.freq:
            entropy.append(diversity_shannon_entropy(locus.values()))
        return entropy

    def get_trait_evenness_iqv(self):
        iqv = []
        for locus in self.freq:
            iqv.append(diversity_iqv(locus.values()))
        return iqv

    def get_slatkin_exact_probability(self):
        slatkin = []
        for locus in self.counts:
            cnt = sorted(locus.values(), reverse=True)
            #log.info("cnt: %s", cnt)
            slatkin.append(slatkin_exact_test(cnt))
        return slatkin

    def get_unlabeled_frequency_lists(self):
        f = []

        for locus in self.freq:
            f.append(sorted(locus.values(), reverse=True))
        #log.debug("unlab freq: %s", f)
        return f

    def get_unlabeled_configuration_counts(self):
        counts = sorted(self.culture_counts.values(), reverse=True)
        #log.debug("configuration counts: %s", counts)

        return counts

    def get_number_configurations(self):
        return len(self.culture_counts)

    def get_unlableled_count_lists(self):
        f = []

        for locus in self.counts:
            f.append(sorted(locus.values(), reverse=True))
        #log.debug("unlab count: %s", f)
        return f

    def get_configuration_slatkin_test(self):
        config = self.get_unlabeled_configuration_counts()
        return slatkin_exact_test(config)

    def update(self):
        self.freq = None
        nf = self.model.simconfig.num_features
        #spectra = dict()  # spectra will be locus as key, value will be dicts of popcount, numtraits
        self.counts = []  # counts will be locus as index to list, each list position is dict with key=trait, value=count
        self.freq = []  # frequencies will be locus as index to list, each list position is dict with key=trait, value=freq
        self.culture_counts = defaultdict(int)

        for i in xrange(0, nf):
            self.counts.append(defaultdict(int))
            self.freq.append(defaultdict(int))

        total = self.model.agentgraph.number_of_nodes()

        for agent_id in self.model.agentgraph.nodes():
            agent_traits = self.model.agentgraph.node[agent_id]['agent'].traits
            culture = self.model.get_traits_packed(agent_traits)
            self.culture_counts[culture] += 1
            for i in xrange(0, nf):
                self.counts[i][agent_traits[i]] += 1

        for i in xrange(0, nf):
            cnt = self.counts[i]
            for trait,count in cnt.items():
                self.freq[i][trait] = float(count) / float(total)









