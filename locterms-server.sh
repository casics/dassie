#!/bin/bash
# =============================================================================
# @file    start-locterms.sh
# @brief   Start the LoCTerms database process
# @author  Michael Hucka <mhucka@caltech.edu>
# @license Please see the file named LICENSE in the project directory
# =============================================================================
#
# This script makes use of fragments of code found on Stack Overflow.
# Code contributed to Stack Overflow is licensed CC-BY-SA 3.0.
# https://creativecommons.org/licenses/by-sa/3.0/

version_number="1.0.0"
website="https://github.com/casics/locterms"

# Configuration variables.
# .............................................................................

dump_file="data/lcsh-dump.tgz"
dbpath="lcsh-db"
log_file="locterms.log"
conf_file="locterms.conf"
pid_file="mongod.pid"
port=27017
user=""
password=""

# Body of script.  No more configuration should be necessary after this point.
# .............................................................................

# Default variable values.

program=${0##*/}
args_given="$@"
chatty=true
dry_run=false
foreground=false
use_log_file=true
exit_code=0
start_time=$(/bin/date '+%G-%m-%d:%H%M')
action=""

# Helper functions.

print_usage() {
    convert_paths
cat <<EOF >&2
Usage:
    $program [options] {start|stop|restart|status}

This controls the database process for LoCTerms.  It must be executed from
the directory where the LoCTerm database is located.

If this is the first time that LoCTerms has been invoked and this instance of
the database has never been loaded, $program will automatically
unpack and restore the database archive before starting the server.
(Subsequent invocations of $program will not need to do this,
and startup will be faster.)  The first time will also require you to supply
a database user login and password to be used for authenticating network
connections to the database.  The values will be written to the file
"$conf_file".

Normally, the database server process is started in the background.  This
script makes the database write diagnostic messages to the log file located at
"$log_file"
unless the option "-l" is used to change it.  When debugging problems, it may
be helpful to run the database server in the foreground by using the "-f"
option; note that doing so will mean that output will NOT be written to the
log file.

The database will listen on the network port $port unless it is changed using
the argument "-P".

When connecting clients to the database, use the configuration values for
user name, login and port number found in the LoCTerms config file:
"$conf_file".

Options:
    -c, --config        Use the given file as the LoCTerms configuration file
    -f, --foreground    Run database process in the foreground
    -h, --help          Print this help message and exit
    -l, --logfile       Write logs to the given file instead of the default
    -n, --dry-run       Show what would be done, but don't do it
    -p, --password      Set up authentication (use together with -u)
    -P, --port          Use the given port instead of the default
    -q, --quiet         Don't display informative messages
    -u, --user          Set up authentication (use together with -p)
    -v, --version       Display the current version number and exit

EOF
    print_version
}

print_version() {
    printf '%s\n' "$program version $version_number" 1>&2
    printf '%s\n' "Author:  Mike Hucka <mhucka@caltech.edu>" 1>&2
    printf '%s\n' "Website: $website" 1>&2
}

parse_args() {
    # Parse comand-line options.

    while (( $# > 0 )); do
        case $1 in
            -c | --conf )
                shift
                conf_file=$1
                ;;
            -f | --foreground )
                foreground=true
                use_log_file=false
                ;;
            -h | --help )
                print_usage
                quit 0
                ;;
            -l | --logfile )
                shift
                log_file=$1
                use_log_file=true
                ;;
            -n | --dry-run )
                dry_run=true
                ;;
            -p | --password )
                shift
                password=$1
                ;;
            -P | --port )
                shift
                port=$1
                ;;
            -q | --quiet )
                chatty=false
                ;;
            -u | --user )
                shift
                user=$1
                ;;
            -v | --version )
                print_version
                quit 0
                ;;
            start|stop|restart|status)
                action=$1
                ;;
            *)
                print_usage
                quit 0
                ;;
        esac
        shift
    done
}

prepare_for_action() {
    # Check that actions make sense.  For example, check if the mongod
    # process is alread running.

    if [[ ! $action ]]; then
        say warning "No action specified."
        say warning ""
        print_usage
        quit 0
    fi

    if ! (is_integer $port); then
        say error "Port argument value '$port' is not a number."
        quit 1
    fi

    if [[ $action == start ]]; then
        quit_if_running
    fi

    if [[ $action =~ ^(start|stop|restart)$ ]]; then
        remove_stale_pid_file
        check_log_file
        welcome
    fi
}

