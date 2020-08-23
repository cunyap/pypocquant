from setuptools import setup

setup(
    name='pyPOCQuant',
    version='0.0.1',
    packages=['pyPOCQuant', 'pyPOCQuant.lib'],
    url='',
    license='t.b.a.',
    author='Andreas P. Cuny; Aaron Ponti',
    author_email='andreas.cuny@bsse.ethz.ch; aaron.ponti@bsse.ethz.ch',
    description='Pipline to batch detect and quantify point of care test strips from images',
    install_requires=[
        'opencv-python==3.4.2.16',
        'opencv-contrib-python==3.4.2.16',
        # 'opencv-python==4.1.1.26',
        # 'opencv-contrib-python==4.1.1.26',
        # 'opencv-contrib-python-nonfree==4.1.1.1',
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
        'jupytext'
    ],
)

