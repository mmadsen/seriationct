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
import ming
import argparse
import seriationct.data as data
import seriationct.utils as utils
import ctpy.utils as ctu
import pytransmission.popgen as pypopgen
from time import time
import uuid

MAXALLELES = 1000000000


def setup():
    global config, sim_id, script

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--devel", help="Use only half of the available CPU cores", type = int, default = 1)
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--configuration", help="Configuration file for experiment", required=True)
    parser.add_argument("--reps", help="Replicated populations per parameter set", default = 25)
    parser.add_argument("--networkmodel", help="Filename of the temporal network model for this simulation", required=True)
    parser.add_argument("--popsize", help="Population size", type = int, required=True)
    parser.add_argument("--numloci", help="Number of loci per individual", type = int, required=True)
    parser.add_argument("--maxinittraits", help="Max initial number of traits per locus for initialization", type = int, required=True)
    parser.add_argument("--samplesize", help="Size of samples taken to calculate all statistics", type = int, required=True)
    parser.add_argument("--innovrate", help="Rate at which innovations occur in population", type = float, required=True)
    parser.add_argument("--samplinginterval", help="Interval between samples, once sampling begins, defaults to 1M steps", default="1000000")
    parser.add_argument("--samplingstarttime", help="Time at which sampling begins, defaults to 250K steps", default="250000")
    parser.add_argument("--simlength", help="Time at which simulation and sampling end, defaults to 2M steps", type = long, default="2000000")

    config = parser.parse_args()


    sim_id = uuid.uuid4().urn
    script = __file__

    if config.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    data.set_experiment_name(config.experiment)
    data.set_database_hostname(config.dbhost)
    data.set_database_port(config.dbport)
    dbconfig = data.getMingConfiguration(data.modules)
    ming.configure(**dbconfig)

    # set up parallelism.  At the moment, this doesn't do anything on OSX
    # but should provide parallelism on Linux across the replicates at least
    cores = utils.get_parallel_cores(config.devel)
    log.debug("Setting up %s cores for parallel simulation", cores)
    import simuOpt
    if(config.debug == 1):
        simuOpt.setOptions(alleleType='long',optimized=True,quiet=False,numThreads = cores)
    else:
        simuOpt.setOptions(alleleType='long',optimized=True,quiet=True,numThreads = cores)







def main():
    import simuPOP as sim
    start = time()
    log.info("Starting simulation run %s",  sim_id)
    log.debug("config: %s" , config)



    initial_distribution = ctu.constructUniformAllelicDistribution(config.maxinittraits)
    log.debug("Initial allelic distribution: %s", initial_distribution)

    innovation_rate = pypopgen.wf_mutation_rate_from_theta(config.popsize, config.innovrate)
    log.debug("Per-locus innov rate within populations: %s", innovation_rate)


    pop = sim.Population(size=config.popsize, ploidy=1, loci=config.numloci)
    simu = sim.Simulator(pop, rep=config.reps)

    simu.evolve(
        initOps = sim.InitGenotype(freq=initial_distribution),
        preOps = [
            sim.PyOperator(func=ctu.logGenerationCount, param=(), step=100, reps=0),
        ],
        matingScheme = sim.RandomSelection(),
        postOps = [sim.KAlleleMutator(k=MAXALLELES, rates=innovation_rate),
                    # sim.PyOperator(func=data.sampleNumAlleles, param=(config.samplesize, innovation_rate, config.popsize,sim_id,config.numloci),
                    #                step=sampling_interval,begin=time_start_stats),
                    # sim.PyOperator(func=data.sampleTraitCounts, param=(config.samplesize, innovation_rate, config.popsize,sim_id,config.numloci),
                    #                step=sampling_interval,begin=time_start_stats),
                    # sim.PyOperator(func=data.censusTraitCounts, param=(innovation_rate, config.popsize,sim_id,config.numloci),
                    #                step=sampling_interval,begin=time_start_stats),
                    # sim.PyOperator(func=data.censusNumAlleles, param=(innovation_rate, config.popsize,sim_id,config.numloci),
                    #                step=sampling_interval,begin=time_start_stats),
                    # sim.PyOperator(func=data.sampleIndividuals, param=(config.samplesize, innovation_rate, config.popsize, sim_id,config.numloci),
                    #                step=sampling_interval, begin=time_start_stats),
               ],
        gen = config.simlength,
    )







    endtime = time()
    elapsed = endtime - start
    data.store_simulation_timing(sim_id,script,config.experiment,elapsed,config.simlength,config.popsize,config.networkmodel)



if __name__ == "__main__":
    setup()
    main()

