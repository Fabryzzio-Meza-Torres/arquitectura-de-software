#!/bin/bash
# usage: wait_kernels.sh slug1 slug2 ... ; waits up to ~4.5 min, prints statuses
K=.venv/Scripts/kaggle
end=$((SECONDS+265))
while [ $SECONDS -lt $end ]; do
  all=""; busy=0
  for s in "$@"; do st=$($K kernels status gianpiersegoviaureta/$s 2>&1 | grep -o 'KernelWorkerStatus\.[A-Z_]*'); all="$all $s=$st"; echo "$st" | grep -qE "RUNNING|QUEUED" && busy=1; done
  [ $busy -eq 0 ] && break; sleep 20
done
echo "$all"
