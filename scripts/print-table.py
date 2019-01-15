#!/usr/bin/python

'''
    List events with the nearest source beyond 30 proper kpc
'''

import json
from collections import namedtuple, OrderedDict

import numpy as np

if __name__ == '__main__':

    # read events.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read nearest host candidates.
    with open('nearest-host-candidate.json', 'r') as fp:
        nearest_hosts = json.load(fp, object_pairs_hook=OrderedDict)

    fmtstr_event = '{:24} {:32} {:18} {:18} {:16}'
    fmtstr_hostcand = '{:16} {:24} {:10.5f} {:10.5f} {:10.5f} {:10.5f}'
    for event_i, event_info_i in cand_events.items():
        line_1 = fmtstr_event.format(
            event_i,
            event_info_i['type'],
            event_info_i['ra'],
            event_info_i['dec'],
            event_info_i['redshift'],
        )
        nh_i = nearest_hosts[event_i]
        if not nh_i:
            line_2 = ''
        elif nh_i[-1] < 30:
            continue
        else:
            line_2 = fmtstr_hostcand.format(*nh_i)
        print(line_1 + ' ' + line_2)
