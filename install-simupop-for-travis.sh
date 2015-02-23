#!/bin/sh
set -ex
cd /tmp
wget --no-check-certificate http://iweb.dl.sourceforge.net/project/simupop/simupop/1.1.2/simuPOP-1.1.2.Ubuntu13-x86_64.tar.gz -O simupop-1.1.2.tar.gz
# don't ask me why it errors without this, it's a bad package build
sudo tar -xzf simupop-1.1.2.tar.gz
# leaves a directory rooted at usr/
# this is simply a binary install, which needs to be added to the python path