dispatch_action() {
    # Do the action requested by the user: start, stop, etc.

    case $action in
        start)
            start_mongod
            ;;
        stop)
            stop_mongod
            ;;
        restart)
            stop_mongod
            start_mongod
            ;;
        status)
            status_mongod
            ;;
    esac
}

recover_database() {
    say info "Saving user credentials to '$conf_file'."
    save_conf_file

    say info "Extracting database dump from '$dump_file'."
    $dry_run || tar xzf "$dump_file"

    start_mongod_process unauthenticated

    say info "Loading dump into running database instance. Note: this step"
    say info "will take time and print a lot of messages. If it succeeds,"
    say info "it will print 'finished restoring $dbpath.terms' near the end."
    say info ""
    $dry_run || mongorestore -v --db $dbpath dump/lcsh

    say info ""
    say info "Configuring user credentials in database."
    config_mongod_user

    say info "Restarting database server process."
    read running pid < <(mongod_running)
    if $running; then
        stop_mongod

        # Mongod can take time to exit. Here we wait for a finite time.
        # Code based on https://unix.stackexchange.com/a/103864/141997
        timeout=10
        while ((timeout > 0)) && ps -p $pid >/dev/null 2>&1; do
            sleep 2
            ((timeout -= 1))
        done
    fi
    start_mongod_process

    say info "Cleaning up."
    $dry_run || /bin/rm -rf dump

    status_mongod
}

save_conf_file() {
    echo "user=$user" > $conf_file
    echo "password=$password" >> $conf_file
    echo "port=$port" >> $conf_file
}

config_mongod_user() {
    if ! $dry_run; then
        # Using --quiet to mongod doesn't stop echoing commands, so
        # need to use output rediction.
        mongo admin <<EOF > /dev/null
db.createUser( { user: "$user", pwd: "$password", roles: [ { role: "read", db: "lcsh-db" } ] } );
EOF
        if (($? > 0)); then
            say error "Unable to configure user creditials."
            say error "You should stop the database and investigate."
            quit 1
        fi
    fi
}

start_mongod_process() {
    # Start the mongod process.

    local mongo_args="--pidfilepath $pid_file --directoryperdb --port $port"
    local log_args="--logpath $log_file --logRotate reopen --logappend"
    local auth_args="--auth"
    local fork="--fork "
    local restore=false

    # If we're running in the foreground, we don't write to the log file.
    # Adjust variables accordingly.
    if ! $use_log_file; then
        log_args=""
    fi
    if $foreground; then
        fork=""
        log_args=""
        say info "database process will be run in the foreground."
    else
        # Default: run in the background
        say info "database process will be forked and run in the background."
    fi

    if [[ ! -z "${1:-}" ]]; then
        # If given an argument, start without authentication
        say info "Starting unconfigured database process."
        $dry_run || mongod $fork $log_args $mongo_args --dbpath=$dbpath
    else
        say info "Starting normal database process."
        $dry_run || mongod $fork $log_args $mongo_args $auth_args --dbpath=$dbpath
    fi
}

start_mongod() {
    # Do the actions to start the database, including possibly restoring it.

    if (database_exists $dbpath); then
        say info "Using database in $dbpath."
    else
        say warning "No database found in '$dbpath'."
        say warning "Will begin by setting up database."
        restore=true
    fi

    if $restore; then
        if [[ -z $user || -z $password ]]; then
            say error "Must supply user and password to set up database."
            quit 1
        else
            say info "Creating local database directory $dbpath."
            $dry_run || mkdir -p "$dbpath"
        fi
    fi

    # Recover the database if necessary.
    if $restore; then
        rotate_log
        recover_database
    else
        start_mongod_process
    fi
}

stop_mongod() {
    read running pid < <(mongod_running)
    if $running; then
        say info "Killing process $pid."
        $dry_run || kill $pid
        $dry_run || rm "$pid_file"
    else
        say warning "LoCTerms database process does not appear to be running."
    fi
}

restart_mongod() {
    stop_mongod
    start_mongod
}

status_mongod() {
    read running pid < <(mongod_running)
    if $running; then
        say info "LoCTerms database process is running with PID $pid."
    else
        say warning "LoCTerms database process does not appear to be running."
    fi
}

check_log_file() {
    if $use_log_file && [[ -n $log_file ]]; then
        if [[ -e "$log_file" && ! -w "$log_file" ]]; then
            printf '%s\n' "Unable to write log file $log_file."
            use_log_file=0
            quit 1
        fi
    fi
}

