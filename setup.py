#!/usr/bin/env python
# Copyright (c) 2015.  Mark E. Madsen <mark@madsenlab.org>
#
# This work is licensed under the terms of the Apache Software License, Version 2.0.  See the file LICENSE for details.

"""
Description here

"""

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages, Command
from setuptools.command.develop import develop
from setuptools.command.install import install

import subprocess
import os
import re
import shutil

# create a decorator that wraps the normal develop and
# install commands to first update the version

def versioned(command_subclass):
    """
    A decorator for ensuring that installations, whether through setup.py install
    or setup.py develop, always update the version number with the Git revision and
    most recent tag.

    :param command_subclass:
    :return:
    """
    VERSION_PY = """
# This file is updated from Git information by running 'python setup.py
# version'.
__version__ = '%s'
"""
    orig_callable = command_subclass.run

    def modified_callable(self):
        if not os.path.isdir(".git"):
            print "This does not appear to be a Git repository."
            return
        try:
            p = subprocess.Popen(["git", "describe",
                                  "--tags", "--always"],
                                 stdout=subprocess.PIPE)
        except EnvironmentError:
            print "unable to run git, leaving seriationct/_version.py alone"
            return
        stdout = p.communicate()[0]
        if p.returncode != 0:
            print "unable to run git, leaving seriationct/_version.py alone"
            return
        # our tags are like:  v2.2
        ver = stdout[len("v"):].strip()
        f = open("seriationct/_version.py", "w")
        f.write(VERSION_PY % ver)
        f.close()
        print "updated _version.py to '%s'" % ver
        orig_callable(self)




    command_subclass.run = modified_callable
    return command_subclass


@versioned
class CustomDevelopClass(develop):
    pass

@versioned
class CustomInstallClass(install):

    def run(self):
        zip_cmd = "zip -r seriationct-templates/seriationct-experiment-template.zip experiment-template >& /dev/null"
        os.system(zip_cmd)
        shutil.copy('admin/seriationct-create-experiment-directory.sh','/usr/local/bin/seriationct-create-experiment-directory')

        install.run(self)


def get_version():
    try:
        f = open("seriationct/_version.py")
    except EnvironmentError:
        return None
    for line in f.readlines():
        mo = re.match("__version__ = '([^']+)'", line)
        if mo:
            ver = mo.group(1)
            return ver
    return None


class VersionUpdate(Command):
    """setuptools Command"""
    description = "update version number"
    user_options = []


    def initialize_options(self):
        pass


    def finalize_options(self):
        pass


    def run(self):
        VERSION = """
# This file is updated from Git information by running 'python setup.py
# version'.
__version__ = '%s'
"""
        if not os.path.isdir(".git"):
            print "This does not appear to be a Git repository."
            return
        try:
            p = subprocess.Popen(["git", "describe",
                                  "--tags", "--always"],
                                 stdout=subprocess.PIPE)
        except EnvironmentError:
            print "unable to run git, leaving seriationct/_version.py alone"
            return
        stdout = p.communicate()[0]
        if p.returncode != 0:
            print "unable to run git, leaving seriationct/_version.py alone"
            return
        # our tags are like:  v2.2
        ver = stdout[len("v"):].strip()
        f = open("seriationct/_version.py", "w")
        f.write(VERSION % ver)
        f.close()
        print "updated _version.py to '%s'" % ver

setup(name="seriationct",
      version=get_version(),
      packages = find_packages(exclude=["admin","analytics","build","ca","networkmodeling","conf","doc","notebooks","simulations","test","testdata"]),
      scripts = [
          'admin/seriationct-simulation-builder.py',
          'admin/seriationct-explain-networkmodel.py',
          'admin/seriationct-seriation-builder.py',
          'admin/seriationct-simulation-export-builder.py',
          'analytics/seriationct-export-single-simulation.py',
          'analytics/seriationct-annotate-minmax-graph.py',
          'analytics/seriationct-sample-exported-datafiles.py',
          'analytics/seriationct-assemblage-duration-export.py',
          'analytics/seriationct-sample-assemblages-for-seriation.py',
          'analytics/seriationct-score-single-linear-network.py',
          'analytics/seriationct-filter-types.py',
          'analytics/seriationct-export-simids.py',
          'analytics/seriationct-finalize-seriation-input.py',
          'networkmodeling/graphbuilders/seriationct-build-clustered-network.py',
          'networkmodeling/graphbuilders/seriationct-build-lineage-splitting-network.py',
          'networkmodeling/graphbuilders/seriationct-build-complete-network.py',
          'networkmodeling/graphbuilders/seriationct-build-spatial-neighbor-network.py',
          'networkmodeling/samplers/seriationct-sampler-spatial-neighbor.py',
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
      ],
      license="APACHE",
      data_files=[('seriationct-template', ['seriationct-templates/seriationct-experiment-template.zip'])],
      cmdclass={ "version": VersionUpdate, "install": CustomInstallClass, "develop": CustomDevelopClass },
      )
