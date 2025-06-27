# PBS Brew Inspector: Tasting Notes from Your Job History

> *Or: A user-friendly and informative alternative to `qjob -x`.*

!!! question "Why not use built-in `qjob -x` command in Aqua?"
    QUT Aqua HPC provides a command `qjob -x` that can be used to extract the details of the finished jobs from the PBS system (Check [this page](https://docs.eres.qut.edu.au/hpc-basic-command-line#useful-commands-on-the-hpc) for more details). However, the format of the output is not very user-friendly and not very informative.

<!-- markdownlint-disable-next-line link-fragments -->
!!! info "See full recipe of `pbs_brew_inspector.sh` in [Full Recipe](#full-recipe-of-pbs_brew_inspectorsh)."

## :material-microscope: What's in Your Computational Brew?

You've been submitting jobs for weeks, crossing your fingers and hoping for the best — but do you actually know what's happening under the hood? Are you wasting resources like a novice chef burning through expensive ingredients, or are you efficiently crafting computational masterpieces?

`pbs_brew_inspector.sh` is your personal sommelier for PBS jobs — swirling, sniffing, and analysing the complex flavours of your computational brews. This script extracts the subtle notes of resource usage and efficiency from your completed jobs, helping you perfect your next batch instead of stumbling around in the dark.

Think of it as your lab notebook for computational experiments, but one that actually tells you the truth about how your recipes performed, what ingredients they consumed, and whether you're a resource efficiency genius or... well, let's find out.

## :material-flask-outline: The Tasting Menu

When you run `pbs_brew_inspector.sh`, you're not just getting a boring list of numbers — you're getting a full sensory analysis of your computational performance. Here's what's on the tasting menu:

- **Walltime Profile:** How long your jobs ran versus how long you requested?
- **CPU Intensity:** Single-note or complex multi-core symphonies?
- **Memory Usage:** Light and crisp or rich and heavy?
- **GPU Utilisation:** The spicy kick of accelerated computing.
- **Efficiency Metrics:** The perfect balance of resource requests.

## :material-chef-hat: Brewing Instructions

Getting your tasting notes is simple. Just run the script with the appropriate flavour filters:

```bash
bash ./pbs_brew_inspector.sh -g     # Sample only GPU jobs
bash ./pbs_brew_inspector.sh -c     # Focus on CPU-only jobs
bash ./pbs_brew_inspector.sh -b     # Examine batch processing jobs
bash ./pbs_brew_inspector.sh -gi    # Look at interactive GPU sessions
```

You'll be presented with a beautifully formatted table showing each job's characteristics:

```text
> bash ./pbs_brew_inspector.sh -gb # Example output for GPU batch jobs

Resource Usage Report -- $USER @ Wed May 14 02:47:54 PM AEST 2025
================================================================================================================================================================
JobID        Wall_Time   Wall_Limit  CPU_Time    CPU%        Mem(GB)    Mem_Limit  Mem_Use%  GPU_Util% GPU_Mem%   GPUs     CPUs       Nodes    Queue
================================================================================================================================================================
3890***.aqua 01:07:53    48:00:00    02:40:13    295%        2.69       64GB       4.2%      72%       4%         1        8          1        gpu_batch_exec
3890***.aqua 02:04:52    48:00:00    07:35:42    504%        5.48       64GB       8.6%      47%       12%        1        8          1        gpu_batch_exec
3905***.aqua 01:35:54    48:00:00    03:57:29    364%        3.32       64GB       5.2%      58%       8%         1        8          1        gpu_batch_exec
3921***.aqua 20:04:13    24:00:00    21:36:23    160%        11.68      64GB       18.2%     39.7%     28%        1        8          1        gpu_batch_exec
================================================================================================================================================================
AVERAGE      06:13:13    42:00:00    -           330.8%      5.79       -          9.1%      54.2%     13.0%      -        -          -        -

Job Statistics:
--------------
Total Jobs: 4
Jobs with GPU: 4
Jobs CPU-only: 0

Average Resource Efficiency:
  CPU Usage: 330.8%
  Memory Usage: 9.1%
  Walltime Usage: 23.4%

GPU Jobs Metrics (average of 4 GPU jobs):
  GPU Utilisation: 54.2%
  GPU Memory Usage: 13.0%
```

!!! warning "Widen your terminal to see it all!"
    The output table spans over 160 characters — that's pretty wide! To avoid missing any columns, give your terminal a good stretch. Go on, maximise that window! You will get the full picture, literally.

## :material-chart-line: Reading Your Tasting Notes

Now comes the fun part — decoding what these numbers are actually telling you about your computational habits. Think of this as learning to read the secret language of resource efficiency:

1. **Walltime Efficiency**: In the example above, you'll notice jobs using only about 23.4% of the requested walltime. This suggests your jobs could use shorter time requests for better queue priority.
2. **Memory Utilisation**: With 9.1% average memory usage, you're requesting far more memory than needed. Consider reducing memory requests for faster queue times.
3. **GPU Utilisation Patterns**: The 54.2% average GPU utilisation indicates reasonable but not optimal GPU use. There might be opportunities to optimise your code to better utilise this expensive resource.
4. **CPU Efficiency**: A CPU usage of 330.8% on 8-CPU jobs reveals you're effectively using about 4 cores out of 8 - potentially an area for optimisation.

!!! warning "Job History Limitation"
    Due to Aqua Server's configuration, the script can only extract the details of jobs from the last 96 hours (4 days). Jobs older than this period will not be available in the PBS history.

    To verify the current job history retention period:

    ```bash
    [user@aquarius02 ~]$ qmgr -c "print server job_history_duration"
    #
    # Set server attributes.
    #
    set server job_history_duration = 96:00:00
    ```

## :material-lightbulb-on: Pairing Suggestions

`pbs_brew_inspector.sh` pairs beautifully with:

- [**Guess, Request, Regret: The Art of Walltime**](../scheduler/The-Art-of-Walltime.md): Use these insights to master your walltime estimates
- More pages coming soon...

## :material-tools: Customisation Notes

Like any good recipe, you can customise this tool to your taste:

- Modify the output format for specific metrics you care about
- Add custom calculations for project-specific efficiency metrics
- Filter for specific job name patterns or time periods
- Export the data for visualisation in your favourite plotting tool

## :material-flag-triangle: The Brew Inspector's Wisdom

The true artisan understands their ingredients. By regularly inspecting your computational brews, you'll develop an intuition for:

- How long similar jobs will take (crucial for walltime estimates)
- Which resources are your bottlenecks
- Where you're wasting computational resources
- How to optimise your code for better efficiency

> **Remember:** Analysing your past jobs isn't just about efficiency — it's about evolving from someone who throws computational ingredients at the wall to see what sticks, into a master chef who knows exactly how much of each resource will create the perfect recipe.

Stop guessing. Start brewing with confidence. Your future self (and your queue priority) will thank you.

## :material-script: Full Recipe of `pbs_brew_inspector.sh`

!!! tip "Download the script directly on the server"
    Download the script directly on the server by running the following commands:
    ```bash
    # by wget
    wget https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/pbs-scripts/scripts/pbs_brew_inspector.sh
    # by curl
    curl -O https://raw.githubusercontent.com/ZhipengHe/Walltime-Chronicles/main/docs/pbs-scripts/scripts/pbs_brew_inspector.sh
    ```

    You can choose to move the script to a more convenient location, e.g. `~/bin/`. Then you can run it directly by typing `pbs_brew_inspector.sh` in the terminal.

    ```bash
    # make the script executable
    chmod +x pbs_brew_inspector.sh
    # move the script to a more convenient location
    mv pbs_brew_inspector.sh ~/bin/
    # run the script
    pbs_brew_inspector.sh
    ```

Copy the below script and save it as `pbs_brew_inspector.sh` to your server to use it. Or you can download it from [this link](../pbs-scripts/scripts/pbs_brew_inspector.sh).

```bash title="pbs_brew_inspector.sh"
#!/bin/bash

################################################################################
# Author: Zhipeng He
# Email: zhipeng.he@hdr.qut.edu.au
# Last Modified: May 14, 2025
# Created Date: May 14, 2025
#
# This script is used to extract the details of the jobs from the PBS system.
# It is used to understand the resource usage of the historical jobs.
#
# Usage:
#   bash ./pbs_brew_inspector.sh [-U username] [-c|-g|-b|-i|-l|-p]
#
# Options:
#   -U username : Specify username (default: current user)
#   -c : Show all CPU jobs
#   -g : Show all GPU jobs
#   -b : Show all batch jobs
#   -i : Show all interactive jobs
#   -l : Show large memory jobs
#   -p : Show persistent jobs
#
# Examples:
#   bash ./pbs_brew_inspector.sh -c      # Show all CPU jobs
#   bash ./pbs_brew_inspector.sh -ci     # Show CPU interactive jobs
#   bash ./pbs_brew_inspector.sh -gb     # Show GPU batch jobs
#   bash ./pbs_brew_inspector.sh -cl     # Show CPU large memory jobs
################################################################################

# Default to current user
USERNAME=$USER
SHOW_CPU_BATCH=true
SHOW_CPU_INTER=true
SHOW_GPU_BATCH=true
SHOW_GPU_INTER=true
SHOW_CPU_BATCH_LARGE=true
SHOW_CPU_INTER_PERS=true

# Parse command line arguments
while getopts "U:cbgilp" opt; do
    case $opt in
        U) USERNAME="$OPTARG" ;;
        c) # CPU jobs
           SHOW_CPU_BATCH=true
           SHOW_CPU_INTER=true
           SHOW_CPU_BATCH_LARGE=true
           SHOW_CPU_INTER_PERS=true
           SHOW_GPU_BATCH=false
           SHOW_GPU_INTER=false
           ;;
        g) # GPU jobs
           SHOW_CPU_BATCH=false
           SHOW_CPU_INTER=false
           SHOW_CPU_BATCH_LARGE=false
           SHOW_CPU_INTER_PERS=false
           SHOW_GPU_BATCH=true
           SHOW_GPU_INTER=true
           ;;
        b) # Batch jobs
           SHOW_CPU_BATCH=true
           SHOW_GPU_BATCH=true
           SHOW_CPU_INTER=false
           SHOW_GPU_INTER=false
           SHOW_CPU_INTER_PERS=false
           ;;
        i) # Interactive jobs
           SHOW_CPU_INTER=true
           SHOW_GPU_INTER=true
           SHOW_CPU_BATCH=false
           SHOW_GPU_BATCH=false
           SHOW_CPU_BATCH_LARGE=false
           ;;
        l) # Large memory jobs
           SHOW_CPU_BATCH_LARGE=true
           SHOW_CPU_BATCH=false
           SHOW_CPU_INTER=false
           SHOW_GPU_BATCH=false
           SHOW_GPU_INTER=false
           SHOW_CPU_INTER_PERS=false
           ;;
        p) # Persistent jobs
           SHOW_CPU_INTER_PERS=true
           SHOW_CPU_BATCH=false
           SHOW_CPU_INTER=false
           SHOW_GPU_BATCH=false
           SHOW_GPU_INTER=false
           SHOW_CPU_BATCH_LARGE=false
           ;;
        \?)
           echo "Invalid option -$OPTARG" >&2
           echo "Usage: $0 [-U username] [-c|-g|-b|-i|-l|-p]"
           echo "  -U username : Specify username (default: current user)"
           echo "  -c : Show all CPU jobs"
           echo "  -g : Show all GPU jobs"
           echo "  -b : Show all batch jobs"
           echo "  -i : Show all interactive jobs"
           echo "  -l : Show large memory jobs"
           echo "  -p : Show persistent jobs"
           echo ""
           echo "Examples:"
           echo "  $0 -c      # Show all CPU jobs"
           echo "  $0 -ci     # Show CPU interactive jobs"
           echo "  $0 -gb     # Show GPU batch jobs"
           echo "  $0 -cl     # Show CPU large memory jobs"
           exit 1
           ;;
    esac
done

# Function to format time in HH:MM:SS format with leading zeros
format_time() {
    local seconds=$1
    local hours=$((seconds/3600))
    local minutes=$((seconds%3600/60))
    local secs=$((seconds%60))
    printf "%02d:%02d:%02d" $hours $minutes $secs
}

# Function to convert HH:MM:SS time string to seconds
time_to_seconds() {
    local time_str=$1
    if [[ -z "$time_str" ]]; then
        echo 0
        return
    fi
    # Use base 10 arithmetic to avoid octal interpretation
    local hours=$((10#$(echo $time_str | cut -d: -f1)))
    local minutes=$((10#$(echo $time_str | cut -d: -f2)))
    local seconds=$((10#$(echo $time_str | cut -d: -f3)))
    echo $((hours*3600 + minutes*60 + seconds))
}

# Print table name and header
printf "%s\n"
printf "%s\n" "Resource Usage Report -- $USERNAME @ $(date)"
printf "%s\n" "$(printf '=%.0s' {1..160})"

# Header for the output table with revised columns
printf "%-13s %-11s %-11s %-11s %-9s %-10s %-10s %-9s %-9s %-10s %-8s %-10s %-8s %-8s\n" \
"JobID" "Wall_Time" "Wall_Limit" "CPU_Time" "CPU%" "Memory" "Mem_Limit" "Mem_Use%" \
"GPU_Util%" "GPU_Mem%" "GPUs" "CPUs" "Nodes" "Queue"
printf "%s\n" "$(printf '=%.0s' {1..160})"

# Initialize variables for calculating averages
total_jobs=0
total_gpu_jobs=0
sum_cpu_percent=0
sum_mem_use_gb=0
sum_mem_use_pct=0
sum_mem_limit_gb=0
sum_gpu_util=0
sum_gpu_mem_pct=0
sum_wall_seconds=0
sum_wall_limit_seconds=0
sum_wall_efficiency=0

# Get all held jobs for the user
jobs=$(qstat -H -u $USERNAME | awk '{print $1}' | grep '^[0-9]')
for job in $jobs; do
    output=$(qstat -fx "$job")
    total_jobs=$((total_jobs + 1))

    # Basic job info
    queue=$(echo "$output" | awk '/queue/ {print $3}')

    # Skip if queue doesn't match filter
    if [[ "$queue" == "cpu_batch_exec" && "$SHOW_CPU_BATCH" != "true" ]] || \
       [[ "$queue" == "gpu_batch_exec" && "$SHOW_GPU_BATCH" != "true" ]] || \
       [[ "$queue" == "cpu_interactive_exec" && "$SHOW_CPU_INTER" != "true" ]] || \
       [[ "$queue" == "gpu_interactive_exec" && "$SHOW_GPU_INTER" != "true" ]] || \
       [[ "$queue" == "cpu_batch_large_exec" && "$SHOW_CPU_BATCH_LARGE" != "true" ]] || \
       [[ "$queue" == "cpu_interactive_persistent_exec" && "$SHOW_CPU_INTER_PERS" != "true" ]]; then
        total_jobs=$((total_jobs - 1))
        continue
    fi

    # Used resources
    cpu_time=$(echo "$output" | awk '/resources_used.cput/ {print $3}')
    wall_time=$(echo "$output" | awk '/resources_used.walltime/ {print $3}')
    cpu_percent=$(echo "$output" | awk '/resources_used.cpupercent/ {print $3}')
    [ -z "$cpu_percent" ] && cpu_percent=0
    sum_cpu_percent=$((sum_cpu_percent + cpu_percent))

    # Allocated resources
    alloc_wall=$(echo "$output" | awk '/Resource_List.walltime/ {print $3}')
    alloc_cpu=$(echo "$output" | awk '/Resource_List.ncpus/ {print $3}')
    alloc_gpu=$(echo "$output" | awk '/Resource_List.ngpus/ {print $3}')
    [ -z "$alloc_gpu" ] && alloc_gpu="0"
    node_count=$(echo "$output" | awk '/Resource_List.nodect/ {print $3}')

    # Memory usage
    used_mem_kb=$(echo "$output" | awk '/resources_used.mem/ {print $3}' | sed 's/kb//')
    [ -z "$used_mem_kb" ] && used_mem_kb=0
    alloc_mem_raw=$(echo "$output" | awk '/Resource_List.mem/ {print $3}')

    # Extract numeric value and unit from allocated memory
    alloc_mem_num=$(echo "$alloc_mem_raw" | sed -E 's/([0-9]+)([a-zA-Z]+)/\1/')
    alloc_mem_unit=$(echo "$alloc_mem_raw" | sed -E 's/([0-9]+)([a-zA-Z]+)/\2/')

    # Convert to GB if needed
    case "${alloc_mem_unit,,}" in
        "gb") alloc_mem="$alloc_mem_num" ;;
        "mb") alloc_mem=$(awk "BEGIN {printf \"%.2f\", $alloc_mem_num / 1024}") ;;
        "kb") alloc_mem=$(awk "BEGIN {printf \"%.2f\", $alloc_mem_num / 1048576}") ;;
        *) alloc_mem="$alloc_mem_raw" ;;
    esac

    used_mem_gb=$(awk "BEGIN {printf \"%.2f\", $used_mem_kb / 1048576}")
    sum_mem_use_gb=$(awk "BEGIN {printf \"%.2f\", $sum_mem_use_gb + $used_mem_gb}")
    sum_mem_limit_gb=$(awk "BEGIN {printf \"%.2f\", $sum_mem_limit_gb + $alloc_mem}")

    # Calculate memory usage percentage
    mem_use_pct=$(awk "BEGIN {printf \"%.1f\", ($used_mem_gb / $alloc_mem) * 100}")
    sum_mem_use_pct=$(awk "BEGIN {printf \"%.1f\", $sum_mem_use_pct + $mem_use_pct}")

    # GPU metrics - Handle CPU-only jobs
    if [ "$alloc_gpu" != "0" ]; then
        # This is a GPU job
        total_gpu_jobs=$((total_gpu_jobs + 1))

        gpu_mem=$(echo "$output" | awk '/resources_used.gpu_mem_avg/ {print $3}')
        [ -z "$gpu_mem" ] && gpu_mem=0
        gpu_mem_pct="${gpu_mem}%"
        sum_gpu_mem_pct=$(awk "BEGIN {printf \"%.1f\", $sum_gpu_mem_pct + $gpu_mem}")

        gpu_util=$(echo "$output" | awk '/resources_used.gpu_percent_avg/ {print $3}')
        if [[ ! -z "$gpu_util" && "$gpu_util" -gt 100 ]]; then
            # Adjust GPU utilisation percentage if needed (some systems report in thousandths)
            gpu_util_adj=$(awk "BEGIN {printf \"%.1f\", $gpu_util / 1000}")
            gpu_util_pct="${gpu_util_adj}%"
            sum_gpu_util=$(awk "BEGIN {printf \"%.1f\", $sum_gpu_util + $gpu_util_adj}")
        else
            [ -z "$gpu_util" ] && gpu_util=0
            gpu_util_pct="${gpu_util}%"
            sum_gpu_util=$(awk "BEGIN {printf \"%.1f\", $sum_gpu_util + $gpu_util}")
        fi
    else
        # This is a CPU-only job
        gpu_util_pct="N/A"
        gpu_mem_pct="N/A"
    fi

    # Calculate wall time efficiency
    wtimesec=$(time_to_seconds "$wall_time")
    wlimitsec=$(time_to_seconds "$alloc_wall")
    sum_wall_seconds=$((sum_wall_seconds + wtimesec))
    sum_wall_limit_seconds=$((sum_wall_limit_seconds + wlimitsec))

    wall_efficiency=$(awk "BEGIN {printf \"%.1f\", ($wtimesec / $wlimitsec) * 100}")
    sum_wall_efficiency=$(awk "BEGIN {printf \"%.1f\", $sum_wall_efficiency + $wall_efficiency}")

    # Print row with improved formatting
    printf "%-13s %-11s %-11s %-11s %-9s %-10s %-10s %-9s %-9s %-10s %-8s %-10s %-8s %-8s\n" \
    "${job}" "$wall_time" "$alloc_wall" "$cpu_time" "$cpu_percent%" \
    "${used_mem_gb}GB" "${alloc_mem}GB" "${mem_use_pct}%" "$gpu_util_pct" "$gpu_mem_pct" \
    "$alloc_gpu" "$alloc_cpu" "$node_count" "$queue"
done

# Calculate averages
if [ $total_jobs -gt 0 ]; then
    avg_cpu_percent=$(awk "BEGIN {printf \"%.1f\", $sum_cpu_percent / $total_jobs}")
    avg_mem_use_gb=$(awk "BEGIN {printf \"%.2f\", $sum_mem_use_gb / $total_jobs}")
    avg_mem_use_pct=$(awk "BEGIN {printf \"%.1f\", $sum_mem_use_pct / $total_jobs}")
    avg_mem_limit_gb=$(awk "BEGIN {printf \"%.2f\", $sum_mem_limit_gb / $total_jobs}")
    avg_wall_seconds=$((sum_wall_seconds / total_jobs))
    avg_wall_limit_seconds=$((sum_wall_limit_seconds / total_jobs))
    avg_wall_efficiency=$(awk "BEGIN {printf \"%.1f\", $sum_wall_efficiency / $total_jobs}")

    # Only calculate GPU averages if we have GPU jobs
    if [ $total_gpu_jobs -gt 0 ]; then
        avg_gpu_util=$(awk "BEGIN {printf \"%.1f\", $sum_gpu_util / $total_gpu_jobs}")
        avg_gpu_mem_pct=$(awk "BEGIN {printf \"%.1f\", $sum_gpu_mem_pct / $total_gpu_jobs}")
        gpu_util_display="${avg_gpu_util}%"
        gpu_mem_display="${avg_gpu_mem_pct}%"
    else
        gpu_util_display="N/A"
        gpu_mem_display="N/A"
    fi

    # Format average walltime using the dedicated function
    avg_wall_time=$(format_time $avg_wall_seconds)
    avg_wall_limit=$(format_time $avg_wall_limit_seconds)

    # Print separator and averages row
    printf "%s\n" "$(printf '=%.0s' {1..160})"
    printf "%-13s %-11s %-11s %-11s %-9s %-10s %-10s %-9s %-9s %-10s %-8s %-10s %-8s %-8s\n" \
    "AVERAGE" "$avg_wall_time" "$avg_wall_limit" "-" "${avg_cpu_percent}%" \
    "${avg_mem_use_gb}GB" "${avg_mem_limit_gb}GB" "${avg_mem_use_pct}%" "$gpu_util_display" "$gpu_mem_display" \
    "-" "-" "-" "-"
fi

# Job Statistics
echo ""
echo "Job Statistics:"
echo "--------------"
printf "Total Jobs: %d\n" "$total_jobs"
printf "Jobs with GPU: %d\n" "$total_gpu_jobs"
printf "Jobs CPU-only: %d\n" "$((total_jobs - total_gpu_jobs))"
printf "\nAverage Resource Efficiency:\n"
printf "  CPU Usage: %.1f%%\n" "$avg_cpu_percent"
printf "  Memory Usage: %.1f%% (%.2f GB used / %.2f GB allocated)\n" "$avg_mem_use_pct" "$avg_mem_use_gb" "$avg_mem_limit_gb"
printf "  Walltime Usage: %.1f%%\n" "$avg_wall_efficiency"

# Only show GPU stats if we have GPU jobs
if [ $total_gpu_jobs -gt 0 ]; then
    printf "\nGPU Jobs Metrics (average of %d GPU jobs):\n" "$total_gpu_jobs"
    printf "  GPU Utilisation: %.1f%%\n" "$avg_gpu_util"
    printf "  GPU Memory Usage: %.1f%%\n" "$avg_gpu_mem_pct"
fi
```
