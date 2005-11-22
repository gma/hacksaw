#!/bin/bash
#
# pull-logs.sh
#
# Note that this script behaves differently to push-logs.sh (other
# than the fact that it pulls logs from another host, rather than
# copying them *to* another host) in two key ways:
#
#   1. it doesn't delete files from the remote host
#   2. it therefore keeps track of the last time a file was retrieved
#
# $Id$
# (C) Cmed Ltd, 2005


USERNAME=root
REMOTEDIR=/var/spool/hacksaw
LOCALDIR=/var/spool/hacksaw
MAXSIZE=""  # maximum size of file to copy in kilobytes

AWK=/usr/bin/awk
LAST_RUN="$(basename $0).time"
COPY_EXT="copying"
HOLD_EXT="onhold"


## Functions

usage()
{
    cat <<EOF 1>&2
Usage: $(basename $0) [OPTIONS] hostname

OPTIONS

    -u username		Remote user name (root)
    -d remotedir	Remote spool directory ($REMOTEDIR)
    -l localdir	        Local log file directory ($LOCALDIR)
    -k kilobytes	Max size of log file (optional)

EOF
    exit 1
}


get_file_size()
{
    local filename=$1
    ssh $USERNAME@$REMOTEHOST ls -lk $filename | $AWK '{ print $5 }'
}


file_too_large()
{
    local filename=$1
    if [ -n "$MAXSIZE" ]; then
	local kbytes=$(get_file_size $filename)
	[ $kbytes -gt $MAXSIZE ]
    else
	return 1
    fi
}


send_error_message()
{
    local log_file=$1
    local lines=$(ssh $USERNAME@$REMOTEHOST wc -l $log_file | \
	$AWK '{ print $1 }')
    local kbytes=$(get_file_size $log_file)
    local msg_file=$LOCALDIR/$(tempfile)
    local msg="ERROR: log file too large "
    msg="$msg ($(basename $log_file): $lines lines, $kbytes kB)"
    echo "$(date "+%b %e %T") $(hostname) $(basename $0)[$$]: $msg" > $msg_file
}


have_been_run_before()
{
    ssh $USERNAME@$REMOTEHOST "test -e $REMOTEDIR/$LAST_RUN"
}


list_remote_files()
{
    local command="find $REMOTEDIR -type f -maxdepth 1 \
	! -regex \".*\.\($COPY_EXT|$HOLD_EXT\)\""
    if have_been_run_before; then
	command="$command -cnewer $REMOTEDIR/$LAST_RUN ! -name $LAST_RUN"
    fi
    ssh $USERNAME@$REMOTEHOST $command
    ssh $USERNAME@$REMOTEHOST "touch $REMOTEDIR/$LAST_RUN"
}


file_doesnt_exist()
{
    local log_file=$1
    ! ssh $USERNAME@$REMOTEHOST test -f $log_file
}


file_not_empty()
{
    local log_file=$1
    ssh $USERNAME@$REMOTEHOST test -s $log_file
}


function scp_file
{
    local filename=$1
    scp $USERNAME@$REMOTEHOST:$filename $LOCALDIR
}


pull_log()
{
    local log_file=$1
    if file_doesnt_exist $log_file; then
	return
    fi
    if file_too_large $log_file; then
	send_error_message $log_file
	ssh $USERNAME@$REMOTEHOST mv $log_file $log_file.$HOLD_EXT
	return
    elif file_not_empty $log_file; then
	scp_file $log_file
    fi
}


## Main program

[ -n "$DEBUG" ] && set -x
set -e

# Process command line args
while getopts ":u:d:l:k:" opt; do
    case $opt in
	u ) USERNAME=$OPTARG
	    ;;
	d ) REMOTEDIR=$OPTARG
	    ;;
	l ) LOCALDIR=$OPTARG
	    ;;
	k ) MAXSIZE=$OPTARG
	    ;;
    esac
done
shift $(($OPTIND - 1))

REMOTEHOST=$1
[ -z $REMOTEHOST ] && usage

files=$(list_remote_files)
for log_file in $files; do
    pull_log $log_file
done
