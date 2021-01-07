#!/bin/bash

#
#  ********************************************************************************
#   Copyright © 2020-2021, ETH Zurich, D-BSSE, Andreas P. Cuny & Aaron Ponti
#   All rights reserved. This program and the accompanying materials
#   are made available under the terms of the GNU Public License v3.0
#   which accompanies this distribution, and is available at
#   http://www.gnu.org/licenses/gpl
#
#   Contributors:
#     * Andreas P. Cuny - initial API and implementation
#     * Aaron Ponti - initial API and implementation
#  *******************************************************************************
#
INPUT_ROOT_FOLDER=__SET_YOUR_INPUT_FOLDER__
OUTPUT_ROOT_FOLDER=${INPUT_ROOT_FOLDER}

python collect_results.py -f ${INPUT_ROOT_FOLDER} -o ${OUTPUT_ROOT_FOLDER}
