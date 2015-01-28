#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import uuid
import logging as log
import seriationct.data as data
import seriationct.utils as utils
import ming

def setup(parser):
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

    return (config, sim_id, script)