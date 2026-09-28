$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$HdfsRoot = '/urbantransit/raw'

Write-Host 'Creating HDFS directory:' $HdfsRoot
hdfs dfs -mkdir -p $HdfsRoot

Write-Host 'Uploading raw transport data...'
hdfs dfs -put -f "$Root\raw_data\*.csv" $HdfsRoot

Write-Host 'HDFS input listing:'
hdfs dfs -ls $HdfsRoot
