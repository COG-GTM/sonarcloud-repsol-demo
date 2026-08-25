#!/bin/sh
# Stand-in for the internal reporting CLI used by the export feature.
contract=""
format="pdf"
while [ $# -gt 0 ]; do
  case "$1" in
    --contract) contract="$2"; shift 2 ;;
    --format) format="$2"; shift 2 ;;
    *) shift ;;
  esac
done
echo "report for contract ${contract} generated as ${format}"
