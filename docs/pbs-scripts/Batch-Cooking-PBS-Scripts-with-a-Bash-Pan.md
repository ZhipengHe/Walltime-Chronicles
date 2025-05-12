# Batch-Cooking PBS Scripts with a Bash Pan

## :material-pot-mix: What's Cooking?

So, you have multiple experiments, each with their own little quirks, and you want to run them one after another on the HPC without babysitting each one? Welcome to **batch-cooking PBS jobs** — where bash scripts are your pan, and experiments are the ingredients.

This script is basically a recipe that:

* Grabs a timestamp so your job names never clash (like naming your children but with less emotional weight).
* Prepares a fresh PBS submission script (like meal-prepping but for compute time).
* Sets up your environment (modules + virtualenv, the usual kitchen hygiene).
* Dumps in your experiments, one by one, and gives them a nice little echo wrapper so you can read the logs without crying.
* Submits it all in one go with `qsub`.

**Result:** *one tidy `.pbs` file, logs clearly marked, and no waking up at 2 a.m. wondering if you ran `Example_Experiment_1.sh` twice.*

---

## :material-notebook-edit-outline: How To Customise

Want to make it your own? Let's break down each part of the recipe:

### 1. Selecting Your Ingredients (Experiments)

Add or remove experiment scripts in the `EXPERIMENTS=(...)` array. This is your tasting menu — change it freely.

```bash
#!/bin/bash

# List of experiments to run
# Add or remove experiments by modifying this array
EXPERIMENTS=(
    "exp_script/Example_Experiment_0.sh"
    "exp_script/Example_Experiment_1.sh"
    "exp_script/Example_Experiment_2.sh"
    # "exp_script/My_New_Experiment.sh"  # Uncomment to add new experiments
    # "path/to/another/experiment.sh"
)
```

### 2. Setting Up Unique Job Names

Creating a timestamp ensures your job names never clash (like naming your children but with less emotional weight).

```bash
# Create a unique timestamp once
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
JOB_NAME="task_${TIMESTAMP}"
PBS_SCRIPT="submit_job_${TIMESTAMP}.pbs"
```

You can customize the format:

- Change `task_` to something meaningful like `training_` or `analysis_`
- Modify the timestamp format by changing `%Y%m%d_%H%M%S`

### 3. Crafting Your PBS Header

Adjust the PBS directives (walltime, resources, queue) to match your appetite and quota.

```bash
# Create PBS script
cat > ${PBS_SCRIPT} << EOF
#!/bin/bash
#PBS -N ${JOB_NAME}
#PBS -l select=1:ncpus=8:ngpus=1:mem=64GB:gpu_id=H100  # Adjust resources here
#PBS -M $USER@qut.edu.au  # Your email for notifications
#PBS -l walltime=48:00:00  # Maximum runtime - format is HH:MM:SS
#PBS -q gpuq  # Queue to submit to - adjust based on your HPC
#PBS -j oe  # Join output and error files
#PBS -m abe  # Mail on abort, begin, and end
#PBS -o ${JOB_NAME}_output.log  # Output log filename
#PBS -e ${JOB_NAME}_error.log  # Error log filename
EOF
```

Common modifications:

- Change `select=1:ncpus=8:ngpus=1:mem=64GB:gpu_id=H100` for different resource needs
- Adjust `walltime=48:00:00` for jobs that need more or less time
- Change `gpuq` to another queue if needed (e.g., `cpuq`, `bigmem`, etc.)

### 4. Setting Up Your Environment

Configure the paths and modules for your kitchen:

```bash
# Add environment setup to the PBS script
cat >> ${PBS_SCRIPT} << EOF
# Set paths
WORK_DIR=\${PBS_O_WORKDIR}
DATASET_DIR=\${WORK_DIR}/dataset  # Adjust dataset path if needed

cd \${PBS_O_WORKDIR}

# Load required modules - customize these based on your needs
module load GCCcore/13.3.0
module load Python/3.12.3
module load libffi/3.4.5
module load CUDA/11.8.0  # Change version based on your GPU requirements

# Create and activate virtual environment
python -m venv env
source env/bin/activate
python -m pip install -r requirements.txt  # Make sure this file exists!

# Run experiments
cd \${WORK_DIR}
EOF
```

You can modify this to:

- Change the path prefix (`\${WORK_DIR}/scripts/`) if your scripts are stored elsewhere
- Add experiment-specific parameters
- Add timing information by adding commands like:
  ```bash
  echo "echo 'Start time: $(date)'" >> ${PBS_SCRIPT}
  # ... experiment command ...
  echo "echo 'End time: $(date)'" >> ${PBS_SCRIPT}
  ```

### 5. Adding Experiment Loops

This part adds each experiment to the PBS script with nice formatting:

```bash
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
```

### 6. Finalizing and Submitting

Make the script executable and submit it:

```bash
# Make the PBS script executable
chmod +x ${PBS_SCRIPT}

# Submit the job
qsub ${PBS_SCRIPT}

# Provide helpful feedback to the user
echo "Job submitted with name: ${JOB_NAME}"
echo "You can monitor the job using: qstat -u \$USER"
echo "Output will be saved in: ${JOB_NAME}_output.log"
```

