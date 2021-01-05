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

ROOT_FOLDER=D:\\cunya\\Large_Study\\COVID_19_POCT

python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera1/100CANON/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera1/100CANON/sorted/ -w 8
echo "* * * * * Camera 1 completed. * * * * *"
python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera2/100EOS5D/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera2/100EOS5D/sorted/ -w 8
echo "* * * * * Camera 2 completed. * * * * *"
python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera3/100CANON/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera3/100CANON/sorted/ -w 8
echo "* * * * * Camera 3 completed. * * * * *"
python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera4/102MSDCF/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera4/102MSDCF/sorted/ -w 8
echo "* * * * * Camera 4 completed. * * * * *"
python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera6/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera6/sorted/ -w 8
echo "* * * * * Camera 6 completed. * * * * *"
python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera7/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera7/sorted/ -w 8
echo "* * * * * Camera 7 completed. * * * * *"
python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera8/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera8/sorted/ -w 8
echo "* * * * * Camera 8 completed. * * * * *"
python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera9/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera9/sorted/ -w 8
echo "* * * * * Camera 9 completed. * * * * *"
python ./split_images_by_strip_type_parallel.py -f ${ROOT_FOLDER}/Camera11/DCIM/100EOS5D/sorted/UNDEFINED/ -o ${ROOT_FOLDER}/Camera11/DCIM/100EOS5D/sorted/ -w 8
echo "* * * * * Camera 11 completed. * * * * *"

echo "* * * * * All done. * * * * *"
