#!/usr/bin/env python
"""
Created on Fri Aug 18 09:46:51 PST 2016
Author: Maksym Dolgykh

This script reads statistics for specified ifname from proc before delay and after delay (default delay is 5 seconds), calculates average PPS and prints out result in nagios plugin output format
https://nagios-plugins.org/doc/guidelines.html#PLUGOUTPUT
"""

import argparse
import sys
import re
import time

def read_interface_counters(ifname):
    fhandle = open("/proc/net/dev", "r")
    data = fhandle.read()
    fhandle.close()

    if ifname not in data:
        return None

    counters = dict()
    delimiter = re.compile("[\s]+")
    lines = re.split("[\r\n]+", data)
    for line in lines:
        # find the line with required ifname
        if re.match('.*(%s):.*'%ifname, line):
            line = line.strip()
            columns=delimiter.split(line)
            counters["rx_bytes"]      = int(columns[1])
            counters["rx_packets"]    = int(columns[2])
            counters["rx_errors"]     = int(columns[3])
            counters["rx_dropped"]    = int(columns[4])
            counters["rx_fifo"]       = int(columns[5])
            counters["rx_frame"]      = int(columns[6])
            counters["rx_compressed"] = int(columns[7])
            counters["rx_multicast"]  = int(columns[8])
            counters["tx_bytes"]      = int(columns[9])
            counters["tx_packets"]    = int(columns[10])
            counters["tx_errors"]     = int(columns[11])
            counters["tx_dropped"]    = int(columns[12])
            counters["tx_fifo"]       = int(columns[13])
            counters["tx_frame"]      = int(columns[14])
            counters["tx_compressed"] = int(columns[15])
            counters["tx_multicast"]  = int(columns[16])
    return counters
        
    

def main():
    # Parse command line argument
    parser = argparse.ArgumentParser()
    parser.add_argument("--ifname", type=str, required=True, metavar="INTERFACE_NAME", help="Name of the network interface to check PPS, i.e. eth0, bond0 etc", action="store")
    parser.add_argument("--delay", type=int, choices=range(2,20), default="5", metavar="DELAY_TIME", help="time in seconds to run PPS test, it should be more than 1 second and less 20, i.e. 2, 3, 4 etc. I suggest to set this to a few seconds or more", action="store")
    parser.add_argument("-w", type=int, required=True, metavar="WARN", help="WARN value, if PPS is higher of this value, return WARNING")
    parser.add_argument("-c", type=int, required=True, metavar="CRIT", help="CRITICAL value, if PPS is higher of this value, return CRITICAL")
    args = parser.parse_args()

    # get current counters
    start_time=time.time()
    if_counters_start = read_interface_counters(args.ifname)
    # delay
    time.sleep(args.delay)
    # get new counters
    if_counters_end = read_interface_counters(args.ifname)

    # calculate pps
    end_time=time.time()
    duration=end_time-start_time
    pps=((if_counters_end["rx_packets"]+if_counters_end["tx_packets"])-(if_counters_start["rx_packets"]+if_counters_start["tx_packets"])) / duration

    if pps >= args.c:
        print("PPS CRITICAL: %d | pps=%d" %(pps,pps))
    elif pps >= args.w:
        print("PPS WARNING: %d | pps=%d" %(pps,pps))
    elif pps < args.w:
        print("PPS OK: %d | pps=%d" %(pps,pps))
    else:
        print("UNKNOWN")
    

if __name__ == '__main__':
    main()
