#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Analysis script for processing "sample size series" experiments, where a single set of assemblages is progressively
seriated, removing an assemblage each time, to examine how the seriation solutions change with increasing sample size.

The assumption is that --inputdirectory points to a directory which contains many subdirectories of IDSS seriation
output, each subdirectory containing the output files from a single seriation run.  The subdirectory names have the
format:

c9c20a98-dcc2-11e4-94d2-b8f6b1154c9b-0-sampled-500-spatiotemporal-resample-size-9

where:

c9c20a98-dcc2-11e4-94d2-b8f6b1154c9b  is the simulation run UUID
0 is the replicate number
500 is the number of virtual artifacts sampled from the time averaged simulation output of the simulation
spatiotemporal is the method by which assemblages were sampled
9 is the number of assemblages retained in this particular seriation solution, ranging between some minimum and the total number of assemblages originally sampled (usually something in the high 20's or low 30's)



"""

import argparse
import logging as log
import zipfile
import networkx as nx
import os
from decimal import *
from re import compile
import pprint as pp


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--inputdirectory", help="path to directory containing subdirectories with seriation results", required=True)
    parser.add_argument("--experiment", help="Experiment name", required=True)
    #parser.add_argument("--")

    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

"""
Results of annotated GML for annotation type: lineage

  node [
    id 5
    label "assemblage-162-850"
    xCoordinate 850.0
    lineage_id "0"
    appears_in_slice "5"
    yCoordinate 162.0
    name "assemblage-162-850"
    cluster_id "0"
    size 500.0
  ]

"""