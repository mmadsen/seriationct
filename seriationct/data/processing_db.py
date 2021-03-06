from mongoengine import *
import bson
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
    """
    Post processing data pipeline for simulation data, through seriation and seriation annotation.

    Unlike other database objects, post processing should be idempotent, creating the same metadata
    and artifacts each time it is run on the same set of simulation runs (although exact contents may vary
    given stochastic resampling).  Thus, each store() method uses update_one to process an upsert on the
    MongoDB collection rather than a save() operation, which creates duplicate entries.

    """
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
            ExportedSimulationData.objects(id=bson.ObjectId()).modify(set__simulation_run_id = sim_id,
                                                      set__output_file = output_file,
                                                      upsert=True,
                                                  new=True)

    def store_sampled_datafile(self, input_file, ssize, output_file):
        # first query the simulation ID of the input file
        log.debug("sampled input_file: %s", input_file)
        export_obj = ExportedSimulationData.objects(output_file=input_file).first()
        sim_id = export_obj.simulation_run_id
        SampledSimulationData.objects(id=bson.ObjectId()).update_one(set__input_file = input_file,
                                                 set__simulation_run_id = sim_id,
                                                 set__output_file = output_file,
                                                 set__sample_size = ssize,
                                                 upsert=True)

    def store_assemblage_sampled_datafile(self, input_file, sample_type, sample_fraction, output_file):
        log.debug("assem sampled input_file: %s", input_file)
        sampled_obj = SampledSimulationData.objects(output_file=input_file).first()
        sim_id = sampled_obj.simulation_run_id
        AssemblageSampledSimulationData.objects(id=bson.ObjectId()).update_one(set__input_file = input_file,
                                                           set__output_file = output_file,
                                                           set__sample_fraction = sample_fraction,
                                                           set__sample_type = sample_type,
                                                           set__simulation_run_id = sim_id,
                                                           upsert=True)

    def store_filtered_datafile(self, input_file, network_model_path, drop_threshold, filter_type, min_nonzero_assemblages, output_file):
        log.debug("filter input_file: %s", input_file)
        assem_obj = AssemblageSampledSimulationData.objects(output_file=input_file).first()
        sim_id = assem_obj.simulation_run_id
        FilteredAssemblageSimulationData.objects(id=bson.ObjectId()).update_one(set__input_file = input_file,
                                                            set__output_file = output_file,
                                                            set__network_model_path = network_model_path,
                                                            set__drop_threshold = drop_threshold,
                                                            set__filter_type = filter_type,
                                                            set__min_nonzero_assemblages = min_nonzero_assemblages,
                                                            set__simulation_run_id = sim_id,
                                                            upsert=True)
        return sim_id

    def store_seriation_inputfile(self, input_file, source_identifier):
        log.debug("seriation input file: %s", input_file)
        filtered_obj = FilteredAssemblageSimulationData.objects(output_file=input_file).first()
        rtn_obj = RegionalTemporalNetworkModel.objects.get(compressedfilepath=filtered_obj.network_model_path)
        xyfile = rtn_obj.xyfilepath
        SeriationInputData.objects(id=bson.ObjectId()).update_one(set__simulation_run_id = filtered_obj.simulation_run_id,
                                              set__seriation_input_file = input_file,
                                              set__network_model_path = filtered_obj.network_model_path,
                                              set__xy_file_path = rtn_obj.xyfilepath,
                                              set__source_identifier = source_identifier,
                                              upsert=True)

    def store_seriation_annotation(self, input_file, source_identifier, seriation_run_id, annotation_dict):
        SeriationAnnotationData.objects(id=bson.ObjectId()).update_one(set__seriation_input_file = input_file,
                                                   set__source_identifier = source_identifier,
                                                   set__seriation_run_id = seriation_run_id,
                                                   set__annotations = annotation_dict,
                                                   upsert=True)

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

    Object created by:  seriationct-sample-assemblages.py

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

    The "source_identifier" field shall consist of a UUID which identifies the link
    between this seriation input record and the seriation run output.  Many seriations
    might have the same network model, simulation run, xyfile, etc., so we need
    a unique key to tie input to output.  This is passed to IDSS as --source_identifier
    and recorded in the database.

    This allows seriation output post-processing to find the original simulation info,
    and through the input file itself, chain back to the simulation post-processing steps.
    """
    seriation_input_file = StringField(required=True)
    simulation_run_id = StringField(required=True)
    network_model_path = StringField(required=True)
    xy_file_path = StringField(required=True)
    source_identifier = StringField(required=True)
    meta = {
        'indexes': [
            '$seriation_input_file'
        ]
    }


class SeriationAnnotationData(Document):
    """
    the primary data source for seriation output is the IDSS SeriationRun object,
    but for seriationct purposes, we often want to annotate the output with
    network models and other classification information that we know in the context
    of an experiment.  This object carries that information at the end of an
    annotation.
    """
    seriation_input_file = StringField(required=True)
    seriation_run_id = StringField(required=True)
    annotations = DictField()
    source_identifier = StringField(required=True)
    meta = {
        'indexes': [
            '$seriation_input_file',
        ]
    }