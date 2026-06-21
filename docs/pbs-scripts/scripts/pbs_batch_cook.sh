#!/bin/bash

################################################################################
# Author: Zhipeng He
# Email: zippo.he@qut.edu.au
# Created Date: May 14, 2025
# Last Modified: June 21, 2026
#
# Sequentially submits multiple experiment scripts as a single PBS job.
# Generates a unique submission file per invocation (timestamped) so runs
# never clobber each other. Each experiment script runs inside the same
# loaded environment (modules + venv), so dependencies load once.
#
# Usage:
#   bash ./pbs_batch_cook.sh
################################################################################

# List of experiments to run
# Add or remove experiments by modifying this array
EXPERIMENTS=(
    "exp_script/Example_Experiment_0.sh"
    "exp_script/Example_Experiment_1.sh"
    "exp_script/Example_Experiment_2.sh"
)

# Create a unique timestamp once
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_NAME="task_${TIMESTAMP}"
PBS_SCRIPT="submit_job_${TIMESTAMP}.pbs"

# Create PBS script
# Note: in the heredoc below, ${...} expands at submission time (when this
# script runs) and \${...} is escaped so it expands at job runtime on the
# compute node. See "Mind your dollar signs" in the page.
cat > ${PBS_SCRIPT} << EOF
#!/bin/bash
#PBS -N ${JOB_NAME}
#PBS -l select=1:ncpus=8:ngpus=1:mem=64GB:gpu_id=H100
#PBS -M $USER@qut.edu.au
#PBS -l walltime=48:00:00
#PBS -q gpu_batch_exec
#PBS -j oe
#PBS -m abe
#PBS -o ${JOB_NAME}_output.log

# Set paths
WORK_DIR=\${PBS_O_WORKDIR}
DATASET_DIR=\${WORK_DIR}/dataset

cd \${PBS_O_WORKDIR}

# Load required modules — check current defaults with \`module avail\`
module load GCCcore/13.3.0
module load Python/3.12.3
module load libffi/3.4.5
module load CUDA/11.8.0

# Create and activate virtual environment
python -m venv env
source env/bin/activate
python -m pip install -r requirements.txt

# Run experiments
cd \${WORK_DIR}
EOF

# Preflight — fail fast if any experiment script is missing, so the PBS
# script isn't generated (and never qsub'd) with broken paths.
for exp in "${EXPERIMENTS[@]}"; do
    if [[ ! -f "scripts/${exp}" ]]; then
        echo "Missing experiment script: scripts/${exp}" >&2
        exit 1
    fi
done

# Add each experiment to the PBS script with a clear log banner
for exp in "${EXPERIMENTS[@]}"; do
    echo "echo '=============================================='" >> "${PBS_SCRIPT}"
    echo "echo 'Running experiment: ${exp}'" >> "${PBS_SCRIPT}"
    echo "echo '=============================================='" >> "${PBS_SCRIPT}"

    echo "bash \${WORK_DIR}/scripts/${exp}" >> "${PBS_SCRIPT}"

    echo "echo ''" >> "${PBS_SCRIPT}"
    echo "echo '=============================================='" >> "${PBS_SCRIPT}"
    echo "echo ''" >> "${PBS_SCRIPT}"
done

# Make the PBS script executable, submit, and capture the real PBS job id.
# `qsub` prints e.g. "12345.aqua" on success; on failure (bad directive,
# resource over-cap, queue closed) we want to surface that, not pretend it
# worked.
chmod +x "${PBS_SCRIPT}"
job_id=$(qsub "${PBS_SCRIPT}") || {
    echo "qsub submission failed for ${PBS_SCRIPT}" >&2
    exit 1
}

echo "Job submitted: ${job_id} (name: ${JOB_NAME})"
echo "You can monitor the job using: qstat -u \$USER"
echo "Output will be saved in: ${JOB_NAME}_output.log"
