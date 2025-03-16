This repository contains the contents to run the case study described in the manuscript "A computational framework for agent-based assessment of multiple environmental exposures".
Users on Linux operating systems should be able to execute the model script.


## How to install

A few steps are required to run the case study.

 1. You will need a working Python environment, we recommend to install Miniforge. Follow their instructions given at e.g.:

    [https://conda-forge.org/download/](https://conda-forge.org/download/)

 2. Open a terminal and browse to a location where you want to store the course contents.

 3. Clone this repository, or download and uncompress the zip file. Afterwards change to the `paper_agent_based_exposure_assessment` folder.

 4. Create the required Python environment:

    `conda env create -f environment/environment.yaml`

The environment file will create a environment named *casestudyutrecht* using Python 3.10. In case you prefer a different name you need to edit the environment file.

The user guide and short reference on Conda can be found [here](https://docs.conda.io/projects/conda/en/latest/user-guide/cheatsheet.html).

## Download the input data
Required additional input data can be downloaded from [Zenodo](https://zenodo.org/records/13913079).
Extract the downloaded zip file and move its contents to the `paper_agent_based_exposure_assessment` folder.

## How to run

Activate the environment in the command prompt:

`conda activate casestudyutrecht`

Execute the script `run.sh`. 
It will first run 20 realisations each for the homemaker (weekday and weekend) and commuter profiles.
Afterwards, exposure estimates are calculated for NO2, PM2.5 and noise using 5 workdays and 2 weekend days.
The CSV output files will be written to the current working directory.

The current setup simulates 1000 agents.
If you want to use more agents you can set the `query_home_where` in the `config.py` file to a larger value.

## Questions or issues

Please ask questions or file issues in the [development repository](https://github.com/computationalgeography/agent_based_exposure_assessment/issues) of this project.
