from mongoengine import *
import logging as log



################ Regional Temporal Network Model Catalog ##############


class RegionalTemporalNetworkModel(Document):
    """
    Data structure to capture the parameters which go into a regional
    temporal network model, and where to find its expressions in the file system.

    The specific parameters of a network model type are given in a DictField,
    allowing the types of network model to be extensible.
    """
    model_id = StringField()
    model_uuid = StringField()
    network_type = StringField()
    generator = StringField()
    populations_per_slice = IntField()
    slices = IntField()
    rawdirectorypath = StringField()
    compressedfilepath = StringField()
    xyfilepath = StringField()
    model_parameters = DictField()




class NetworkModelDatabase(object):
    """
    persistence connection to the MongoDB database server
    into which RegionalTemporalNetworkmodel metadata are stored.
    """

    def __init__(self, args):
        self.args = args

        log.info("db connect args: %s", args)
        connect(db = args['database'],
                host = args['dbhost'],
                port = int(args['dbport']),
                username = args['dbuser'],
                password = args['dbpassword'])


    def store_model_metadata(self, model_data):
        """
        Saves the metadata for a single network model.

        :param data : dict with network model parameters
        """

        data = model_data.copy()
        # we use dict.pop because we went to remove things from the input dict that 
        # are named model objects, and leave behind the unknown network model parameters
        # to preserve extensibility

        rtn = RegionalTemporalNetworkModel()
        rtn.model_id = data.pop('model_id')
        rtn.model_uuid = data.pop('model_uuid')
        rtn.network_type = data.pop('network_type')
        rtn.generator = data.pop('generator')
        rtn.populations_per_slice = data.pop('populations_per_slice')
        rtn.slices = data.pop('slices')
        rtn.rawdirectorypath = data.pop('rawdirectorypath')
        rtn.compressedfilepath = data.pop('compressedfilepath')
        rtn.xyfilepath = data.pop('xyfilepath')

        # whatever is left in data are specific network model parameters
        rtn.model_parameters = data

        rtn.save()



######################## Simulation Data Post Processing #################

class ExportedSimulationData(EmbeddedDocument):
    """
    Simple export of raw simulation data to data files, time averaging all intervals
    together for a given assemblage.  There is only one of these files for each
    simulation run ID.

    Object created by:  seriationct-export-single-simulation.py
    """
    simulation_run_id = StringField(required=True)
    # each end product file will come from a single original data export file
    output_file = StringField(required=True)


class SampledSimulationData(EmbeddedDocument):
    """
    Resampling of very large exported data records to standardize the sample of objects
    per assemblage to something closer to archaeological recovery.  This tends to
    filter out very rare combinations, of course.

    Object created by:  seriationct-sample-exported-datafiles.py

    There can be more than one of these for every ExportedSimulationData object
    """
    input_file = StringField(required=True)
    sample_size = IntField(required=True)
    output_file = StringField(required=True)
    simulation_run_id = StringField(required=True)


class AssemblageSampledSimulationData(EmbeddedDocument):
    """
    Sample of some number of assemblages from the total number of communities
    available in the exported and sampled data.

    Object created by:  seriationct-sample-assemblages-for-seriation.py

    There can be more than one of these for every SampledSimulationData object,
    especially given the --numsamples <int> argument
    """
    input_file = StringField(required=True)
    sample_type = StringField(required=True)
    sample_fraction = FloatField(required=True)
    output_file = StringField(required=True)
    simulation_run_id = StringField(required=True)


class FilteredAssemblageSimulationData(EmbeddedDocument):
    """
    Filtered set of assemblages where all assemblages are kept, but some types
    (columns) are removed based on a set of filtering criteria (e.g., < 3 assemblages
    have nonzero values for a type, dip tests for unimodality, etc).

    Object created by:  seriationct-filter-types.py

    There will be exactly one of these for every AssemblageSampledSimulationData object.

    """
    input_file = StringField(required=True)
    network_model_path = StringField(required=True)
    drop_threshold = FloatField()
    filter_type = StringField(required=True)
    min_nonzero_assemblages = IntField()
    output_file = StringField(required=True)
    simulation_run_id = StringField(required=True)


class SeriationInputData(EmbeddedDocument):
    """
    Final set of post processed data files to be used as input to IDSS seriation.
    This class is a simple pointer to the output of whatever the last stage
    of post-processing and sampling is, and exists to allow that pipeline to be
    mutable while preserving a single point of entry for seriation job construction.

    As such, there is no foreign key/ReferenceField relationship here.  The script
    that constructs these objects actually will copy the path from the output_file
    field in the final stage of post-processing to this object.

    """
    seriation_input_file = StringField(required=True)
    simulation_run_id = StringField(required=True)

