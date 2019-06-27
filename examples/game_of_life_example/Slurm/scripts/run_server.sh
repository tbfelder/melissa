#!/bin/bash

#SBATCH -N ${NODES_SERVER}
#SBATCH --ntasks-per-node=${PROC_PER_NODE}
#SBATCH --mem=0
#SBATCH --time=${WALLTIME_SERVER}
#SBATCH -o melissa.%j.log
#SBATCH -e melissa.%j.err
#SBATCH --job-name=Melissa
#SBATCH --partition=fast

module load openmpi

date +\"%d/%m/%y %T\"
source /home/users/pogodzinski/melissa/install/bin/melissa_set_env.sh
# run Melissa
echo  \"### Launch Melissa\"
mkdir stats${SLURM_JOB_ID}.resu
cd stats${SLURM_JOB_ID}.resu
${SERVER_CMD}
wait %1
date +\"%d/%m/%y %T\"
cd ..