You can add additional commands here to:
- Copy the PBS script to an archive location
- Add the job ID to a tracking file
- Set up monitoring or notifications

---

## :material-chef-hat: The Complete Recipe

Here's the full script that you can copy, paste, and modify to suit your needs:

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
JOB_NAME="task_${TIMESTAMP}"
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
#PBS -e ${JOB_NAME}_error.log
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

---

## :material-lightbulb-on: Tips from the Bash Kitchen

* Use descriptive experiment script names — “exp1.sh” and “exp2.sh” are fine, but "exp_doomed_to_fail.sh" will save you time.
* Want to run things in parallel instead of sequentially? That's another recipe... and it involves GNU `parallel`, job arrays, and possibly a small ritual.
* Always `echo` your steps. Your future self, trying to debug at midnight, will thank you.
* Mind your dollar signs in heredocs! Escape PBS variables like `\${PBS_O_WORKDIR}` but leave `${TIMESTAMP}` naked. The difference? One's for the future, one's for right now — like prepping tomorrow's lunch vs. tonight's dinner.

## :material-tools: Troubleshooting Tips

Even the best chefs have kitchen mishaps. Here's how to handle common issues:

* **Path Problems**: If your experiments aren't running, check that the paths in the `EXPERIMENTS` array match your actual directory structure.

* **Script Permissions**: Ensure your individual experiment scripts have execute permissions:
  ```bash
  chmod +x scripts/exp_script/Example_Experiment_*.sh
  ```

* **Dependency Hell**: If your experiments have different Python package requirements, consider:
    * Using separate virtual environments for each experiment
    * Creating a unified `requirements.txt` with all dependencies
    * Adding `pip install -r specific_requirements.txt` in each experiment script

* **Resource Conflicts**: If your experiments need different amounts of resources, consider making separate submission scripts rather than running them sequentially.

## :material-application-variable: Environment Variables

Your experiment scripts can access these PBS environment variables:

* `$PBS_O_WORKDIR`: The directory from which the job was submitted
* `$PBS_JOBID`: The job's unique identifier
* `$PBS_JOBNAME`: The name of the job (in this case, `task_TIMESTAMP`)
* `$PBS_NODEFILE`: A file containing the nodes assigned to the job
* `$PBS_QUEUE`: The queue the job was submitted to


## :material-fire: Advanced Techniques

Ready to level up your cooking skills?

### Handling Failures Gracefully

To prevent later experiments from failing if an earlier one crashes:

```bash
# Add to each experiment loop iteration
echo "if bash \${WORK_DIR}/scripts/${exp}; then" >> ${PBS_SCRIPT}
echo "  echo 'Experiment ${exp} completed successfully'" >> ${PBS_SCRIPT}
echo "else" >> ${PBS_SCRIPT}
echo "  echo 'WARNING: Experiment ${exp} failed with exit code $?'" >> ${PBS_SCRIPT}
echo "  # Continue anyway" >> ${PBS_SCRIPT}
echo "fi" >> ${PBS_SCRIPT}
```

### Experiment Status Tracking

Create a summary of completed experiments at the end:

```bash
# Add before the experiments loop
echo "declare -A experiment_status" >> ${PBS_SCRIPT}

# Add within the loop (replacing the direct bash command)
echo "if bash \${WORK_DIR}/scripts/${exp}; then" >> ${PBS_SCRIPT}
echo "  experiment_status[\"${exp}\"]=\"SUCCESS\"" >> ${PBS_SCRIPT}
echo "else" >> ${PBS_SCRIPT}
echo "  experiment_status[\"${exp}\"]=\"FAILED\"" >> ${PBS_SCRIPT}
echo "fi" >> ${PBS_SCRIPT}

# Add after the experiments loop
echo "echo '============== EXPERIMENT SUMMARY ==============='" >> ${PBS_SCRIPT}
echo "for exp in \"${EXPERIMENTS[@]}\"; do" >> ${PBS_SCRIPT}
echo "  echo \"\$exp: \${experiment_status[\"\$exp\"]}\"" >> ${PBS_SCRIPT}
echo "done" >> ${PBS_SCRIPT}
echo "echo '================================================'" >> ${PBS_SCRIPT}
```

### Email Notifications with Results

Add result summaries to your email notifications:

```bash
# Add at the end of the script (before submission)
echo "mail -s \"Job ${JOB_NAME} Complete\" $USER@qut.edu.au < ${JOB_NAME}_output.log" >> ${PBS_SCRIPT}
```

---

## :material-food-variant: Happy Cooking!

With this script, you can set up a batch of experiments, hit submit, and let the HPC do its thing while you focus on more interesting work—or maybe even go outside for a change.

> **Remember:** A watched pot never boils, and a watched HPC job doesn't finish any faster.

## :material-egg-easter: Coming Soon...

* A version that uses PBS job arrays (aka "batch-cooking with timers").
* Error catching and handling — building on our "Handling Failures Gracefully" section.
* Log file management like a pro (or at least, like someone who doesn't grep 10GB files manually).
* Experiment templating — for when you need to run the same experiment with different flavors (parameters).
* Resource optimisation — making sure you're not using a sledgehammer to crack a nut.
