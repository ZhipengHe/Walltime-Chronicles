# Batch-Cooking PBS Scripts with a Bash Pan

!!! warning "This is a work in progress"
    Right now, this page is a work in progress. Only an example bash file is provided. I will update this page with more details soon.

## :material-bash: Example Bash Pan

```bash
#!/bin/bash

# Author: Zhipeng He
# Email: zhipeng.he@hdr.qut.edu.au

# List of experiments to run
# Add or remove experiments by modifying this array
EXPERIMENTS=(
    "exp_script/Example_Experiment_0.sh"
    "exp_script/Example_Experiment_1.sh"
    "exp_script/Example_Experiment_2.sh"
)

# Create a unique timestamp once
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_NAME="tslib_${TIMESTAMP}"
PBS_SCRIPT="submit_job_${TIMESTAMP}.pbs"

# Create PBS script
cat > ${PBS_SCRIPT} << EOF
#!/bin/bash
#PBS -N ${JOB_NAME}
#PBS -l select=1:ncpus=8:ngpus=1:mem=64GB:gpu_id=H100
#PBS -M $USER@qut.edu.au
#PBS -l walltime=48:00:00
#PBS -q gpuq
#PBS -j oe
#PBS -m abe
#PBS -o ${JOB_NAME}_output.log

# Set paths
WORK_DIR=\${PBS_O_WORKDIR}
DATASET_DIR=\${WORK_DIR}/dataset

cd \${PBS_O_WORKDIR}

module load GCCcore/13.3.0
module load Python/3.12.3
module load libffi/3.4.5
module load CUDA/11.8.0

python -m venv env
source env/bin/activate
python -m pip install -r requirements.txt

# Run experiments
cd \${WORK_DIR}
EOF

# Add each experiment to the PBS script
for exp in "${EXPERIMENTS[@]}"; do
    # Add a section header for each experiment
    echo "echo '=============================================='" >> ${PBS_SCRIPT}
    echo "echo 'Running experiment: ${exp}'" >> ${PBS_SCRIPT}
    echo "echo '=============================================='" >> ${PBS_SCRIPT}
    
    # Add the experiment command (run directly)
    echo "bash \${WORK_DIR}/scripts/${exp}" >> ${PBS_SCRIPT}
    
    # Add a separator between experiments
    echo "echo ''" >> ${PBS_SCRIPT}
    echo "echo '=============================================='" >> ${PBS_SCRIPT}
    echo "echo ''" >> ${PBS_SCRIPT}
done

# Make the PBS script executable
chmod +x ${PBS_SCRIPT}

# Submit the job
qsub ${PBS_SCRIPT}

echo "Job submitted with name: ${JOB_NAME}"
echo "You can monitor the job using: qstat -u \$USER"
echo "Output will be saved in: ${JOB_NAME}_output.log" 
```
