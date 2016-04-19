#!/usr/bin/env python

import seriationct.data as data
import os
import fnmatch
import sys

database = "sc-pnn-1000"
database += "_samples_raw"
db_args = {}
db_args['dbhost'] = 'localhost'
db_args['dbport'] = 27017
db_args['database'] = database
db_args['dbuser'] = None
db_args['dbpassword'] = None
pp_db = data.PostProcessingDatabase(db_args)



def delete_duplicate_entry(fname):
	obj = data.ExportedSimulationData.objects(output_file=fname)
	print "num duplicates: %s" % obj.count()
	entries = obj.all()
	second = entries[1]
	second.delete()



for file in os.listdir("exported-data"):
    if fnmatch.fnmatch(file, '*.txt'):
        full_fname = "exported-data"
        full_fname += "/"
        full_fname += file

        try:
        	export_obj = data.ExportedSimulationData.objects.get(output_file=full_fname)
        except:
        	print "duplicate: %s" % full_fname
        	delete_duplicate_entry(full_fname)


