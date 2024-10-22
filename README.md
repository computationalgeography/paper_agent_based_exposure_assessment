This repository contains the contents to run the case study described in the manuscript "A computational framework for agent-based assessment of multiple environmental exposures".
Users on Linux operating systems should be able to execute the model script.


## Download the input data
Required additional input data can be downloaded from [Zenodo](https://zenodo.org/records/13913079).


## How to install

A few steps are required to run the case study.

 1. You will need a working Python environment, we recommend to install Miniforge. Follow their instructions given ati e.g.:

    [https://conda-forge.org/download/](https://conda-forge.org/download/)

 2. Open a terminal and browse to a location where you want to store the course contents.

 3. Clone this repository, or download and uncompress the zip file. Afterwards change to the `paper_agent_based_exposure_assessment` folder.

 4. Create the required Python environment:

    `conda env create -f environment/environment.yaml`

The environment file will create a environment named *casestudyutrecht* using Python 3.10. In case you prefer a different name you need to edit the environment file.

The user guide and short reference on Conda can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/cheatsheet.html).


## How to run

Execute the script `run.sh`. It will run 25 realisations for homemaker and commuter.
