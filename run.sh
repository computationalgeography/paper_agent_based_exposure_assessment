#!/bin/bash
set -e

REALISATIONS=25

for (( i=0; i<${REALISATIONS}; i++ ))
do
  echo "Realisation " $((${i} + 1))
  echo "  Homemaker workday"
  python main.py homemaker_buffer_workday $((${i} + 1)) --arg 10000
  echo "  Homemaker weekend day"
  python main.py homemaker_buffer_weekend $((${i} + 1)) --arg 10000
  echo "  Commuter workday"
  python main.py commuter_workday $((${i} + 1)) --arg 1
done
