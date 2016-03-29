#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import seriationct.analytics as sa
import seriationct.data as data

import csv
import argparse
import logging as log
import zipfile
import networkx as nx
from networkx.utils import open_file, make_str
import os
from decimal import *
from re import compile
import pprint as pp

# IDSS package
from seriation.database import SeriationRun, SeriationFileLocations

def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--modeltype", choices=['hierarchy', 'other', 'clustered', 'lineage'], required=True, default='other')
    parser.add_argument("--experiment", help="Experiment name, used to label graphics", required=True)
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")
    parser.add_argument("--addlabel", help="Optional label to be added to diagrams", type=str)

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')



def process_single_file(inputfile, network_model):
    # parse the inputfile and calculate the output file name
    input_basename = os.path.basename(inputfile)
    root, ext = os.path.splitext(input_basename)
    input_path = os.path.dirname(inputfile)
    path_components = os.path.split(input_path)

    sample_type = path_components[-2]
    # if the path element is the start of a ./path or /path, trim the path characters
    sample_type = sample_type.strip('./')

    log.debug("root: %s sampletype: %s", root, sample_type)

    graph_title = sa.get_graphics_title(root, sample_type, args.experiment, args.modeltype, args.addlabel)

    if input_path is '':
        input_path = '.'
    output_filename = input_path + '/' + root + "-annotated.gml"
    log.info("Processing input %s to output %s", input_basename, output_filename)

    # read the minmax input file
    mm = sa.read_gml_and_normalize_floats(inputfile)

    # parse the slices in the networkmodel
    zf = zipfile.ZipFile(network_model, 'r')
    for file in [f for f in zf.namelist() if f.endswith(".gml")]:
        if file.startswith("__"):
            pass
        else:
            gml = zf.read(file)
            slice = sa.parse_gml_and_normalize_floats(gml)

            sa.copy_attributes_to_minmax(slice, mm, args.modeltype)

    # now save the annotated graph to a file in GML format
    nx.write_gml(mm, output_filename)

    if args.modeltype == 'hierarchy':
        # for hierarchical models, label them with their level and child groupings and
        # write a graph to the filesystem
        gv_annotated = sa.get_hierarchy_level_annotated_graphviz(mm, 'rdylgn11')
        dot_filename = input_path + '/' + root + "-annotated-hierarchy.dot"
        png_filename = input_path + '/' + root + "-annotated-hierarchy.png"
    elif args.modeltype == 'other':
        # for other models, annotate the graph with origin time and duration of assemblages
        gv_annotated = sa.get_nonhierarchical_oldstyle_annotated_graphviz(mm)
        dot_filename = input_path + '/' + root + "-annotated-chronological.dot"
        png_filename = input_path + '/' + root + "-annotated-chronological.png"
    elif args.modeltype == 'clustered':
        gv_annotated = sa.get_clustered_annotated_graphviz(mm)
        dot_filename = input_path + '/' + root + "-clustered-annotated-chronological.dot"
        png_filename = input_path + '/' + root + "-clustered-annotated-chronological.png"
    elif args.modeltype == 'lineage':
        gv_annotated = sa.get_lineage_annotated_graphviz(mm)
        dot_filename = input_path + '/' + root + "-lineage-annotated-chronological.dot"
        png_filename = input_path + '/' + root + "-lineage-annotated-chronological.png"

    sa.write_ordered_dot(gv_annotated, dot_filename, name=graph_title)

    cmd = "neato -Tpng "
    cmd += dot_filename
    cmd += " -o "
    cmd += png_filename

    os.system(cmd)
    return (output_filename,png_filename)



if __name__ == "__main__":
    setup()

    database = args.experiment
    database += "_samples_raw"
    db_args = {}
    db_args['dbhost'] = args.dbhost
    db_args['dbport'] = args.dbport
    db_args['database'] = database
    db_args['dbuser'] = None
    db_args['dbpassword'] = None
    pp_db = data.PostProcessingDatabase(db_args)


    sruns = SeriationRun.objects
    for srun in sruns:
        id = srun.seriation_run_id
        floc = srun.file_locations

        contmbw_gml = floc.continuityminmaxbyweightgmlfile
        freqmbw_gml = floc.frequencyminmaxbyweightgmlfile

        log.debug("source_identifier: %s", srun.source_identifier)

        # get the network model from the seriation_input_data table
        sinput = data.SeriationInputData.objects.get(source_identifier = srun.source_identifier)
        network_model = sinput.network_model_path
        sinput_file = sinput.seriation_input_file

        log.debug("network model: %s", network_model)

        if contmbw_gml is not None:
            output_filename, png_filename = process_single_file(contmbw_gml, network_model)

            annot = {}
            annot['cont_network_model_annotated_gml'] = output_filename
            annot['cont_network_model_annotated_png'] = png_filename
            pp_db.store_seriation_annotation(sinput_file, srun.source_identifier,id,annot)

            log.info("srun: %s  cont mbw gml: %s", id, contmbw_gml)
        if freqmbw_gml is not None:
            output_filename, png_filename = process_single_file(freqmbw_gml, network_model)
            log.info("srun: %s  freq mbw gml: %s", id, freqmbw_gml)

            annot = {}
            annot['freq_network_model_annotated_gml'] = output_filename
            annot['freq_network_model_annotated_png'] = png_filename
            pp_db.store_seriation_annotation(sinput_file, srun.source_identifier,id,annot)



