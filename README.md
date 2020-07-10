# pyPOCQuant

Library for computer vision approach to automatically read out the result from POC test images and quantify the band intensities.

written by `Andreas P. Cuny` and `Aaron Ponti`



## How to start?



First read the manual [MANUAL](manual/UserInstructions.md)



## Installation:

1. Install system `Python3` or `miniconda3`.
   
   [Download miniconda](https://docs.conda.io/en/latest/miniconda.html)
   

   If you have other Python installations it is good practice to install everything new into a separate environment. Also such an environment  can be later used to create a snapshot of your installation and shared  with other to build exactly the identical environment.

2. Create a new environment "pyPOCQuantEnv" with:

   ```bash
   conda create -n pyPOCQuantEnv python=3.6
   activate pyPOCQuantEnv
   ```

   *Note: more information about conda environments can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html)*

2. Clone this repo:

   ```bash
   git clone https://git.bsse.ethz.ch/cunya/pypocquant.git
   ```

3.  Install the library

   ```python
   pip install -e .
   ```

4.  Run the scripts as described in the manual.