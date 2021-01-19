[![made-with-python](https://img.shields.io/badge/Made%20with-Python-brightgreen.svg)](https://www.python.org/) [![made-with-python3.6](https://img.shields.io/pypi/pyversions/pyimd.svg)](https://www.python.org/) [![supported-platform](https://img.shields.io/badge/platform-linux--x64%20%7C%20osx--x64%20%7C%20win--x64-lightgrey.svg)]() [![License](https://img.shields.io/badge/license-GPLv3-brightgreen.svg)](https://git.bsse.ethz.ch/cunya/pypocquantui/master/LICENSE) [![Documentation Status](https://readthedocs.org/projects/pypocquant/badge/?version=latest)](https://pypocquant.readthedocs.io/en/latest/?badge=latest)

pyPOCQuant  - A tool to automatically quantify Point-Of-Care Tests from images
======================================
written by `Andreas P. Cuny` and `Aaron Ponti`

This repository contains the implementation of the computer vision library *pyPOCQuant* to automatically detect and quantify test line (TL) signal bands from lateral flow assays (LFA) images,  as described in the paper: 




* Cuny, A. P., Rudolf, F., & Ponti, A. (2020). pyPOCQuant - A tool to automatically quantify Point-Of-Care Tests from images. MedRxiv,. https://doi.org/10.1101/2020.11.08.20227470



Please [cite the paper(s)](https://www.medrxiv.org/content/10.1101/2020.11.08.20227470v1) if you are using this code in your research or work.


## How to start?



First read the manual [MANUAL](manual/UserInstructions.md)



## Installation:

Install external non Python dependencies depending on your operating system

#### Windows

[Install tesseract]( https://tesseract-ocr.github.io/tessdoc/Home.html).

#### Linux

Install the following dependences (instructions for Ubuntu Linux):

```bash
$ sudo apt install libzmq3-dev, tesseract-ocr, libzbar0
```

#### macOS

To install the required dependencies we recommend to use the packaging manager `brew`. Install it from here if you have't allready [Install brew](https://brew.sh/).

```bash
$ brew install zbar
$ brew install tesseract
```

#### All platforms

1. Install system `Python3` or `miniconda3`.
   
   [Download miniconda](https://docs.conda.io/en/latest/miniconda.html)
   

   If you have other Python installations it is good practice to install everything new into a separate environment. Also such an environment  can be later used to create a snapshot of your installation and shared  with other to build exactly the identical environment.

2. Create a new environment "pyPOCQuantEnv" with:

   ```bash
   conda create -n pyPOCQuantEnv python=3.6
   activate pyPOCQuantEnv
   ```

   *Note: more information about conda environments can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)*

3. Clone this repo:

   ```bash
   git clone https://git.bsse.ethz.ch/cunya/pypocquant.git
   ```

4. Install all requirements.

   ```bash
   $ cd ${pyPOCQuantUI_root_folder}
   $ pip install -r requirements/${platform}
   ```

   where `${platform}` is one of `win32.txt`, `linux.txt`, or `osx.txt`.

#### Notes

- Depending on your Python installation, you may need to use `pip3` instead of `pip`.

- For both running it from source or with the compiled binaries `zbar` and `tesseract` needs to be installed and be on PATH. On Windows `zbar` libs are installed automatically.


## Usage

We provide an example workflow in a Jupyter [notebook](https://github.com/) that illustrate how this library can be used as well as a step by step __QuickStart__ (add link) guide in the documentation.

### Example data

We provide example data as well as an example configuration in this repo under:

   ```bash
   examples/config.conf
   examples/images
   ```

### Minimal example

Create a Python script or Jupyter notebook cell with the following code to run the pipeline on all images for a given `input_folder_path`.

```python
from pypocquant.lib.pipeline import run_pipeline
from pypocquant.lib.settings import default_settings

# Get the default settings
settings = default_settings()

# Change settings manually as needed
settings["sensor_band_names"] = ('igm', 'igg', 'ctl')

# Alternatively, load existing settings file
# from pypocquant.lib.settings import load_settings
# settings = load_settings('full/path/to/settings/file.conf')

# Set final argument
input_folder_path = 'full/path/to/input/folder'
results_folder_path = 'full/path/to/results/folder'
max_workers = 8 

# Run the pipeline
run_pipeline(
    input_folder_path,
    results_folder_path,
    **settings,
    max_workers=max_workers
)
```

### Command line interface (CLI)

Running *pyPOCQuant* from the CLI is best suited when automating the processing  of  large  amounts  of  images  and  folders.   

To create a default configuration from the CLI, use the `-c` flag of pyPOCQuant.py.

```bash 
python pyPOCQuant.py −c /PATH/TO/CONFIG/FILE.conf
```

By far the  easiest  approach  is  to  use  the _pyPOCQuantUI_ (GUI)  for  this  purpose (see below for more information), but it could also be done with other tools, such as Fiji (as described in the manual). 

Once the configuration file is ready, a full study can be started by running  pyPOCQuant  on  a  full  folder  of  images  The  analysis  is performed in parallel, and the number of concurrent tasks can be adjusted by the `-w` (`--workers`) argument.  

```bash
python pyPOCQuant.py −f /PATH/TO/INPUT/FOLDER −o /PATH/TO/RESULTS/FOLDER −s /PATH/TO/CONFIG/FILE −w ${NUMWORKERS}
```

- __`-f`__ `/PATH/TO/INPUT/FOLDER/MANUFACTURER`: path to the folder that contains all images for a given camera and manufacturer.
- __`-o`__ `/PATH/TO/RESULTS/FOLDER`: path where the results (and the quality control images) for a given camera and manufacturer will be saved. The results are saved in a `quantification_data.csv` text file.
- __`-s`__ `/PATH/TO/CONFIG/FILE`: path to the configuration file to be used for this analysis.  Note that a configuration file will be needed per manufacturer and (possibly) camera combination.
- __`-w`__ `NUM_WORKERS`: number of  parallel processes; e.g. `8`.
- __`-v`__: `VERSION` : displays current version of _pyPOCQuant_.
- __`-h`__ `HELP`: displays the CLI arguments and their usage.


To run it with the provided example data type:

```bash
python pyPOCQuant.py −f examples/images −o examples/images/results −s examples/config.conf −w 4
```

### Graphical user interface (GUI)

We also developped a graphical user interface for this tool. You can find it [pyPOCQuantUI](https://git.bsse.ethz.ch/cunya/pypocquantui/). The simplest use is downloading the pre compiled binaries for your operating system. Otherwise you can also run it from source.




## Troubleshooting

Installation requires Python 3.6 , PyQT 5 and fbs 0.9 with PyInstaller 3.4. We have tested the package on (macOS, Linux, Windows 7 and 10) Please [open an issue](https://github.com/) if you have problems that are not resolved by our installation guidelines above.




## Contributors ✨

pyPOCQuant is developed by Andreas P. Cuny and Aaron Ponti. If you want to contribute and further develop the project feel free to do so!

<table>
  <tr>
    <td align="center"><a href="https://github.com/cunyap"><img src="https://avatars2.githubusercontent.com/u/16665588?s=400&u=6489cdd348df91eba79af4c4f54b94dff95342d6&v=4" width="100px;" alt=""/><br /><sub><b>Andreas P. Cuny</b></sub></a><br /><a href="#projectManagement" title="Project Management">📆</a><a href="https://git.bsse.ethz.ch/cunya/pypocquantui/-/graphs/master" title="Code">💻</a> <a href="#design" title="Design">🎨</a> <a href="#ideas" title="Ideas, Planning, & Feedback">🤔</a><a href="#infra" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
    <td align="center"><a href="https://github.com/aarpon"><img src="https://avatars2.githubusercontent.com/u/1226043?s=400&u=1a8877023c6810a70ae0f1985d6cd11f62c6e184&v=4" width="100px;" alt=""/><br /><sub><b>Aaron Ponti</b></sub></a><br /><a href="#projectManagement" title="Project Management">📆</a><a href="https://git.bsse.ethz.ch/cunya/pypocquantui/-/graphs/master" title="Code">💻</a> <a href="#design" title="Design">🎨</a> <a href="#ideas" title="Ideas, Planning, & Feedback">🤔</a><a href="#infra" title="Infrastructure (Hosting, Build-Tools, etc)">🚇</a></td>
  </tr>
</table>




## How to cite 
```bibtex
@article{cuny2020,
  author    = {Andreas P. Cuny and Fabian Rudolf and Aaron Ponti},
  title     = {A tool to automatically quantify Point-Of-Care Tests from images},
  journal   = {MedRxiv},
  year      = {2020},
  doi       = {10.1101/2020.11.08.20227470}
}
```




   
