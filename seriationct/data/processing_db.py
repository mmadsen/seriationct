from mongoengine import *
import logging as log



class SimulationRunMetadata(Document):
    """
    COPY OF THE MING OBJECT IN SIMULATION_METADATA.PY, UNTIL I MOVE THE MAIN SIMULATION PROGRAM TO MONGOENGINE
    THIS IS BAD DUPLICATION, BAD PROGRAMMER!
    """
    script_filename = StringField()
    simulation_run_id = StringField()
    experiment_name = StringField()
    full_command_line = StringField()
    innov_rate = FloatField()
    migration_fraction = FloatField()
    random_seed = IntField()
    num_loci = IntField()
    max_init_traits = IntField()
    elapsed_time = FloatField()
    sim_length = IntField()
    sample_fraction = FloatField()
    sampled_length = IntField()
    popsize = IntField()
    networkmodel = StringField()
    subpopulation_durations = DictField()
    subpopulation_origin_times = DictField()
    meta = {
        'indexes': [
            'simulation_run_id',
            'networkmodel',
            'experiment_name'
        ]
    }




class SimulationMetadataDatabase(object):
    def __init__(self, args):
        self.args = args

        log.debug("db connect args: %s", args)
        connect(db=args['database'],
                host=args['dbhost'],
                port=int(args['dbport']),
                username=args['dbuser'],
                password=args['dbpassword'])

    def store_simulation_run_parameters(self, sim_id, script, exp, elapsed, length,
                                        sampledlength, popsize, netmodel, durations,
                                        fcline, rseed, origins, innovrate, migrationrate,
                                        numloci, maxinittraits):

        sm = SimulationRunMetadata()
        sm.script_filename = script
        sm.simulation_run_id = sim_id
        sm.experiment_name = exp
        sm.elapsed_time = elapsed
        sm.full_command_line = fcline
        sm.random_seed = rseed
        sm.run_length = length
        sm.sampled_length = sampledlength
        sm.popsize = popsize
        sm.networkmodel = netmodel
        sm.subpopulation_durations = durations
        sm.subpopulation_origin_times = origins
        sm.innov_rate = innovrate
        sm.migration_fraction = migrationrate
        sm.num_loci = numloci
        sm.max_init_traits = maxinittraits
        sm.save(validate=False)


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

        log.debug("db connect args: %s", args)
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


class PostProcessingDatabase(object):
    def __init__(self, args):
        self.args = args

        log.debug("db connect args: %s", args)
        connect(db=args['database'],
                host=args['dbhost'],
                port=int(args['dbport']),
                username=args['dbuser'],
                password=args['dbpassword'])


    def store_exported_datafile(self, sim_id, output_file):
        exported_db = ExportedSimulationData()
        exported_db.simulation_run_id = sim_id
        exported_db.output_file = output_file
        exported_db.save()

    def store_sampled_datafile(self, input_file, ssize, output_file):
        # first query the simulation ID of the input file
        log.debug("sampled input_file: %s", input_file)
        export_obj = ExportedSimulationData.objects.get(output_file=input_file)
        sampled_db = SampledSimulationData()
        sampled_db.input_file = input_file
        sampled_db.output_file = output_file
        sampled_db.sample_size = ssize
        sampled_db.simulation_run_id = export_obj.simulation_run_id
        sampled_db.save()

    def store_assemblage_sampled_datafile(self, input_file, sample_type, sample_fraction, output_file):
        log.debug("assem sampled input_file: %s", input_file)
        sampled_obj = SampledSimulationData.objects.get(output_file=input_file)
        assem_db = AssemblageSampledSimulationData()
        assem_db.input_file = input_file
        assem_db.output_file = output_file
        assem_db.sample_fraction = sample_fraction
        assem_db.sample_type = sample_type
        assem_db.simulation_run_id = sampled_obj.simulation_run_id
        assem_db.save()

    def store_filtered_datafile(self, input_file, network_model_path, drop_threshold, filter_type, min_nonzero_assemblages, output_file):
        log.debug("filter input_file: %s", input_file)
        assem_obj = AssemblageSampledSimulationData.objects.get(output_file=input_file)
        filtered_db = FilteredAssemblageSimulationData()
        filtered_db.input_file = input_file
        filtered_db.output_file = output_file
        filtered_db.network_model_path = network_model_path
        filtered_db.drop_threshold = drop_threshold
        filtered_db.filter_type = filter_type
        filtered_db.min_nonzero_assemblages = min_nonzero_assemblages
        filtered_db.simulation_run_id = assem_obj.simulation_run_id
        filtered_db.save()
        return assem_obj.simulation_run_id

    def store_seriation_inputfile(self, input_file):
        log.debug("seriation input file: %s", input_file)
        filtered_obj = FilteredAssemblageSimulationData.objects.get(output_file=input_file)
        rtn_obj = RegionalTemporalNetworkModel.objects.get(compressedfilepath=filtered_obj.network_model_path)
        xyfile = rtn_obj.xyfilepath
        ser = SeriationInputData()
        ser.simulation_run_id = filtered_obj.simulation_run_id
        ser.seriation_input_file = input_file
        ser.network_model_path = filtered_obj.network_model_path
        ser.xy_file_path = xyfile
        ser.save()



class ExportedSimulationData(Document):
    """
    Simple export of raw simulation data to data files, time averaging all intervals
    together for a given assemblage.  There is only one of these files for each
    simulation run ID.

    Object created by:  seriationct-export-single-simulation.py
    """
    simulation_run_id = StringField(required=True)
    # each end product file will come from a single original data export file
    output_file = StringField(required=True)
    meta = {
        'indexes': [
            '$output_file'
        ]
    }


class SampledSimulationData(Document):
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
    meta = {
        'indexes': [
            '$output_file'
        ]
    }


class AssemblageSampledSimulationData(Document):
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
    meta = {
        'indexes': [
            '$output_file'
        ]
    }


class FilteredAssemblageSimulationData(Document):
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
    meta = {
        'indexes': [
            '$output_file'
        ]
    }


class SeriationInputData(Document):
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
    network_model_path = StringField(required=True)
    xy_file_path = StringField(required=True)
    meta = {
        'indexes': [
            '$seriation_input_file'
        ]
    }

