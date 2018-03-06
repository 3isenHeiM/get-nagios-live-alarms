#!/usr/bin/env python

# Get the live alarms in a running nagios instance
# Changelog:
#  v0.1 20180301    vonStauffenFeld    Initial release
#
# 
#

import errno
import socket
import os
from optparse import OptionParser
from copy import copy
import logging
from logging import handlers
import string
import sys
from time import sleep

# ---- constants ---------------------------------------------------------------
STATUSFILE="/usr/local/nagios/var/status.dat"
LOGFILE = "/var/log/file.log"

# Globals lists to store the Nagios live alarms
result = []
path = []

# ---- Configure logging correctly -------------------------------------------
def configureLogging():
    ## VARIABLES
    format_entry = '%(asctime)s.%(msecs)03d [%(levelname)-8s] %(message)s'
    format_date = '%Y-%m-%d %H:%M:%S'

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(format_entry, format_date)

    # Output the logs if asked (DEBUG mode)
    if options.console :
        # Logging to sys.stderr
        consolehandler = logging.StreamHandler(sys.stdout)
        #consolehandler.setLevel(log_lvl)
        consolehandler.setFormatter(formatter)
        logger.addHandler(consolehandler)

    try :
        # Log file rotation is assured by logrotate
        filehandler = logging.FileHandler(options.logfile)

        # We can set here different log formats for the stderr output !
        #filehandler.setLevel(0)
        # use the same format as the file
        filehandler.setFormatter(formatter)
        # add the handler to the root logger
        logger.addHandler(filehandler)

    except Exception as e :
        if hasattr(e, 'message') :
            logging.fatal("Exception caught : %s" %e)#.message)
        else :
            logging.fatal("Exception %s caught" %e)

    logging.info("*** Begin of %s ***" %sys.argv[0] )
    logging.info("Logging correctly configured.")


def getNagiosStatus(path):
    """
    Parse the Nagios status.dat file into a dict to give the ability to report
    on host/service information

    `path` is the absolute path to the Nagios status.dat

    Return dict() if OK

    source : https://codereview.stackexchange.com/a/48844/162323
    """
    result = {}
    mode = None
    #modes = ['hoststatus', 'servicestatus', 'info', 'programstatus']
    modes = ['hoststatus', 'servicestatus']

    with open(path, 'r') as f:
        for line in f:
            line = line.strip()

            # Mode starting
            if line.endswith('{'):
                mode = line.split()[0]

                if mode in modes:
                    record = {}
                    if mode not in result:
                        result[mode] = {}
                else:
                    mode = None

            # Mode ending
            elif line.endswith('}') and mode:
                if 'hoststatus' in mode:
                    result[mode][record['host_name']] = record.copy()

                elif 'servicestatus' in mode:
                    if record['host_name'] not in result[mode]:
                        result[mode][record['host_name']] = {}

                    result[mode][record['host_name']][
                            record['service_description']] = record.copy()
                else:
                    result[mode] = record.copy()

                mode = None

            # Collect the data if we are interested
            elif mode:
                data = line.split('=', 1)
                if len(data) > 1:
                    record[data[0]] = data[1]

    return result


# ---- Parse the Nagios status dictionnary and outputs a list of host/services
#      with the "target" value different than 0
#      Input : dictionnary & value to look for
def getAlarms(dictionnary, target):

    for key, value in dictionnary.items():
        path.append(key)
        # Check if nested dictionnary, to use recursion
        if isinstance(value, dict):
            getAlarms(value, target)

        # Match on the inputted value
        if key == target:
            if dictionnary[target] != '0':
              # last element is the 'last_hard_state', and we do not pass it to the path variable
              result.append(copy(path[:-1]))
        path.pop()

    return result

# ---- Parse the command-line arguments and set the options accordingly
def create_options():
  desc = '%s (%s). Version %s.' % (about_info["name"],
                                  about_info["product_number"],
                                  about_info["version"])
  parser = OptionParser(description = desc)

## MANAGEMENT OPTIONS  
  parser.add_option('--console',
    dest='console', action='store_true', default=False,
    help = "If logging to console is wanted. Debug only")

  parser.add_option("-o", "--output-path", type = "string",
    dest = "logfile", action = "store", default = LOGFILE,
    help = "Logfile to write into. The Directory must have " \
            "been created in advance. " \
           "Default is '%s'" % LOGFILE)

  parser.add_option("-s", "--status-file", type = "string",
    dest = "statusfile", action = "store", default = STATUSFILE,
    help = "Path to the Nagios status file, to determine the live alarms." \
           "Default is '%s'" % STATUSFILE)

  (options, args) = parser.parse_args()
  return [options, args, parser]



if __name__ == "__main__" :

        (options, args,parser) = create_options()
        configureLogging()

       ################################################################################
       #
       #                               m a i n l i n e
       #
       ################################################################################

        # Parse the nagios status file  

        nagios_status = getNagiosStatus(options.statusfile)
        #print nagios_status['servicestatus']['localhost']["SSH"]['current_state']
        #print nagios_status

        # Extract the services/hosts in alarm
        alarms = getAlarms(nagios_status, 'last_hard_state')
        #print alarms

        # List of the services currently in alarm
        serviceTraps=[]

        # List of the hosts currently in alarm
        hostTraps=[]

        for i in result:
                if i[0] == 'servicestatus' :
                        serviceTraps.append(i[1:])
                elif i[0] == 'hoststatus' :
                        hostTraps.append(i[1])

        #print(serviceTraps)
        #print(hostTraps)
 
        logging.info("*** End of program %s." %sys.argv[0])
        exit(0)

#EOF
   
    
    
    
    
    
    
    
    
