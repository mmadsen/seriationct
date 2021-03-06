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


import uuid

import seriationct.utils as utils
import simuOpt
simuOpt.setOptions(alleleType='long', optimized=True, quiet=False, numThreads=utils.get_parallel_cores(dev_flag=True))
import simuPOP as sim

import seriationct.demography as demo


global config, sim_id, script


def setup(parser):
    config = parser.parse_args()

    sim_id = uuid.uuid4().urn
    script = __file__

    if config.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    # set up parallelism.  At the moment, this doesn't do anything on OSX
    # but should provide parallelism on Linux across the replicates at least
    cores = utils.get_parallel_cores(config.devel)
    log.debug("Setting up %s cores for parallel simulation", cores)

    # import simuOpt
    # if(config.debug == 1):
    #     simuOpt.setOptions(alleleType='long',optimized=True,quiet=False,numThreads = cores)
    # else:
    #     simuOpt.setOptions(alleleType='long',optimized=True,quiet=True,numThreads = cores)


    return (config,sim_id,script)



def main():
    MAXALLELES = 10000000
    subpop_history_map = dict()

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--networkmodel", help="Filename of the temporal network model zipfile for this simulation",
                        required=True)
    parser.add_argument("--popsize", help="Population size for each subpopulation", type=int, default=200)
    parser.add_argument("--simlength", help="Time at which simulation and sampling end",type=long, default="3000")
    parser.add_argument("--innovrate", help="Rate at which innovations occur in population in scale-free theta units", type=float, default=0.001)
    parser.add_argument("--experiment", help="provide name for experiment", required=False)
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--devel", help="Use only half of the available CPU cores", type=int, default=1)
    parser.add_argument("--migrationfraction", help="Fraction of population that migrates each time step", type=float, default=0.1)

    (config, sim_id, script) = setup(parser)

    burn_time = utils.simulation_burnin_time(config.popsize, config.innovrate)
    log.info("Burn-in time: %s", burn_time)


    log.info("Explaining network model %s for popsize %s and innovation rate %s", config.networkmodel, config.popsize, config.innovrate)


    net_model = demo.TemporalNetwork(networkmodel_path=config.networkmodel,
                                     simulation_id=sim_id,
                                     sim_length=config.simlength,
                                     burn_in_time=burn_time,
                                     initial_subpop_size=config.popsize,
                                     migrationfraction=config.migrationfraction
                                     )

    pop = sim.Population(size = net_model.get_initial_size(), subPopNames = net_model.get_subpopulation_names(), infoFields=net_model.get_info_fields())

    log.info("network model has slices at %s", net_model.times)
    #log.info("Initial migration matrix: %s", net_model._cached_migration_matrix)
    for time in range(1,config.simlength+1):
        pop.dvars().gen = time
        net_model(pop)
        if net_model.is_change_time(time):
            log.info("time: %s subpop names: %s subpop sizes: %s", time, net_model.get_subpopulation_names(), net_model.get_subpopulation_sizes())

        if time == config.simlength:
            sp_durations = net_model.get_subpopulation_durations()
            log.debug("subpop durations: %s", sp_durations)
            log.debug("time: %s END of simulation", time)

if __name__ == "__main__":
    main()