check_conf_file() {
    if [[ -n $conf_file ]]; then
        . $conf_file
        if [[ -z $user ]]; then
            say error "No user name set for authentication."
            quit 1
        fi
        if [[ -z $password ]]; then
            say error "No password set for authentication."
            quit 1
        fi
    fi
}

remove_stale_pid_file() {
    if [[ -f "$pid_file" ]]; then
        read running pid < <(mongod_running)
        if ! $running; then
            say warning "Removing stale file $pid_file."
            rm -f "$pid_file"
        fi
    fi
}

convert_paths() {
    # Convert relative paths to absolute.

    log_file=$(abspath $log_file)
    pid_file=$(abspath $pid_file)
    conf_file=$(abspath $conf_file)
}

# Code modified from https://stackoverflow.com/a/31861475/743730
abspath() {
    # Takes an argument, a file, and returns its absolute path.

    if [[ -d "$1" ]]; then
        cd "$1"
        echo `/bin/pwd -P`
    else
        cd `dirname "$1"`
        echo `/bin/pwd -P`/`basename "$1"`
    fi
}

# This function modified from http://stackoverflow.com/a/17686989/743730
mongod_running() {
    # Returns 1-2 values: a Boolean and optionally the pid.

    local status=false
    if [[ -f "$pid_file" ]]; then
        if [[ -n $(pgrep -F $pid_file) ]]; then
            local pid=$(< "$pid_file")
            status="true $pid"
        fi
    else
        # We don't have a pid file, but sometimes things go wrong and our
        # mongod process may be running after all.
        if [[ -n $(pgrep lcsh) ]]; then
            local pid=$(pgrep lcsh)
            say warning "No pid file found, but database seems to be running"
            status="true $pid"
        fi
    fi
    echo $status
}

quit_if_running() {
    # Check for pid file.  If present, it may indicate a locterms mongod
    # process is already running.

    read running pid < <(mongod_running)
    if $running; then
        say error "It appears a database process with pid $pid is running."
        say error "Use 'stop' or 'restart' to stop the previous process."
        say error "If that fails, remove file $pid_file."
        quit 1
    fi
}

welcome() {
    # Set the start time and print a welcome message.
    # Note: this can't be run until after the log file is set up.

    log ""
    log "===== $program started at $start_time ====="
    log "Arguments given: $args_given"
    log "Logging output to $log_file"

    if $dry_run; then
        say info "Dry run."
    fi
}

quit() {
    # Exit with the status code in $1.
    # If given arg $2, it's a string to be both printed and logged.

    if [[ ! -z "${2:-}" ]]; then
        say warning "$2"
    fi
    if [[ $action =~ ^(start|stop|restart)$ ]]; then
        local stop_time=$(/bin/date '+%G-%m-%d:%H%M')
        log "===== $program exited at $stop_time with exit code $1 ====="
    fi
    exit $1
}

say() {
    # Takes 2 arguments: a severity code, and a text string.
    # Prints a message to the terminal, unless the code is "note"
    # and $chatty is not 1.  Always logs the message.

    local code=$1
    local msg=$2

    log "$msg"

    local BLACK=`tput setaf 0`
    local RED=`tput setaf 1`
    local GREEN=`tput setaf 2`
    local YELLOW=`tput setaf 3`
    local BLUE=`tput setaf 4`
    local MAGENTA=`tput setaf 5`
    local CYAN=`tput setaf 6`
    local WHITE=`tput setaf 7`
    local RESET=`tput sgr0`

    case $code in
        info)
            if $chatty; then
                printf "${GREEN}%s${RESET}\n" "$2"
            fi
            ;;
        warning)
            printf "${YELLOW}%s${RESET}\n" "$2"
            ;;
        error)
            printf "${RED}%s${RESET}\n" "$2"
            ;;
    esac
}

log() {
    # Log a message to the log file.

    if $use_log_file && [[ -n $log_file ]]; then
        printf '%s\n' "$*" >> "$log_file"
    fi
}

rotate_log() {
    if $use_log_file && [[ -e "$log_file" ]]; then
        say info "Moving old log file to $log_file.old"
        /bin/mv $log_file $log_file.old
    fi
}

database_exists() {
    [[ -d $1/lcsh && -e $1/WiredTiger ]]
}

is_integer() {
    [[ $1 =~ ^[0-9]+$ ]]
}

# Main entry point.

parse_args "$@"
convert_paths
prepare_for_action
dispatch_action

quit $exit_code
