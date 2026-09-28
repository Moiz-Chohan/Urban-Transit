#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HDFS_ROOT="/urbantransit/raw"

hdfs dfs -mkdir -p "$HDFS_ROOT"
hdfs dfs -put -f "$ROOT"/raw_data/*.csv "$HDFS_ROOT"
hdfs dfs -ls "$HDFS_ROOT"
