#!/bin/bash
#
# push-logs.sh
#
# $Id$
# (C) Cmed Ltd, 2004


SYSLOG=syslog


function usage()
{
    echo "Usage: $(basename $0) [-u username] [-d remotedir] [-l (logfile|logdir)] hostname"\
	1>&2
}


function push_log()
{
    local log_file=$1
    local remote_host=$2
    local login=$3
    local directory=$4
    timestamp=$(date -u +%y%m%d-%H%M%S)
    log_name=$(hostname)_$(basename $log_file)_$timestamp
    temp_file=$(tempfile)
    mv $log_file $temp_file
    pkill -HUP -f $SYSLOG
    scp $temp_file $login@$remote_host:$directory/$log_name.tmp
    ssh $login@$remote_host "mv $directory/$log_name.tmp $directory/$log_name"
    rm $temp_file
}


set -e

log_path=$(pwd)
login=root
directory=/var/spool
# Process command line args
while getopts ":u:d:l:" opt; do
    case $opt in
	l ) log_path=$OPTARG
	    ;;
	u ) login=$OPTARG
	    ;;
	d ) directory=$OPTARG
	    ;;
    esac
done
shift $(($OPTIND - 1))
if [ $# -ne 1 ]; then
     usage
     exit 1
fi
remote_host=$1

if [ -d $log_path ]; then
    for log_file in $(ls $log_path); do
        push_log $log_path/$log_file $remote_host $login $directory
    done
else
    push_log $log_path $remote_host $login $directory
fi
