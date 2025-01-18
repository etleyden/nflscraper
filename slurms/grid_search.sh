#!/bin/bash

## Begin SLURM Batch Commands
##SBATCH --cpus-per-task=31
##SBATCH --mem=59G
##SBATCH --time=0-01:00
##SBATCH --mail-user leydene@vcu.edu
##SBATCH --mail-type=ALL
##SBATCH --output=svm_grid_search.log

module load anaconda3
source .nflscraper_venv/bin/activate
python src/grid_search_svm.py data/nfl2017_2023.csv

## ** End Of SLURM Batch Commands **
##
## ===================================
## Important Hickory GPU Request Note
## ===================================
## Most importantly, the option `--gres=gpu:<type>:<count>` must be used
## to request GPUs (`-G` or `--gpus` will not work). Values for `<type>`
## are `40g` and `80g`, referring to the 40 GB and 80 GB GPUs. The current
## limits (`<count>`) for the 40 GB GPUs are 1 in the `long` QOS and 2 in
## `short`. The current limit for the 80 GB GPUs is 1 in `short` (they are
## unavailable in `long`).
##
##
## More Info: https://wiki.vcu.edu/x/P6POBQ
##
## END