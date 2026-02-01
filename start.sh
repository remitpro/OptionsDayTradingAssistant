#!/bin/bash

# Loop forever
while true; do
  echo "Starting scan at $(date)"
  python main.py
  echo "Scan complete. Sleeping for 15 minutes..."
  sleep 900
done
