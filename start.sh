#!/bin/bash

# Start Streamlit in the background
echo "Starting Streamlit Dashboard..."
streamlit run src/ui/dashboard.py --server.port 8080 --server.address 0.0.0.0 &

# Loop for the scanner
while true; do
  echo "Starting scan at $(date)"
  python main.py
  echo "Scan complete. Sleeping for 15 minutes..."
  sleep 900
done
