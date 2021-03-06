#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import csv
import zipfile
import argparse
import logging as log
import os
import fnmatch
import math
import random
import numpy as np
import re
from collections import defaultdict
import networkx as nx
import seriationct.data as data


def setup():
    global args, config, simconfig
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", type=int, help="turn on debugging output")
    parser.add_argument("--inputfile", help="path to directory with IDSS format input files to sample", required=True)
    parser.add_argument("--outputdirectory", help="path to directory for sampled data files", required=True)
    parser.add_argument("--samplefraction", type=float, help="Sample size to resample frequencies for each sim run and replication", required=True)
    parser.add_argument("--sampletype", choices=['random', 'spatial', 'temporal', 'spatiotemporal','complete','excludelist','slicestratified'],
                        help="type of sampling.  random has no stratification, temporal is rough early/late stratification, spatial is"
                            "quadrants, spatiotemporal is stratification by both, complete preserves all rows, excludelist returns all rows except those given in a file", required=True)
    parser.add_argument("--excludefile", help="File of assemblage names to exclude from the input list")
    parser.add_argument("--numsamples", type=int, help="number of samples to take from each original data set (default is 1)", default=1)
    parser.add_argument("--temporaldata", help="path to directory with temporal data files to match files in inputdirectory "
                                               "(required for temporal or spatiotemporal sampling")
    parser.add_argument("--temporalperiods", type=int, help="Number of temporal periods in which to stratify the sample", default=3)
    parser.add_argument("--spatialquadrats", type=int, help="Number of blocks in the X and Y directions in which to stratify the sample", default=3)
    parser.add_argument("--spatialdata", help="path to XY file of spatial coordinates for assemblages")
    parser.add_argument("--maxsizespatial", type=int, help="Maximum size of spatial coordinates in X and Y directions", default=1100)
    parser.add_argument("--experiment", help="provide name for experiment, to be used as prefix for database collections")
    parser.add_argument("--dbhost", help="database hostname, defaults to localhost", default="localhost")
    parser.add_argument("--dbport", help="database port, defaults to 27017", default="27017")




    args = parser.parse_args()

    if args.debug == 1:
        log.basicConfig(level=log.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
    else:
        log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')


############################## utility methods ###########################

def _parse_networkmodel(path):
    network_slices = dict()

    zf = zipfile.ZipFile(path, 'r')

    for file in [f for f in zf.namelist() if f.endswith(".gml")]:
        m = re.search('(?!\-)(\d+)\.gml', file)
        file_number = m.group(1)
        log.debug("Parsing GML file %s:  file number %s", file, file_number)

        gml = zf.read(file)
        slice = nx.parse_gml(gml)
        #log.debug("slice nodes: %s", '|'.join(sorted(slice.nodes())))
        network_slices[int(file_number)] = slice

    return network_slices


def parse_filename_into_root(filename):
    base = os.path.basename(filename)
    root, ext = os.path.splitext(base)
    return root

def get_uuid_from_root(root):
    occur = 5  # get the UUID, so fifth occurrence of "-"

    indices = [x.start() for x in re.finditer("-", root)]
    uuid_part = root[0:indices[occur-1]]
    rest = root[indices[occur-1]+1:]
    return uuid_part


def read_unsampled_file(filename):
    """
    Reads the unsampled export file, and produces a header row, and a list of rows for further sampling

    """
    assemblage_to_row = dict()
    with open(filename, 'r') as incsv:
        csvread = csv.reader(incsv, delimiter="\t")

        header_row = csvread.next()
        header_str = '\t'.join(header_row)
        header_str += '\n'

        row_list = []
        row_idx = 0
        for row in csvread:
            row_list.append(row)
            assemblage_to_row[row[0]] = row_idx
            row_idx += 1

    log.debug("assemblage_to_row: %s", assemblage_to_row)

    return (header_str, row_list,assemblage_to_row)

def build_regular_blocks(numblocks,max):
    """
    Construct block boundaries for use in spatial sampling.  The block
    boundaries will be the same in the X and Y directions, forming numblocks
    quadrats in the overall space.  The maximum space size is extended slightly to
    account for the spread of nodes around centroids.
    """
    block_boundaries = []
    block_width = float(max + 100) / float(numblocks)
    lower_val = 0.0
    upper_val = 0.0
    for block in range(0, numblocks):
        upper_val += block_width
        block_boundaries.append((lower_val, upper_val))
        lower_val = upper_val
    #log.debug("boundaries: %s", block_boundaries)
    return block_boundaries

def split_list(a, n):
    k, m = len(a) / n, len(a) % n
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in xrange(n))

