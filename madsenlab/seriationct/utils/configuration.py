#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import json
from operator import itemgetter
from numpy.random import RandomState


##########################################################################

class BaseConfiguration(object):
    """
    Common behavior for all configuration classes.

    An object of this class also has property getter/setters for specific instances of the configuration, which would
    characterize a specific simulation run.  These must be set by a simulation model's script, for consumption by
    underlying classes and modules.

    The class also contains two methods for constructing document-ready representations of a set of configuration
    parameters, as a LaTeX table or a Pandoc-formatted Markdown table.  With a wrapper script, these methods
    allow direct incorporation of simulation configurations into publications and reports, for accuracy and
    reproducibility.
    """

    INTERACTION_RULE_CLASS = {"madsenlab.seriationct.rules.NeutralCopyingRule": 0.5, "madsenlab.seriationct.rules.ConformistCopyingRule": 0.5}

    POPULATION_STRUCTURE_CLASS = 'madsenlab.seriationct.population.FixedTraitStructurePopulation'

    NETWORK_FACTORY_CLASS = 'madsenlab.seriationct.population.SquareLatticeFactory'

    TRAIT_FACTORY_CLASS = 'madsenlab.seriationct.traits.LocusAlleleTraitFactory'

    INNOVATION_RULE_CLASS = 'madsenlab.seriationct.population.InfiniteAllelesMutationRule'
    """
    The fully qualified import path for a class which implements the population model.
    """

    STRUCTURE_PERIODIC_BOUNDARY = [True, False]

    SIMULATION_CUTOFF_TIME = 2000000
    """
    The time at which we terminate a simulation which is cycling endlessly with active links.
    """

    REPLICATIONS_PER_PARAM_SET = 10
    """
    For each combination of simulation parameters, CTPy and simuPOP will run this many replicate
    populations, saving samples identically for each, but initializing each replicate with a
    different population and random seed.
    """

    POPULATION_SIZES_STUDIED = [400,900,1600,2500,10000]
    """
    In most of the CT models we study, the absolute amount of variation we might expect to see is
    partially a function of the number of individuals doing the transmitting.  This is *total* population
    size, either for a single population, or the metapopulation as a whole in a spatial model.  Because we are
    going to model this on a grid, these numbers should be perfect squares, so that if the population size is N,
    the lattice size (on a side) is SQRT(N).
    """

    SAMPLE_SIZES_STUDIED = [10,20,40,80,120]


    base_parameter_labels = {
        'POPULATION_SIZES_STUDIED' : 'Population sizes',
        'STRUCTURE_PERIODIC_BOUNDARY' : 'Does the population structure have a periodic boundary condition?',
        'REPLICATIONS_PER_PARAM_SET' : 'Replicate simulation runs at each parameter combination',
        'NUMBER_OF_TRAITS_PER_DIMENSION': 'Number of traits per locus/dimension/feature',
        'NUMBER_OF_DIMENSIONS_OR_FEATURES': 'Number of loci/dimensions/features each individual holds',
        'SIMULATION_CUTOFF_TIME' : 'Maximum time after which a simulation is sampled and terminated if it does not converge',
    }


    def __init__(self, config_file):
        # if we don't give a configuration file on the command line, then we
        # just return a Configuration object, which has the default values specified above.
        if config_file is None:
            return

        # otherwise, we load the config file and override the default values with anything in
        # the config file
        try:
            json_data = open(config_file)
            self.config = json.load(json_data)
        except ValueError:
            print "Problem parsing json configuration file - probably malformed syntax"
            exit(1)
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
            exit(1)

        # we succeeded in loading the configuration, now override the default values of variables
        # given the contents of the configuration file
        for variable,value in self.config.iteritems():
            setattr(self, variable, value)

        # finalize the list of derived values
        self._calc_derived_values()


        # run-specific values common to all models
        self._popsize = None
        self._sim_id = None
        self._periodic = None
        self._script = None
        self._max_time = None
        self._sample_size = None

        # set up a global RNG everything can use
        self._prng = RandomState()

    @property
    def prng(self):
        return self._prng


    @property
    def script(self):
        return self._script

    @script.setter
    def script(self,s):
        self._script = s

    @property
    def periodic(self):
        return self._periodic

    @periodic.setter
    def periodic(self,p):
        self._periodic = p

    @property
    def sim_id(self):
        return self._sim_id

    @sim_id.setter
    def sim_id(self,id):
        self._sim_id = id


    @property
    def popsize(self):
        return self._popsize

    @popsize.setter
    def popsize(self, val):
        self._popsize = val

    @property
    def maxtime(self):
        return self._max_time

    @maxtime.setter
    def maxtime(self,val):
        self._max_time = val

    @property
    def sample_size(self):
        return self._sample_size

    @sample_size.setter
    def sample_size(self,val):
        self._sample_size = val


    def __repr__(self):
        attrs = vars(self)
        rep = '\n'.join("%s: %s" % item for item in attrs.items() if item[0] != "config")
        return rep

    def to_latex_table(self, experiment, **kwargs):
        """
        Constructs a LaTeX table and tabular environment for the simulation parameters and
        control variable settings.  A list of "internal" or unimplemented variables are
        filtered out of this list, and actual variable names are translated to human-readable
        phrases with a lookup table.

        Takes an optional named argument:  caption=String.  This parameter will replace
        the caption automatically generated by this method.

        :return: A string comprising the LaTeX representation for the parameters.

        """
        if 'caption' not in kwargs or kwargs['caption'] is None:
            caption_text = "\\caption{Parameters for CT Mixture Model simulations for Experiment Name: "
            caption_text += experiment
            caption_text += '}\n'
        else:
            caption_text = '\\caption{'
            caption_text += kwargs['caption']
            caption_text += '}\n'


        #if kwargs['caption'] is not None:
        #    caption_text = '\\caption{'
        #    caption_text += kwargs['caption']
        #    caption_text += '}\n'
        #else:
        #    caption_text = "\\caption{Parameters for Axelrod Simulations for Experiment Name: "
        #    caption_text += experiment
        #    caption_text += '}\n'


        t = []
        t.append('\\begin{table}[h]\n')
        t.append('\\begin{tabular}{|p{0.6\\textwidth}|p{0.4\\textwidth}|}\n')
        t.append('\\hline\n')
        t.append('\\textbf{Simulation Parameter} & \\textbf{Value or Values} \\\\ \n')
        t.append('\\hline\n')

        for var in self._get_public_variables():
            s = self.parameter_labels[var[0]]
            s += ' & '


            # need to know if var[1] is a single integer, or a list
            if hasattr(var[1], '__iter__'):
                s += ', '.join(map(str, var[1]))
            else:
                s += str(var[1])

            s += '\\\\ \n \\hline \n'
            t.append(s)


        t.append('\\hline\n')
        t.append('\\end{tabular}\n')
        t.append(caption_text)
        t.append('\\label{tab:seriationct-sim-parameters}\n')
        t.append('\\end{table}\n')

        return ''.join(t)

    def to_pandoc_table(self, experiment, **kwargs):
        """
        Constructs a Markdown table (in pandoc format) for the simulation parameters and
        control variable settings.  A list of "internal" or unimplemented variables are
        filtered out of this list, and actual variable names are translated to human-readable
        phrases with a lookup table.

        :return: Text string representing a Pandoc table
        """
        t = []

        t.append('| Simulation Parameter                   | Value or Values                                   |\n')
        t.append('|:---------------------------------------|:--------------------------------------------------|\n')

        for var in self._get_public_variables():
            s = '|    '
            s += self.parameter_labels[var[0]]
            s += '   |   '


            # need to know if var[1] is a single integer, or a list
            if hasattr(var[1], '__iter__'):
                s += ', '.join(map(str, var[1]))
            else:
                s += str(var[1])

            s += '  | \n'
            t.append(s)

        return ''.join(t)

    def _get_public_variables(self):
        attrs = vars(self)
        filtered = [item for item in attrs.items() if item[0] not in self.vars_to_filter]
        filtered.sort(key=itemgetter(0))
        return filtered

