#!/bin/bash
#
# push-logs.sh
#
# $Id$
# (C) Cmed Ltd, 2004


SYSLOG=syslog  # a pattern that matches process name, not the actual name


function usage()
{
    echo "Usage: $(basename $0) [-u username] [-d remotedir]" \
	"[-l (logfile|logdir)] hostname" 1>&2
}


function push_log()
{
    local log_file=$1
    local remote_host=$2
    local login=$3
    local remotedir=$4
    if [ ! -f $log_file ]; then
	return
    fi
    timestamp=$(date -u +%Y%m%d-%H%M%S)
    log_name=$(hostname)-$(basename $log_file)-$timestamp
    temp_file=$(tempfile)
    mv $log_file $temp_file
    pkill -HUP -f $SYSLOG
    if [ -s $temp_file ]; then
	scp -Bq $temp_file $login@$remote_host:$remotedir/$log_name.copy
	ssh $login@$remote_host \
            "mv $remotedir/$log_name.copy $remotedir/$log_name"
    fi
    rm $temp_file
}


set -e

log_path=$(pwd)
login=root
remotedir=/var/spool
# Process command line args
while getopts ":u:d:l:" opt; do
    case $opt in
	l ) log_path=$OPTARG
	    ;;
	u ) login=$OPTARG
	    ;;
	d ) remotedir=$OPTARG
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
        push_log $log_path/$log_file $remote_host $login $remotedir
    done
else
    push_log $log_path $remote_host $login $remotedir
fi
