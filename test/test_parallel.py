#!/usr/bin/env python
# Copyright (c) 2013.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

import logging as log
import unittest
import seriationct.utils as utils
import os
import tempfile
import argparse

log.basicConfig(level=log.INFO, format='%(asctime)s %(levelname)s: %(message)s')

class ParallelTest(unittest.TestCase):



    def test_parallel_cores(self):
        cores = utils.get_parallel_cores(dev_flag=True)
        self.assertTrue(isinstance(cores, int))
        self.assertLess(cores, 128, "cores more than 128, this is unlikely in testing")




if __name__ == "__main__":
    unittest.main()