#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import logging as log
import pprint as pp
import seriationct.data as data

def sampleNumAlleles(pop, param):
    """Samples allele richness for all loci in a replicant population, and simply logs the richness by subpop and locus.

        Mostly for prototyping purposes...

    """
    import simuPOP as sim
    import simuPOP.sampling as sampling
    (ssize, mutation,popsize,sim_id,numloci) = param
    rep = pop.dvars().rep
    gen = pop.dvars().gen
    subpops = pop.subPopNames()
    for sp_name in subpops:
        sample = sampling.drawRandomSample(pop, subPops=pop.subPopByName(sp_name), sizes=ssize)
        sim.stat(sample, alleleFreq=sim.ALL_AVAIL)
        for locus in range(numloci):
            numAlleles = len(sample.dvars().alleleFreq[locus].values())
            #log.debug("simulation_id: %s gen: %s replicate: %s subpop: %s  ssize: %s locus: %s richness: %s ", sim_id, gen, rep, sp_name,ssize,locus,numAlleles)

    return True



def sampleIndividuals(pop, param):
    import simuPOP as sim
    import simuPOP.sampling as sampling
    (ssize, mutation, popsize, sim_id, num_loci) = param
    popID = pop.dvars().rep
    gen = pop.dvars().gen
    subpops = pop.subPopNames()
    samplelist = []

    for sp_name in subpops:
        sample = sampling.drawRandomSample(pop, subPops=pop.subPopByName(sp_name), sizes=ssize)
        genotype_samples = []
        for idx in range(ssize):
            s = list(sample.individual(idx).genotype())
            genotype_samples.append(s)

        sample = dict(sampletime = gen, subpop=sp_name, replicate = popID, genotype=genotype_samples)
        samplelist.append(sample)

    #log.debug("individual samples: %s", samplelist)

    return True


def sampleAlleleAndGenotypeFrequencies(pop, param):
    import simuPOP as sim
    import simuPOP.sampling as sampling
    (ssize, mutation, popsize, sim_id, num_loci) = param
    popID = pop.dvars().rep
    gen = pop.dvars().gen
    subpops = pop.subPopNames()
    sample_list = list()


    for sp_name in subpops:
        sample = sampling.drawRandomSample(pop, subPops=pop.subPopByName(sp_name), sizes=ssize)
        sim.stat(sample, haploFreq = range(0, num_loci))
        sim.stat(sample, alleleFreq = sim.ALL_AVAIL)

        keys = sample.dvars().haploFreq.keys()
        haplotype_map = sample.dvars().haploFreq[keys[0]]
        num_classes = len(haplotype_map)

        #log.debug("gen: %s replicate: %s subpop: %s numclasses: %s class freq: %s", gen, popID, sp_name, num_classes, haplotype_map)

        #class_freq = {'-'.join(i[0]) : str(i[1]) for i in haplotype_map.items()}
        class_freq = dict()
        for k,v in haplotype_map.items():
            key = '-'.join(str(x) for x in k)
            class_freq[key] = v
        #log.debug("class_freq packed: %s", class_freq)

        sample = dict(subpop = sp_name, crichness = num_classes, cfreq = class_freq)
        sample_list.append(sample)


    data.storeClassFrequencySamples(sim_id,gen,popID,ssize,popsize,mutation,sample_list)
    return True