"""
Helsinki time module
This module provides functions to get the current time in Helsinki, Finland, 
taking into account daylight saving time (DST) changes. 
It also includes a function to synchronize the system time with an NTP server.
"""
import time
import ntptime
import config

def last_sunday(year, month):
    days_in_month = 31
    timestamp = time.mktime((year, month, days_in_month, 0, 0, 0, 0, 0))
    weekday = time.localtime(timestamp)[6]  # Monday=0, Sunday=6
    return days_in_month - ((weekday + 1) % 7)


def localtime():
    utc_timestamp = time.time()
    utc = time.localtime(utc_timestamp)
    year = utc[0]

    summer_time_start = time.mktime((
        year,
        3,
        last_sunday(year, 3),
        1, 0, 0, 0, 0
    ))

    summer_time_end = time.mktime((
        year,
        10,
        last_sunday(year, 10),
        1, 0, 0, 0, 0
    ))

    if summer_time_start <= utc_timestamp < summer_time_end:
        offset_hours = 3
    else:
        offset_hours = 2

    return time.localtime(utc_timestamp + offset_hours * 60 * 60)

def sync_time_with_ntp():
    try:
        config.debug_print('Syncing RTC with NTP')
        ntptime.settime()
        config.debug_print('RTC synced: %s' % (time.localtime(),))
    except OSError as error:
        config.debug_print('NTP sync failed: %s' % error)