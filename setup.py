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

from setuptools import setup

setup(
    name='pyPOCQuant',
    version='0.0.1',
    packages=['pyPOCQuant', 'pyPOCQuant.lib'],
    url='',
    license='GPLv3',
    author='Andreas P. Cuny; Aaron Ponti',
    author_email='andreas.cuny@bsse.ethz.ch; aaron.ponti@bsse.ethz.ch',
    description='Pipline to batch detect and quantify point of care test strips from images',
    install_requires=[
        'opencv-python==3.4.2.16',
        'opencv-contrib-python==3.4.2.16',
        'exifread',
        'imutils',
        'matplotlib',
        'numpy',
        'scipy',
        'pytesseract',
        'imageio',
        'rawpy',
        'pyzbar',
        'tqdm',
        'pandas',
        'scikit-learn',
        'scikit-image',
        'pyqt==5.9.2',
        'nbconvert',
        'jupytext',
        'pytest'
    ],
)

