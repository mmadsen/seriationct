#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
import math
from parallel import get_parallel_cores
from exceptions import format_exception


# Function for testing the partial or total ordering of a list of numbers

def strictly_increasing(L):
    return all(x<y for x, y in zip(L, L[1:]))

def strictly_decreasing(L):
    return all(x>y for x, y in zip(L, L[1:]))

def non_increasing(L):
    return all(x>=y for x, y in zip(L, L[1:]))

def non_decreasing(L):
    return all(x<=y for x, y in zip(L, L[1:]))


def simulation_burnin_time(popsize, innovrate):
    """
    Calculates burnin time, and rounds it to the nearest 1000 generation interval.

    :param popsize:
    :param innovrate:
    :return:
    """
    tmp = (9.2 * popsize) / (innovrate + 1.0) # this is conservative given the original constant is for the diploid process
    return int(math.ceil(tmp / 1000.0)) * 1000