def read_temporal_data(temporal_path):
    origin_map = dict()
    origin_to_assemblages = defaultdict(list)
    duration_map = dict()
    with open(temporal_path, 'r') as tempcsv:
        csvread = csv.reader(tempcsv, delimiter='\t')

        header = csvread.next()

        for row in csvread:
            origin_map[row[0]] = int(row[1])
            duration_map[row[0]] = int(row[2])
            origin_to_assemblages[row[1]].append(row[0])

    #log.debug("origin_to_assemblages: %s", origin_to_assemblages)

    return (origin_map,duration_map,origin_to_assemblages)


def read_spatial_xyfile():
    """
    Read XY file of spatial coordinates for assemblages and return a dict where
    the assemblage name is key, and the value is a tuple (x,y).  We use this
    method because in real situations, the coordinates will not be part of the
    assemblage names
    """
    assemblage_coordinates = dict()
    with open(args.spatialdata, 'r') as xyfile:
        csvread = csv.reader(xyfile, delimiter='\t')

        header = csvread.next()

        for row in csvread:
            x = int(row[1])
            y = int(row[2])
            #log.debug("x: %s y: %s", x,y)
            assemblage_coordinates[row[0]] = (x,y)

    #log.debug("assemblage_coordinates: %s", assemblage_coordinates)

    return assemblage_coordinates


def get_quadrat_for_coordinates(coordinates, block_boundaries):
    """
    Given a tuple of x,y coordinates for an assemblage, returns a block ID
    given the block boundaries
    """
    x = float(coordinates[0])
    y = float(coordinates[1])

    xblock = None
    yblock = None

    # calculate the block in the x and y directions
    for i in range(0,len(block_boundaries)):
        block = block_boundaries[i]
        if block[0] <= x < block[1]:
            xblock = i

    for i in range(0,len(block_boundaries)):
        block = block_boundaries[i]
        if block[0] <= y < block[1]:
            yblock = i


    return (xblock,yblock)




############################## sampling methods ###########################

def complete_inventory(row_list, assemblage_to_row):
    """
    A null method which simply returns all of the input rows.  This can be
    useful for doing verification testing, or if there are a small number of input
    assemblages, but we want to still feed simulation output through a common
    data preparation pipeline for seriation.

    """
    return assemblage_to_row.values()


def exclude_assemblage_list(row_list, exclude_file_path, assemblage_to_row):
    """
    A method for excluding specific assemblages from the sample.  This is useful mainly
    for testing and calibration, where we might want to see what the effect is of excluding
    specific assemblages.

    """
    sampled_rows = []
    exclude_assemblages = []
    with open(exclude_file_path, mode='r') as exclude_file:
        for e in exclude_file:
            assem = e.strip()
            log.debug("Exclude assemblage: %s", assem)
            exclude_assemblages.append(assem)

    log.debug("exclude assemblages: %s", exclude_assemblages)

    for row in row_list:
        if row[0] not in exclude_assemblages:
            sampled_rows.append(assemblage_to_row[row[0]])

    return sampled_rows



def random_sample_without_stratification(row_list):
    """
    Takes a uniform random sample of rows without any stratification
    Returns a list of row indices that can be used to select the
    sample points from the original rows in the file
    """
    num_rows = len(row_list)

    num_samples = int(math.ceil(args.samplefraction * num_rows))
    log.info("Taking %s samples from file %s", num_samples, file)

    sampled_rows = random.sample(range(0, num_rows), num_samples)
    log.debug("Sampling rows: %s", sampled_rows)

    return sampled_rows


def random_sample_per_slice_stratification(row_list, assemblage_to_row, file):
    """
    Takes a fraction of nodes of size args.samplefraction from each slice, so that each
    time slice in a set of assemblages is represented.  Mainly useful for simple, stylized
    network models used to study the underlying behavior of seriations.  We assume for
    simplicity a static population size of nodes per slice, which is consistent with the
    builder program.
    """
    sampled_rows = []
    networkmodel = get_networkmodel_for_input(file)
    slices = _parse_networkmodel(networkmodel)
    num_nodes = slices[1].number_of_nodes()
    sample_per_slice = int(args.samplefraction * num_nodes)
    log.debug("number of assemblages to sample per slice: %s", sample_per_slice)

    for slice in slices.values():
        assem = []
        for node, data in slice.nodes_iter(data=True):
            assem.append(slice.node[node]['label'])
        sample = random.sample(assem, sample_per_slice)
        log.debug("sample for slice %s:  %s", slice, sample)
        sampled_rows.extend([assemblage_to_row[x] for x in sample])

    log.debug("sampled_rows: %s", sampled_rows)

    return sampled_rows


