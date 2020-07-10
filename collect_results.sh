#!/bin/bash

# ROOT INPUT AND OUTPUT FOLDERS
INPUT_ROOT_FOLDER=/mnt/store/data/covid/results/Large_Study/COVID_19_POCT/
OUTPUT_ROOT_FOLDER=${INPUT_ROOT_FOLDER}

python collect_results.py -f ${INPUT_ROOT_FOLDER} -o ${OUTPUT_ROOT_FOLDER}
