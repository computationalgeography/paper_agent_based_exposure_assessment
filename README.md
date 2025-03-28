This repository contains the contents to run the case study described in the manuscript "A computational framework for agent-based assessment of multiple environmental exposures".
Users on Linux operating systems should be able to execute the model script.

## How to install

A few steps are required to run the case study.

 1. You will need a working Python environment, we recommend to install Miniforge in case you have no Conda package manager installed yet.
    Follow their instructions given at:

    [https://conda-forge.org/download/](https://conda-forge.org/download/)

    before you continue.

 2. Open a terminal and browse to a location where you want to store the course contents.

 3. Clone this repository

    `git clone https://github.com/computationalgeography/paper_agent_based_exposure_assessment.git`

    or download and uncompress the [zip](https://github.com/computationalgeography/paper_agent_based_exposure_assessment/archive/refs/heads/main.zip)
    file of the repository.

 4. Navigate to the `paper_agent_based_exposure_assessment` folder:

    `cd paper_agent_based_exposure_assessment`

    and create the required Python environment:

    `conda env create -f environment/environment.yaml`

The environment file will create a environment named *casestudyutrecht* using Python 3.10. In case you prefer a different name you need to edit the `environment/environment.yaml` file.

The user guide and short reference on Conda can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/cheatsheet.html).

## Download the input data
Required additional input data can be downloaded from [Zenodo](https://zenodo.org/records/13913079), e.g. with

`wget https://zenodo.org/records/13913079/files/input_data.zip`

Extract the downloaded zip file and its contents into the `paper_agent_based_exposure_assessment` folder.

## How to run

Activate the environment in the command prompt:

`conda activate casestudyutrecht`

Execute the script `run.sh`.
It will first run 10 realisations each for the homemaker (weekday and weekend) and commuter profiles.
Note that running the simulations can take a while, the progress will be printed.
After completion, overall exposure estimates are calculated for NO<sub>2</sub>, PM<sub>2.5</sub> and noise using 5 workdays and 2 weekend days.
Six CSV output files with mean and standard deviation values for each agent will be written to the current working directory.

The current setup simulates 1000 agents.
If you want to use more agents you can set the `query_home_where` in the `config.py` file to a larger value.
To use a different number of realisations change the `REALISATIONS` entry in the script `run.sh`.

## Questions or issues

The most recent version of the modelling framework can be found in the [development repository](https://github.com/computationalgeography/agent_based_exposure_assessment/issues) of this project.
Please file issues there or contact the corresponding author [Oliver Schmitz](mailto:o.schmitz@uu.nl) if you have questions or need support in applying the framework.