def random_temporal_sample(row_list, root, assemblage_to_row):
    """
    Takes a uniform random sample, stratified by splitting assemblages
    into N periods.
    """
    uuid = get_uuid_from_root(root)
    temporal_file = uuid + "-assemblage-data.txt"
    temporal_path = args.temporaldata + "/" + temporal_file
    log.debug("using temporal data: %s", temporal_path)

    (origin_map,duration_map,origin_to_assemblages) = read_temporal_data(temporal_path)

    #log.debug("origin_map: %s", origin_map)

    times = set()
    times.update(origin_map.values())
    sorted_times = sorted(list(times))

    period_lists = list(split_list(sorted_times, args.temporalperiods))

    log.debug("Periods to stratify the temporal sample by: %s", period_lists)

    sampled_assemblages = []
    for periods in period_lists:
        assemblages_in_period_list = []
        log.debug("periods: %s", periods)
        for time in periods:
            assemblages_in_period_list.extend(origin_to_assemblages[str(time)])

        log.debug("assemblages in period list: %s", assemblages_in_period_list)
        num_samples = int(math.ceil(args.samplefraction * len(row_list)) / len(period_lists))

        period_sample = random.sample(assemblages_in_period_list, num_samples)

        sampled_assemblages.extend(period_sample)

    log.debug("sampled assemblages: %s", sampled_assemblages)

    sampled_indices = []
    for assem in sampled_assemblages:
        sampled_indices.append(assemblage_to_row[assem])

    log.debug("sampled indices %s", sampled_indices)
    return sampled_indices


def random_spatial_sample(row_list, assemblage_to_row):
    """
    Takes a uniform random sample, stratified by splitting space into quadrats
    with T blocks in the X and Y spatial directions.
    """
    coordinates_map = read_spatial_xyfile()

    # build a list of tuples of the block boundaries
    quadrat_boundaries = build_regular_blocks(args.spatialquadrats, args.maxsizespatial)

    log.debug("quadrat boundaries: %s", quadrat_boundaries)

    num_blocks_each_direction = len(quadrat_boundaries)

    assemblages_by_quadrat = defaultdict(list)

    for row in row_list:
        assemblage = row[0]
        coord = coordinates_map[assemblage]
        quadrat = get_quadrat_for_coordinates(coord,quadrat_boundaries)
        assemblages_by_quadrat[quadrat].append(assemblage)

    log.debug("assemblages by quadrat: %s", assemblages_by_quadrat)

    # now we take an appropriate number of samples from each quadrat
    num_samples = int(math.ceil(args.samplefraction * len(row_list)) / len(assemblages_by_quadrat))
    log.debug("Number of assemblages sampled per quadrat: %s", num_samples)

    sampled_assemblages = []
    for quadrat_population in assemblages_by_quadrat.values():

        log.debug("quadrat population: %s", quadrat_population)

        num_assem_in_quadrat = len(quadrat_population)
        if num_samples > num_assem_in_quadrat:
            num_samples = num_assem_in_quadrat

        quadrat_sample = random.sample(quadrat_population, num_samples)
        log.debug("quadrat_sample: %s", quadrat_sample)
        sampled_assemblages.extend(quadrat_sample)

    sampled_indices = []
    for assem in sampled_assemblages:
        sampled_indices.append(assemblage_to_row[assem])

    log.debug("sampled indices: %s", sampled_indices)
    return sampled_indices


