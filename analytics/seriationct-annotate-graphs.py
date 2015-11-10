#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import seriationct.analytics as sa
from seriation.database import SeriationDatabase, SeriationFileLocations, SeriationRun

import csv
import argparse
import logging as log
import zipfile
import networkx as nx
from mongoengine import *
import itertools
from networkx.utils import open_file, make_str
import os
from decimal import *
from re import compile
import pprint as pp


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--networkmodel", help="path to ZIP format network model containing GML slices", required=True)
    parser.add_argument("--modeltype", choices=['hierarchy', 'other', 'clustered', 'lineage'], required=True, default='other')
    parser.add_argument("--experiment", help="Experiment name, used to label graphics", required=True)
    parser.add_argument("--graphtype", choices=['minmaxbyweight', 'minmaxbycount', 'sumgraphbycount', 'sumgraphbyweight'], default="minmaxbyweight")
    parser.add_argument("--seriationtype", choices=['frequency', 'continuity', 'both'], default='frequency')
    parser.add_argument("--dbhost", help="MongoDB database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="MongoDB database port, defaults to 27017", type=int, default="27017")
    parser.add_argument("--database", help="Name of IDSS-generated database of seriation runs to annotate", required=True)
    parser.add_argument("--dbuser", help="Username on MongoDB database server, optional")
    parser.add_argument("--dbpassword", help="Password on MongoDB database server, optional")
    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


    connect(db = args.database,
            host = args.dbhost,
            port = args.dbport,
            username = args.dbuser,
            password = args.dbpassword)



def process_file(gmlfile):
    """
    Process a single GML file from the database

    :param gmlfile:
    :return:
    """
    pass



def create_worklist():
    """
    Using the graphtype and seriationtype arguments, construct a list of file paths to process
    from the database.

    :return: list of files to process
    """

    # We might do both, or only one type of solution, so just iterate over a 1 or 2
    # element list
    stype = []
    if args.seriationtype == 'both':
        stype.append('frequency')
        stype.append('continuity')
    else:
        stype.append(args.seriationtype)


    filelist = []

    for type in stype:
        tag = type + args.graphtype

        # iterate over documents which contain this tag, then pull the filename
        # associated with the tag







if __name__ == "__main__":
    setup()

    # connect to the database and to the DB specified on the command line
    # the collection itself is specified by mongoengine, which is magical
    db = SeriationDatabase(args)

    for srun in SeriationRun.objects:


        process_file(gmlfile)








    # parse the inputfile and calculate the output file name
    input_basename = os.path.basename(args.inputfile)
    root, ext = os.path.splitext(input_basename)
    input_path = os.path.dirname(args.inputfile)
    path_components = os.path.split(input_path)

    sample_type = path_components[-2]
    # if the path element is the start of a ./path or /path, trim the path characters
    sample_type = sample_type.strip('./')

    log.debug("root: %s sampletype: %s", root, sample_type)

    graph_title = sa.get_graphics_title(root, sample_type)


    if input_path is '':
        input_path = '.'
    output_filename = input_path + '/' + root + "-annotated.gml"
    log.info("Processing input %s to output %s", input_basename, output_filename)

    # read the minmax input file
    mm = sa.read_gml_and_normalize_floats(args.inputfile)

    # parse the slices in the networkmodel
    zf = zipfile.ZipFile(args.networkmodel, 'r')
    for file in [f for f in zf.namelist() if f.endswith(".gml")]:
        if file.startswith("__"):
            pass
        else:
            gml = zf.read(file)
            slice = sa.parse_gml_and_normalize_floats(gml)

            sa.copy_attributes_to_minmax(g_slice = slice, g_mm = mm)


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




