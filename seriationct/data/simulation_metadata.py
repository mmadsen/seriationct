#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
.. module:: simulation_data
    :platform: Unix, Windows
    :synopsis: Data object for storing metadata and parameter about a simulation run in MongoDB, via the Ming ORM.

.. moduleauthor:: Mark E. Madsen <mark@madsenlab.org>

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




def store_simulation_metadata(sim_id,script,exp,elapsed,length,sampledlength,popsize,netmodel,durations,fcline,rseed):
    """Stores the parameters and metadata for a simulation run in the database.

    """
    SimulationMetadata(dict(
        script_filename = script,
        simulation_run_id = sim_id,
        experiment_name = exp,
        elapsed_time = elapsed,
        full_command_line = fcline,
        random_seed = rseed,
        run_length = length,
        sampled_length = sampledlength,
        popsize = popsize,
        networkmodel = netmodel,
        subpopulation_durations = durations
    )).m.insert()
    return True


def columns_to_export_for_analysis():
    cols = [
        "simulation_run_id",
        "experiment_name",
        "elapsed_time",
        "run_length",
        "popsize",
        "networkmodel"
    ]
    return cols


class SimulationMetadata(Document):

    class __mongometa__:
        session = Session.by_name(_get_dataobj_id())
        name = 'simulation_metadata'

    _id = Field(schema.ObjectId)
    script_filename = Field(str)
    simulation_run_id = Field(str)
    experiment_name = Field(str)
    full_command_line = Field(str)
    random_seed = Field(int)
    elapsed_time = Field(float)
    run_length = Field(int)
    sampled_length = Field(int)
    popsize = Field(int)
    networkmodel = Field(str)
    subpopulation_durations = Field(schema.Anything)





