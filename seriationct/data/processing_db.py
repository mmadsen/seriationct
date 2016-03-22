from mongoengine import *
import logging as log



class ExportedSimulationData(EmbeddedDocument):
    simulation_run_id = StringField(required=True)

    # each end product file will come from a single original data export file
    exported_data_path = StringField(required=True)




    bootstrap_ci_flag = BooleanField()
    bootstrap_significance = FloatField()
    spatial_significance = BooleanField()
    spatial_bootstrap_n = IntField()
    xyfile_path = StringField(required=True)
    inputfile = StringField(required=True)
    outputdirectory = StringField(required=True)
    continuity_seriation = BooleanField()
    frequency_seriation = BooleanField()
    full_cmdline = StringField()



class SampledSimulationData(EmbeddedDocument):
    pass


class AssemblageSampledSimulationData(EmbeddedDocument):
    pass


class FilteredAssemblageSimulationData(EmbeddedDocument):
    pass