def random_spatiotemporal_sample(row_list, assemblage_to_row):
    """
    Combines spatial and temporal sampling
    """
    log.debug("========== begin spatiotemporal sample ================")
    uuid = get_uuid_from_root(root)
    temporal_file = uuid + "-assemblage-data.txt"
    temporal_path = args.temporaldata + "/" + temporal_file
    log.debug("using temporal data: %s", temporal_path)

    (origin_map,duration_map,origin_to_assemblages) = read_temporal_data(temporal_path)

    #log.debug("origin_map: %s", origin_map)

    times = set()
    times.update(origin_map.values())
    sorted_times = sorted(list(times))

    period_lists = list(split_list(sorted_times, args.temporalperiods))

    log.debug("Periods to stratify the temporal sample by: %s", period_lists)


    coordinates_map = read_spatial_xyfile()

    # build a list of tuples of the block boundaries
    quadrat_boundaries = build_regular_blocks(args.spatialquadrats, args.maxsizespatial)

    log.debug("quadrat boundaries: %s", quadrat_boundaries)

    num_blocks_each_direction = len(quadrat_boundaries)

    assemblages_by_quadrat = defaultdict(list)

    for row in row_list:
        assemblage = row[0]
        coord = coordinates_map[assemblage]
        quadrat = get_quadrat_for_coordinates(coord,quadrat_boundaries)
        assemblages_by_quadrat[quadrat].append(assemblage)

    #log.debug("assemblages by quadrat: %s", assemblages_by_quadrat)

    # calculate number of assemblages per quadrat per period
    num_spatial_samples = int(math.ceil(args.samplefraction * len(row_list)) / len(assemblages_by_quadrat))
    num_samples = num_spatial_samples / len(period_lists)
    log.debug("Number of assemblages sampled per quadrat per period: %s", num_samples)

    sampled_assemblages = []
    for quadrat_population in assemblages_by_quadrat.values():
        log.debug("Starting quadrat sample ==============================")
        log.debug("quadrat population: %s", quadrat_population)
        quadrat_sample = []
        for periods in period_lists:
            assemblages_in_period_list = []
            quadrat_period_list = []
            log.debug("periods: %s", periods)
            for time in periods:
                # filter the assemblages that exist in this period to only include those in
                # this quadrat
                assemblages_in_period_list.extend(origin_to_assemblages[str(time)])
                quadrat_period_list.extend( [a for a in assemblages_in_period_list if a in quadrat_population] )

            log.debug("assemblages in quadrat and period: %s", quadrat_period_list)

            #if num_samples >= len(quadrat_period_list):
            #    num_samples = len(quadrat_period_list)
            if len(quadrat_period_list) == 0:
                continue

            log.debug("taking %s samples from this quadrat and period", num_samples)

            period_quadrat_sample = random.sample(quadrat_period_list, num_samples)
            log.debug("period/quadrat sample: %s", period_quadrat_sample)
            quadrat_sample.extend(period_quadrat_sample)
        log.debug("quadrat sample: %s", quadrat_sample)
        sampled_assemblages.extend(quadrat_sample)

    sampled_indices = set()
    for assem in sampled_assemblages:
        sampled_indices.add(assemblage_to_row[assem])

    log.debug("sampled indices: %s", sampled_indices)
    return list(sampled_indices)



def get_networkmodel_for_input(file):
    sampled_obj = data.SampledSimulationData.objects(output_file = file).first()
    sim_id = sampled_obj.simulation_run_id
    sim_run = data.SimulationRunMetadata.objects(simulation_run_id = sim_id).first()
    networkmodel = sim_run.networkmodel
    return networkmodel


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
    sm_db = data.SimulationMetadataDatabase(db_args)


    log.info("Starting processing of %s", args.inputfile)
    full_fname = args.inputfile
    root = parse_filename_into_root(args.inputfile)

    (header, row_list,assemblage_to_row) = read_unsampled_file(full_fname)
    log.debug("header: %s", header)

    # create N independent samplings from each input file
    for sample_num in range(0, args.numsamples):
        outputfile = args.outputdirectory + "/" + root + "-" + args.sampletype  +"-" + str(args.samplefraction) + "-assemsample-" + str(sample_num) + ".txt"

        if args.sampletype == 'random':
            sampled_rows = random_sample_without_stratification(row_list)
        elif args.sampletype == 'spatial':
            sampled_rows = random_spatial_sample(row_list, assemblage_to_row)
        elif args.sampletype == 'temporal':
            sampled_rows = random_temporal_sample(row_list, root, assemblage_to_row)
        elif args.sampletype == 'spatiotemporal':
            sampled_rows = random_spatiotemporal_sample(row_list, assemblage_to_row)
        elif args.sampletype == 'complete':
            sampled_rows = complete_inventory(row_list, assemblage_to_row)
        elif args.sampletype == 'excludelist':
            sampled_rows = exclude_assemblage_list(row_list, args.excludefile, assemblage_to_row)
        elif args.sampletype == 'slicestratified':
            sampled_rows = random_sample_per_slice_stratification(row_list, assemblage_to_row,full_fname)

        log.info("Writing sampled output for file: %s ", outputfile)

        with open(outputfile, 'wb') as outfile:
            outfile.write(header)

            for row_idx in sampled_rows:
                row = row_list[row_idx]
                row_str = '\t'.join(row)
                row_str += '\n'
                outfile.write(row_str)


    pp_db.store_assemblage_sampled_datafile(full_fname, args.sampletype, args.samplefraction, outputfile)
    log.info("Completed processing of file %s", full_fname)

