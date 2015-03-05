#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""
from distutils.core import setup

setup(name="seriationct",
      version="1.0",
      packages = [
        'seriationct',
        'seriationct.data',
        'seriationct.utils',
        'seriationct.demography',
        'seriationct.sampling'
      ],
      scripts = [
          'admin/seriationct-runbuilder.py',
          'admin/seriationct-explain-networkmodel.py',
          'analytics/seriationct-export-data.py',
          'graphs/seriationct-create-networkmodel.py',
          'simulations/sim-seriationct-networkmodel.py',
      ],
      author='Mark E. Madsen',
      author_email='mark@madsenlab.org',
      url='https://github.com/mmadsen/seriationct',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2.7',
          'Topic :: Scientific/Engineering',
      ]
      )