##########################################################################

class MixtureConfiguration(BaseConfiguration):
    """
    Defines a number of class level constants which serve as configuration for a set of simulation models.
    Each constant can be overriden by a JSON configuration file, which this class is responsible for
    parsing.  Given a JSON configuration file, the values for any constants defined in that file replace
    the default values given here -- but the names must match.

    This class also contains any logic required by a simulation model to calculate derived parameters -- i.e.,
    those values which the simulation model may treat as configuration but which are derived by calculation from
    user supplied parameter values.


    """

    NUMBER_OF_DIMENSIONS_OR_FEATURES = [100,200]
    """
    This is the number of "loci" or "features".  By analogy with classifications,
    these are also "dimensions".
    """

    NUMBER_OF_TRAITS_PER_DIMENSION = [500,1000]
    """
    This is the number of INITIAL traits from which each locus/feature is initialized.  The innovation
      rule class determines whether this is infinite or has a fixed number.
    """

    INNOVATION_RATE = [0.001,0.005]

    CONFORMISM_STRENGTH = [0.1, 0.2, 0.05, 0.3]

    ANTICONFORMISM_STRENGTH = [0.1, 0.2, 0.05, 0.3]

    parameter_labels = {
        'POPULATION_SIZES_STUDIED' : 'Population sizes',
        'STRUCTURE_PERIODIC_BOUNDARY' : 'Does the population structure have a periodic boundary condition?',
        'REPLICATIONS_PER_PARAM_SET' : 'Replicate simulation runs at each parameter combination',
        'SIMULATION_CUTOFF_TIME' : 'Maximum time after which a simulation is sampled and terminated if it does not converge',
        'NUMBER_OF_DIMENSIONS_OR_FEATURES' : 'Number of loci or dimensions per individual',
        'NUMBER_OF_TRAITS_PER_DIMENSION' : 'Number of traits per locus from which the population is initialized',
        'INNOVATION_RATE' : 'Population rate at which new innovations occur'
    }


    # For Latex or Pandoc output, we also filter out any object instance variables, and output only the class-level variables.
    vars_to_filter = ['config', '_prng', "_popsize", "_num_features", "_num_traits", "_sim_id", "_periodic", "_script",
                      "_innovation_rate", "_max_time", "_num_features", "_num_traits",
                      "INTERACTION_RULE_CLASS", "POPULATION_STRUCTURE_CLASS", "INNOVATION_RULE_CLASS",
                      "NETWORK_FACTORY_CLASS", "TRAIT_FACTORY_CLASS", "_conformism_strength", "_anticonformism_strength", "_sample_size"]
    """
    List of variables which are never (or at least currently) pretty-printed into summary tables using the latex or markdown/pandoc methods

    Some variables might be here because they're currently unused or unimplemented....
    """

    def __init__(self, config_file):

        super(MixtureConfiguration, self).__init__(config_file)

        # object properties for each specific run

        self._num_features = None
        self._num_traits = None
        self._innovation_rate = None
        self._conformism_strength = None
        self._anticonformism_strength = None


    @property
    def conformism_strength(self):
        return self._conformism_strength

    @conformism_strength.setter
    def conformism_strength(self, v):
        self._conformism_strength = v

    @property
    def anticonformism_strength(self):
        return self._anticonformism_strength

    @anticonformism_strength.setter
    def anticonformism_strength(self, v):
        self._anticonformism_strength = v

    @property
    def innovation_rate(self):
        return self._innovation_rate

    @innovation_rate.setter
    def innovation_rate(self, r):
        self._innovation_rate = r

    @property
    def num_features(self):
        return self._num_features

    @num_features.setter
    def num_features(self,val):
        self._num_features = val

    @property
    def num_traits(self):
        return self._num_traits

    @num_traits.setter
    def num_traits(self,val):
        self._num_traits = val



    def _calc_derived_values(self):
        """
        No known derived values right now....
        """
        pass


