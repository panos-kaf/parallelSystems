#!/bin/bash

USER_TO_WATCH="${1:-$USER}"
COMMAND_TO_RUN="qstat -u $USER_TO_WATCH"
INTERVAL=1

cleanup() {
    echo -e "\n\nWatcher stopped manually. Exiting."
    exit 130
}

trap cleanup SIGINT

echo "Starting job watcher for user: $USER_TO_WATCH"
echo "Monitoring command: $COMMAND_TO_RUN"
sleep 2

while true; do
    OUTPUT=$(qstat -u "$USER_TO_WATCH" 2>&1)
    if [ -z "$OUTPUT" ]; then
        clear
        echo "------------------------------------------------"
        echo "Finished"
        echo "Timestamp: $(date)"
        echo "------------------------------------------------"
        echo -e "\a" # bell
        break
    else
        clear
        echo "--- (Monitoring: $COMMAND_TO_RUN | Interval: ${INTERVAL}s | Ctrl+C to stop) ---"
        echo "--- (Last refresh: $(date +'%Y-%m-%d %H:%M:%S')) ---"
        echo
        echo "$OUTPUT"
    fi

    sleep $INTERVAL
done

echo "Watcher script finished."
exit 0
