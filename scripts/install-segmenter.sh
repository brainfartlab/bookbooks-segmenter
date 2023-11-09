#!/bin/bash
WHEEL=$(find /opt/segmenter/segmenter/dist -type f -name "*.whl")

source activate pytorch
pip install $WHEEL
