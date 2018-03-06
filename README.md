# get-nagios-live-alarms
This script returns the live alarms from nagios, by parsing the status.dat file.

This is based on the "last_hard_state" value or each host/service.
I this value is different than 0, this host/service is in alarm.


Freely adapted from here : https://codereview.stackexchange.com/a/48844/162323
