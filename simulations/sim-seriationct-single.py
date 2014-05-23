#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
the purpose here is to run the tree structured model for a fixed length of time, with mutation, and see what
happens to the structure of trait trees, sampled at fixed intervals.  We will leave in homophily, but ignore
convergence since it should be temporary with mutation/noise.

"""


import logging as log
import ming
import argparse
import madsenlab.seriationct.utils as utils
import madsenlab.seriationct.data as data
import madsenlab.seriationct.dynamics as dyn
import pprint as pp
from time import time
import uuid




def setup():
    global args, simconfig

    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", help="provide name for experiment", required=True)
    parser.add_argument("--debug", help="turn on debugging output")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--configuration", help="Configuration file for experiment", required=True)
    parser.add_argument("--popsize", help="Population size", required=True)
    parser.add_argument("--numloci", help="Number of loci per individual", required=True)
    parser.add_argument("--maxinittraits", help="Max initial number of traits per locus for initialization", required=True)
    parser.add_argument("--conformismstrength", help="Strength of conformist bias [0.0 - 1.0]", required=True)
    parser.add_argument("--anticonformismstrength", help="Strength of conformist bias [0.0 - 1.0]", required=True)
    parser.add_argument("--samplesize", help="Size of samples taken to calculate all statistics", required=True)
    parser.add_argument("--innovrate", help="Rate at which innovations occur in population", required=True)
    parser.add_argument("--periodic", help="Periodic boundary condition", choices=['1','0'], required=True)
    parser.add_argument("--diagram", help="Draw a diagram of the converged model", action="store_true")
    parser.add_argument("--samplinginterval", help="Interval between samples, once sampling begins, defaults to 1M steps", default="1000000")
    parser.add_argument("--samplingstarttime", help="Time at which sampling begins, defaults to 250K steps", default="250000")
    parser.add_argument("--simulationendtime", help="Time at which simulation and sampling end, defaults to 2M steps", default="2000000")

    args = parser.parse_args()

    simconfig = utils.MixtureConfiguration(args.configuration)

    if args.debug == '1':
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    log.debug("experiment name: %s", args.experiment)
    data.set_experiment_name(args.experiment)
    data.set_database_hostname(args.dbhost)
    data.set_database_port(args.dbport)
    config = data.getMingConfiguration(data.modules)
    ming.configure(**config)

    simconfig.num_features = int(args.numloci)
    simconfig.num_traits = int(args.maxinittraits)
    simconfig.popsize = int(args.popsize)
    simconfig.innovation_rate = float(args.innovrate)
    simconfig.maxtime = int(args.simulationendtime)
    simconfig.script = __file__
    simconfig.conformism_strength = float(args.conformismstrength)
    simconfig.anticonformism_strength = float(args.anticonformismstrength)
    simconfig.maxtime = int(args.simulationendtime)
    simconfig.sample_size = int(args.samplesize)

    simconfig.sim_id = uuid.uuid4().urn
    if args.periodic == '1':
        simconfig.periodic = 1
    else:
        simconfig.periodic = 0


def main():
    start = time()

    model_constructor = utils.load_class(simconfig.POPULATION_STRUCTURE_CLASS)
    graph_factory_constructor = utils.load_class(simconfig.NETWORK_FACTORY_CLASS)
    trait_factory_constructor = utils.load_class(simconfig.TRAIT_FACTORY_CLASS)
    interaction_rule_list = utils.parse_interaction_rule_map(simconfig.INTERACTION_RULE_CLASS)
    innovation_rule_constructor = utils.load_class(simconfig.INNOVATION_RULE_CLASS)

    log.debug("Configuring CT Mixture Model with structure class: %s graph factory: %s interaction rule: %s", simconfig.POPULATION_STRUCTURE_CLASS, simconfig.NETWORK_FACTORY_CLASS, simconfig.INTERACTION_RULE_CLASS)

    # instantiate the model and its various subobjects, including any interaction rules
    graph_factory = graph_factory_constructor(simconfig)
    trait_factory = trait_factory_constructor(simconfig)



    model = model_constructor(simconfig, graph_factory, trait_factory)
    interaction_rule_list = utils.construct_rule_objects(interaction_rule_list, model)
    model.interaction_rules = interaction_rule_list

    # now we're ready to initialize the population
    model.initialize_population()
    innovation_rule = innovation_rule_constructor(model)

    # initialize a dynamics
    dynamics = dyn.MoranDynamics(simconfig,model,innovation_rule)


    log.info("Starting %s", simconfig.sim_id)

    while(1):

        dynamics.update()
        timestep = dynamics.timestep

        if (timestep % 100000) == 0:
            log.debug("time: %s copying events: %s copies by locus: %s  innovations: %s innov by locus: %s",
                      timestep, model.get_interactions(), model.get_interactions_by_locus(), model.get_innovations(),
                      model.get_innovations_by_locus())
            #ax.full_update_link_cache()

        if timestep > int(args.samplingstarttime) and timestep % int(args.samplinginterval)  == 0:
            utils.sample_mixture_model(model, args, simconfig, timestep)

        # if the simulation is cycling endlessly, and after the cutoff time, sample and end
        if timestep >= simconfig.maxtime:
            # we'll get the last sample because the endtime will also be a multiple of the sampling interval
            #utils.sample_mixture_model(model, args, simconfig, timestep)
            endtime = time()
            elapsed = endtime - start
            log.info("Completed: %s  Elapsed: %s", simconfig.sim_id, elapsed)
            data.store_simulation_timing(simconfig.sim_id,simconfig.INTERACTION_RULE_CLASS,simconfig.POPULATION_STRUCTURE_CLASS,simconfig.script,args.experiment,elapsed,timestep)
            exit(0)

# end main




if __name__ == "__main__":
    setup()
    main()

