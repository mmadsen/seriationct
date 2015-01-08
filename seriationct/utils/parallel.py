#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

def get_parallel_cores(dev_flag):
    import multiprocessing
    cores = multiprocessing.cpu_count()
    if(dev_flag == 1):
        cores /= 2
    return cores
