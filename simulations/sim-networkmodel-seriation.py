#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
the purpose here is to run the tree structured model for a fixed length of time, with innovation_rateation, and see what
happens to the structure of trait trees, sampled at fixed intervals.  We will leave in homophily, but ignore
convergence since it should be temporary with innovation_rateation/noise.

"""

import logging as log
from time import time
import math

import argparse
import ctpy.utils as ctu
import pytransmission.popgen as pypopgen
import simuOpt

import seriationct as sct
import seriationct.data as data
import seriationct.sampling as sampling
import seriationct.utils as utils

simuOpt.setOptions(alleleType='long', optimized=True, quiet=False, numThreads=utils.get_parallel_cores(dev_flag=True))

global config, sim_id, script



def main():
    MAXALLELES = 10000000

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--devel", help="Use only half of the available CPU cores", type=int, default=1)
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--reps", help="Replicated populations per parameter set", type=int, default=4)
    parser.add_argument("--networkmodel", help="Path of a directory containing GML files representing the temporal network model for this simulation",
                        required=True)
    parser.add_argument("--numloci", help="Number of loci per individual", type=int, required=True)
    parser.add_argument("--maxinittraits", help="Max initial number of traits per locus for initialization", type=int,
                        required=True)
    parser.add_argument("--samplesize", help="Size of samples taken to calculate all statistics", type=int,
                        required=True)
    parser.add_argument("--innovrate", help="Rate at which innovations occur in population in scale-free theta units", type=float, required=True)
    parser.add_argument("--simlength", help="Time at which simulation and sampling end, defaults to 3000 generations",
                        type=long, default="3000")
    parser.add_argument("--popsize", help="Initial size of population for each community in the model", type=int, required=True)
    parser.add_argument("--migrationfraction", help="Fraction of population that migrates each time step", type=float, required=True, default=0.2)

    (config, sim_id, script) = sct.setup(parser)

    log.info("config: %s", config)

    ### NOTE ###
    ###
    ### the simuPOP module is deliberately imported here because we need to process the
    ### command line arguments first, to understand which version of the simuPOP module (e.g.,
    ### long allele representation, etc, to import, and because we need to figure out how
    ### many cores the machine has, etc., to set it up for parallel processing.  If we import
    ### at the top of the file as normal, the imports happen before any code is executed,
    ### and we can't set those options.  DO NOT move these imports out of setup and main.
    import simuPOP as sim
    import seriationct.demography as sdemo

    start = time()
    log.info("Starting simulation run %s", sim_id)
    log.debug("config: %s", config)

    # Calculate the burn in time

    burn_time = utils.simulation_burnin_time(config.popsize, config.innovrate)
    log.info("Minimum burn in time given popsize and theta: %s", burn_time)

    initial_distribution = ctu.constructUniformAllelicDistribution(config.maxinittraits)
    log.debug("Initial allelic distribution (for each locus): %s", initial_distribution)

    innovation_rate = pypopgen.wf_mutation_rate_from_theta(config.popsize, config.innovrate)
    log.debug("Per-locus innov rate within populations: %s", innovation_rate)


    # Construct a demographic model from a collection of network slices which represent a temporal network
    # of changing subpopulations and interaction strengths.  This object is Callable, and simply is handed
    # to the mating function which applies it during the copying process
    networkmodel = sdemo.TemporalNetwork(networkmodel_path=config.networkmodel,
                                         simulation_id=sim_id,
                                         sim_length=config.simlength,
                                         burn_in_time=burn_time,
                                         initial_subpop_size=config.popsize,
                                         migrationfraction=config.migrationfraction)

    # The regional network model defines both of these, in order to configure an initial population for evolution
    # Construct the initial population
    population = sim.Population(size=networkmodel.get_initial_size(),
                                subPopNames = networkmodel.get_subpopulation_names(),
                                ploidy=1,
                                loci=config.numloci,
                                infoFields=networkmodel.get_info_fields())

    # We are going to evolve the same population over several replicates, in order to measure how stochastic variation
    # effects the measured copying process.
    simu = sim.Simulator(population, rep=config.reps)


    # Start the simulation and evolve the population, taking samples after the burn-in time has elapsed

    simu.evolve(
        initOps=sim.InitGenotype(freq=initial_distribution),
        preOps=[
            sim.PyOperator(func=ctu.logGenerationCount, param=(), step=100, reps=0)
        ],
        matingScheme=sim.RandomSelection(subPopSize=networkmodel()),
        postOps=[sim.KAlleleMutator(k=MAXALLELES, rates=innovation_rate),
                 sim.PyOperator(func=sampling.sampleAlleleAndGenotypeFrequencies,
                                param=(config.samplesize, config.innovrate, config.popsize, sim_id, config.numloci),
                                subPops=sim.ALL_AVAIL,
                                step=1, begin=burn_time),

        ],
        gen=config.simlength,
    )

    endtime = time()
    elapsed = endtime - start
    log.info("simulation complete in %s seconds", elapsed)
    sampled_length = int(config.simlength) - burn_time
    data.store_simulation_metadata(sim_id, script, config.experiment, elapsed, config.simlength, sampled_length, config.popsize,
                                 config.networkmodel,networkmodel.get_subpopulation_durations())


if __name__ == "__main__":
    main()

