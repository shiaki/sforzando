#!/usr/bin/python

'''
    Read results from visual inspection, create new target lists.
'''

import os, sys
import json
import glob, shutil
from collections import OrderedDict

if __name__ == '__main__':

    # read candidate events.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read results of visual inspection
    with open('./visual-inspection.json', 'r') as f:
        vis_insp = json.load(f, object_pairs_hook=OrderedDict)

    '''
    Visual inspection flags:
        c: potential close-by host object
        y: host object visible
        n: host object invisible
        q: poor image quality
        f: flag for interesting cases
    '''

    case_absent, case_visible, case_ambiguous = list(), list(), list()

    # for events in the list, get their inspection results.
    for cand_i, cand_info_i in cand_events.items():

        # skip events w/o vis inspection
        if cand_i not in vis_insp:
            continue

        # get results.
        result_i = ''.join([v for k, v in vis_insp[cand_i].items()])
        is_visible = ('y' in result_i)
        is_absent = ('n' in result_i)

        # case 1: visible
        if is_visible and (not is_absent):
            case_visible.append(cand_i)
            continue

        # case 2: absent
        if (not is_visible) and is_absent:
            case_absent.append(cand_i)
            continue

        # case 3: intermediate, cannot tell.
        case_ambiguous.append(cand_i)

    # print three lists of events.
    fmtstr_event = '{:24} {:32} {:18} {:18} {:16}'
    fmtstr_visinsp = '{:8} {:8} {:8} {:12} {:8}'
    img_srcs = ['SDSS', 'ps1', 'DECaLS', 'MzLS/BASS', 'DES']
    for cand_list in (case_visible, case_absent, case_ambiguous):
        print('\n\n\n\n\n')
        print(fmtstr_event.format('Name', 'Type', 'RA', 'Dec', 'Z'), \
              fmtstr_visinsp.format(*img_srcs))
        for cand_i in cand_list:
            cand_info_i = cand_events[cand_i]
            cand_str = fmtstr_event.format(
                cand_i,
                cand_info_i['type'],
                cand_info_i['ra'],
                cand_info_i['dec'],
                cand_info_i['redshift'],
            )
            vinsp_info_i = vis_insp[cand_i]
            insp_repr_i = list()
            for imsrc_i in img_srcs:
                if imsrc_i not in vinsp_info_i:
                    insp_repr_i.append('N/A')
                    continue
                if 'y' in vinsp_info_i[imsrc_i]:
                    insp_repr_i.append('Y')
                    continue
                if 'n' in vinsp_info_i[imsrc_i]:
                    insp_repr_i.append('N')
                    continue
                insp_repr_i.append('?')
            vinsp_str = fmtstr_visinsp.format(*insp_repr_i)
            print(cand_str, vinsp_str)
