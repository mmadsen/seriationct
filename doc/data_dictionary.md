# Data Dictionary for SeriationCT #

This data dictionary applies to tag "v1.1" of SeriationCT, committed 2/28/15 by mmadsen

The data repository is MongoDB, which is schema-free, so this document catalogs the fields currently used.  

## Database ##

The database names for SeriationCT are automatically generated from the "experiment" parameter given as a command line argument to the simulation script.  For example, if the command line parameter "--experiment validationtest" is given, the simulation script will create a database called "validationtest_samples_raw" in the appropriate MongoDB server instance.  

The suffix "_samples_raw" indicates that the database contains raw output from the simulation without any post processing.  

## Collections ##

Within the raw samples database, SeriationCT currently stores two "document collections" (the MongoDB equivalent of tables).  

### Collection:  simulation_metadata ###

The collection named "simulation_metadata" is the repository for recording simulation runs.  The collection has the following fields:

**simulation_run_id**:  a UUID (universally unique identifier) generated for this simulation run according to the Type 1 algorithm in RFC1422.  This is given as the ASCII string equivalent of the underlying 128 bit value.  An example of a UUID in text form is "urn:uuid:64bd0cf8-bfa1-11e4-aa6a-b8f6b1154c9b".  

**sampled_length**:  the number of simulation steps from which data samples are recorded (as opposed to burn in periods or other non-sampled periods).  Type:  integer

**random_seed**:  32 bit integer value recording the seed value for any random number generators used in the simulation run. 

**script_filename**:  String giving directory path (optional) and filename (required) for the executable invoked for the simulation run.

**networkmodel**:  String giving directory path (optional) and filename (required) for a compressed ZIP format file containing GML network files that contain sequential network slices representing an evolving interaction network.  Each file can have a descriptive name, but should contain "-<digit>.gml" as the end of the filenames (e.g., "verificationtest-2.gml").  The order in which network files are applied is derived from from this convention.  

**popsize**:  The base population size for each vertex in the network model, as an integer.  The total population size at any given time is the number of vertices in the active network slice multiplied by this value.  

**elapsed_time**:  The total wall clock time in seconds taken for execution of the simulation run (including any internally processed replicates, as in simuPOP simulations).  Type:  floating point

**experiment_name**:  String giving the name for this collection of experimental results.  

**run_length**: The total number of simulation steps performed (which will be equal to or greater than the sampled time, above).  Type:  integer

**full_command_line**:  String giving the exact command line used to execute this simulation run.

**subpopulation_durations**:  A map/dictionary of the subpopulations in network slices specified by **networkmodel**, and the number of simulation steps each subpopulation existed as part of the evolving population.  Keys are strings, values are integers.


### Collection:  seriationct_sample_unaveraged ###

**simulation_run_id**:  As above, records the unique simulation run which produced this data sample.

**random_seed**:  As above.  

**replication**:  In simulations where a single run has a set of parameters but is executed as N replications with the same parameters, as in simuPOP, this field records the replication number.  When there is only one replication per simulation run, this value will be zero.    Type:  integer

**class_freq**:  A map/dictionary of sampled data values for trait combinations (classes) and their frequency in the sample from that time instant.  An example of an entry is "0-0-4" : 0.24, indicating that 24% of samples displayed class "0-0-4".  Keys are strings, values are floating point numbers.

**class_count**:  A map/dictionary of sampled data values for trait combinations (classes) and their count in the sample from that time instant.  Keys are strings, values are integers.

**simulation_time**:  The simulation step (integer) at which the sample was taken.  

**subpop**:  The subpopulation from which the sample was taken, identified by the "label" field in the NetworkX vertex object in the relevant GML file within the network model.  Type:  string

**sample_size**:  The number of individuals sampled from the subpopulation.  Type:  integer

**mutation_rate**:  The overall population rate of innovations per simulation step.  Thus, a rate of 1.0 means that the population will have, on average, a new trait in each simulation step, in some subpopulation.  The usual "per individual chance" of mutation is thus mutation_rate / (popsize * number of active subpopulations) and varies over time as subpopulations are added and deleted.   Type:  floating point number.

**population_size**:  As above, the base size of a subpopulation in the simulation.  

**class_richness**:  The number of classes represented in the sample of individuals in this simulation step.  It is equivalent to len(class_count.keys()).  Type:  integer.


