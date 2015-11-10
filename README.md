seriationct
==========

Framework for studying the quantitative linkage between regional-scale cultural transmission models
and the structures that show up in seriations.  The framework:

1.  Facilitates the construction of regional-scale settlement and contact models, in the form of temporal
network models where vertices represent communities and weighted edges represent the intensity of individual
movement between communities.  
1.  Executes simulations of neutral (and potentially other) social learning models within the "metapopulation"
represented by the regional-scale network model, saving samples of trait counts from each subpopulation at each 
time interval to a MongoDB database.  
1.  Facilitates various sampling schemes for extracting "class" frequencies (intersecting all traits) from the 
database to construct data sets which closely mimic time-averaged archaeological assemblages for technologies such
as pottery or stone tools.   The resulting data sets are suitable as input for the [IDSS algorithm](https://github.com/clipo/idss-seriation)
for archaeological seriation.
1.  Provides tools for annotating the results of IDSS seriation (e.g., minmax graphs from frequency or continuity 
seriation) with information originating in the regional network model, so that we can do statistical analyses of 
the "quality" or accuracy of the seriation result, or analyze differences in the structure of seriation solutions
given differences in the topology of the original regional network model.



