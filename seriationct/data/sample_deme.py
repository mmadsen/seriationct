#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

from ming import Session, Field, schema
from ming.declarative import Document
from seriationct.data.dbutils import generate_collection_id


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



#
# def sampleNumAlleles(pop, param):
#     """Samples allele richness for all loci in a replicant population, and stores the richness of the sample in the database.
#
#         Args:
#
#             pop (Population):  simuPOP population replicate.
#
#             params (list):  list of parameters (sample size, mutation rate, population size, simulation ID)
#
#         Returns:
#
#             Boolean true:  all PyOperators need to return true.
#
#     """
#     (ssize, mutation, popsize,sim_id,numloci) = param
#     popID = pop.dvars().rep
#     gen = pop.dvars().gen
#     sample = sampling.drawRandomSample(pop, sizes=ssize)
#     sim.stat(sample, alleleFreq=sim.ALL_AVAIL)
#     for locus in range(numloci):
#         numAlleles = len(sample.dvars().alleleFreq[locus].values())
#         _storeRichnessSample(popID,ssize,numAlleles,locus,gen,mutation,popsize,sim_id)
#     return True
#
#
# def _storeRichnessSample(popID, ssize, richness, locus, generation,mutation,popsize,sim_id):
#     RichnessSample(dict(
#         simulation_time=generation,
#         replication=popID,
#         locus=locus,
#         richness=richness,
#         sample_size=ssize,
#         population_size=popsize,
#         mutation_rate=mutation,
#         simulation_run_id=sim_id
#     )).m.insert()
#     return True


def storeClassFrequencySamples(sim_id, gen, rep, ssize, popsize, mut, sample_list):
    """
    Stores multiple class frequency samples.  The sample list is a list of dicts,
    each of which has the form: {subpop: str, crichness: int, cfreq: dict}
    """
    for sample in sample_list:
        storeClassFrequencySample(sim_id, gen, rep, sample['subpop'], ssize, popsize, mut, sample['crichness'], sample['cfreq'] )

    return True


def storeClassFrequencySample(sim_id, gen, rep, subpop, ssize, popsize, mut, crichness, cfreq):
    ClassFrequencySampleUnaveraged(
        dict(
            simulation_run_id = sim_id,
            simulation_time = gen,
            replication = rep,
            subpop = subpop,
            sample_size = ssize,
            population_size = popsize,
            mutation_rate = mut,
            class_richness = crichness,
            class_freq = cfreq

        )
    ).m.insert()
    return True

class ClassFrequencySampleUnaveraged(Document):


    class __mongometa__:
        session = Session.by_name(_get_dataobj_id())
        name = 'classfreq_sample_unaveraged'

    # metadata and parameters
    _id = Field(schema.ObjectId)
    simulation_run_id = Field(str)
    simulation_time = Field(int)
    replication = Field(int)
    subpop = Field(str)
    sample_size = Field(int)
    population_size = Field(int)
    mutation_rate = Field(float)
    # observables
    class_richness = Field(int)
    class_freq = Field(schema.Anything)




class RichnessSample(Document):

    class __mongometa__:
        session = Session.by_name(_get_dataobj_id())
        name = 'richness_sample'

    _id = Field(schema.ObjectId)
    simulation_time = Field(int)
    replication = Field(int)
    locus = Field(int)
    richness = Field(int)
    sample_size = Field(int)
    population_size = Field(int)
    mutation_rate = Field(float)
    simulation_run_id = Field(str)