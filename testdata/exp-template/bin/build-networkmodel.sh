#!/bin/sh

echo "========================================================="
echo "  Sampling random network models from config"
echo "========================================================="

mkdir -p rawnetworkmodels
mkdir -p networkmodels


seriationct-sampler-spatial-neighbor.py \
    --experiment test3 \
    --netmodelconfig network-model-configuration-nnmodel.json \
    --rawnetworkmodelspath rawnetworkmodels \
    --compressednetworkmodelspath networkmodels \
    --xyfilespath xyfiles \
    --nummodels 4 \
    --debug 0


#seriationct-explain-networkmodel.py \
#	--networkmodel networkmodels/test3-network.zip



