#!/bin/bash
#
# push-logs.sh
#
# $Id$
# (C) Cmed Ltd, 2004


USERNAME=root
REMOTEDIR=/var/spool/hacksaw
LOCALDIR=/var/spool/hacksaw
MAXSIZE=""  # maximum size of file to copy in kilobytes

AWK=/usr/bin/awk
COPY_EXT="copying"
HOLD_EXT="onhold"


function usage
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


function scp_file
{
    local filename=$1
    local basename=$(basename $filename)
    scp -Bq $filename $USERNAME@$REMOTEHOST:$REMOTEDIR/$basename.$COPY_EXT
    ssh $USERNAME@$REMOTEHOST \
	"mv $REMOTEDIR/$basename.$COPY_EXT $REMOTEDIR/$basename"
}


function get_file_size
{
    local filename=$1
    ls -lk $filename | $AWK '{ print $5 }'
}


function file_too_large
{
    local filename=$1
    local kbytes=$(get_file_size $filename)
    if [ -n "$MAXSIZE" ]; then
	[ $kbytes -gt $MAXSIZE ]
    else
	return 1
    fi
}


function send_error_message
{
    local log_file=$1
    local lines=$(wc -l $log_file | $AWK '{ print $1 }')
    local kbytes=$(get_file_size $log_file)
    local msg_file=$(tempfile)
    local msg="ERROR: log file too large "
    msg="$msg ($(basename $log_file): $lines lines, $kbytes kB)"
    echo "$(date "+%b %e %T") $(hostname) $(basename $0)[$$]: $msg" > $msg_file
    scp_file $msg_file
    rm -f $msg_file
}


function push_log
{
    local log_file=$1
    if [ ! -f $log_file ]; then
	return
    fi
    if file_too_large $log_file; then
	mv $log_file $log_file.$HOLD_EXT
	send_error_message $log_file
	return
    elif [ -s $log_file ]; then
	scp_file $log_file
    fi
    rm $log_file
}


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

files=$(find $LOCALDIR \
    -type f ! \
    -regex ".*\.\($COPY_EXT\|$HOLD_EXT\)" \
    -maxdepth 1)

for log_file in $files; do
    push_log $log_file
done
