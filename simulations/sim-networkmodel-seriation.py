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
    parser.add_argument("--networkmodel", help="Filename of the temporal network model for this simulation",
                        required=True)
    parser.add_argument("--numloci", help="Number of loci per individual", type=int, required=True)
    parser.add_argument("--maxinittraits", help="Max initial number of traits per locus for initialization", type=int,
                        required=True)
    parser.add_argument("--samplesize", help="Size of samples taken to calculate all statistics", type=int,
                        required=True)
    parser.add_argument("--innovrate", help="Rate at which innovations occur in population", type=float, required=True)
    parser.add_argument("--samplingstarttime", help="Time at which sampling begins, defaults to 250K steps", type=long,
                        default="250000")
    parser.add_argument("--simlength", help="Time at which simulation and sampling end, defaults to 2M steps",
                        type=long, default="3000")

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
    import simuPOP.demography as demo
    import seriationct.demography as sdemo

    start = time()
    log.info("Starting simulation run %s", sim_id)
    log.debug("config: %s", config)


    # test purposes
    num_subpops = 2
    popsize = 1000
    popsize_list = [popsize] * num_subpops
    subpop_names = [str(i) for i in xrange(0, num_subpops)]
    log.debug("subpopulation names: %s", subpop_names)

    initial_distribution = ctu.constructUniformAllelicDistribution(config.maxinittraits)
    log.debug("Initial allelic distribution (for each locus): %s", initial_distribution)

    innovation_rate = pypopgen.wf_mutation_rate_from_theta(popsize, config.innovrate)
    log.debug("Per-locus innov rate within populations: %s", innovation_rate)


    # Process the temporal network model for subpopulations
    #
    network_snapshots = None
    networkmodel = sdemo.TemporalNetwork(file_list=network_snapshots, sim_length=config.simlength, initial_size=popsize_list, info_fields='migrate_to')


    population = sim.Population(size=popsize_list, subPopNames = subpop_names, ploidy=1, loci=config.numloci, infoFields=['migrate_to'])
    simu = sim.Simulator(population, rep=config.reps)

    simu.evolve(
        initOps=sim.InitGenotype(freq=initial_distribution),
        preOps=[
            sim.PyOperator(func=ctu.logGenerationCount, param=(), step=100, reps=0)
        ],
        matingScheme=sim.RandomSelection(subPopSize=networkmodel),
        postOps=[sim.KAlleleMutator(k=MAXALLELES, rates=innovation_rate),
                 sim.PyOperator(func=sampling.sampleAlleleAndGenotypeFrequencies,
                                param=(config.samplesize, config.innovrate, popsize, sim_id, config.numloci),
                                subPops=sim.ALL_AVAIL,
                                step=1, begin=1000),
                 sim.Stat(popSize=True, step=100, begin=100),
                 sim.PyEval(r'"gen %d, rep %d  %s\n" % (gen, rep, subPopSize)', step=100, begin=100),

        ],
        # finalOps=sim.PyOperator(func=sampling.sampleIndividuals,
        #                         param=(config.samplesize, innovation_rate, config.popsize, sim_id, config.numloci),
        #                         subPops=sim.ALL_AVAIL,
        #                         step=1000, begin=1000),
        gen=networkmodel.get_sim_length(),
    )

    endtime = time()
    elapsed = endtime - start
    log.info("simulation complete in %s seconds", elapsed)
    data.store_simulation_timing(sim_id, script, config.experiment, elapsed, config.simlength, popsize,
                                 config.networkmodel)


if __name__ == "__main__":
    main()

