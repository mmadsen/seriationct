#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
from dbutils import *

from sample_deme import ClassFrequencySampleUnaveraged, storeClassFrequencySample, storeClassFrequencySamples
from processing_db import RegionalTemporalNetworkModel, NetworkModelDatabase, ExportedSimulationData, \
    SampledSimulationData, AssemblageSampledSimulationData, \
    FilteredAssemblageSimulationData, SeriationInputData, PostProcessingDatabase, \
    SimulationMetadataDatabase, SimulationRunMetadata, SeriationAnnotationData

# the following *should* be overridden by command line processing, even by defaults.
# bogus values are to ensure that CLI processing and configuration is working without bugs
dbhost = "override"
dbport = "override"
experiment_name = "test"


# When a new module is added for data, the module's filename should be added to the module list below,
# and the module must support a _get_dataobj_id() method which returns the string used in the Ming ORM
# configuration for MongoDB.  This is defined in each module, and then used in the declarative definition
# of the data object being stored.  Ming configuration is then automatic so that simulation simulations need
# include only two lines which are fully generic.

modules = [sample_deme]

