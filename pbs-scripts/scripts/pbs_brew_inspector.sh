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
