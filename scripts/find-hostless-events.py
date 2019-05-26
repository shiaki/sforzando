#!/usr/bin/python

'''
    Find candidates of 'hostless' events
'''

import os
import json
import glob
from collections import OrderedDict

osc_dir = './Transient-catalogs/supernovae/'

def read_supernovae():
    '''
    Iterate over JSON files in OSC
    '''
    for subdir, dirs, files in os.walk(osc_dir):
        for file_i in files:
            if '.json' != file_i.lower()[-5:]:
                continue
            with open(subdir + '/' + file_i, 'r') as fp:
                yield json.load(fp)

def claimedtype_to_str(claimedtype):
    '''
    Convert `claimedtype` field to human-readable style
    '''
    rstr = list()
    for rec_i in claimedtype:
        if rec_i['value'] in ['Candidate', 'LGRB']:
            continue
        type_i, descr_i = rec_i['value'], list()
        if ('kind' in rec_i) and rec_i['kind']:
            descr_i.append(rec_i['kind'][:5])
        if ('probability' in rec_i) and rec_i['probability']:
            descr_i.append('p=%.2f'%(float(rec_i['probability'])))
        if descr_i:
            rstr.append('%s (%s)'%(type_i, ', '.join(descr_i)))
        else:
            rstr.append(type_i)
    return '; '.join(rstr)

def select_coord(ra_list, dec_list):
    '''
    Find the most referred coordinates of a event.
    '''
    ref_idc = dict()
    for rec_i in ra_list + dec_list: # get unique reference sources
        for id_i in [int(x) for x in rec_i['source'].split(',')]:
            ref_idc[id_i] = [0, 0]

    # count ref sources for ra and dec
    crds = {ki: ['', ''] for ki, vi in ref_idc.items()}
    for rec_i in ra_list:
        for id_i in [int(x) for x in rec_i['source'].split(',')]:
            ref_idc[id_i][0] += 1
            if not crds[id_i][0]:
                crds[id_i][0] = rec_i['value']
    for rec_i in dec_list:
        for id_i in [int(x) for x in rec_i['source'].split(',')]:
            ref_idc[id_i][1] += 1
            if not crds[id_i][1]:
                crds[id_i][1] = rec_i['value']

    # remove unpaired reference sources, and find the most referred src.
    ref_idc_rc = {ki: vi[0] for ki, vi in ref_idc.items() if vi[0] == vi[1]}
    if not ref_idc_rc: # dirty patch for multiple values with the same ref code
        ref_idc_rc = {ki: vi[0] for ki, vi in ref_idc.items()}
    src_id_sel = max(ref_idc, key=ref_idc.get)

    # return values.
    return tuple(crds[src_id_sel])

if __name__ == '__main__':

    candidate_events = OrderedDict()
    fmtstr = '{:32} {:40} {:24} {:24} {:16}'

    # read events
    for event_i in read_supernovae():
        for event_name_i, event_info_i in event_i.items():

            # skip events with host names
            '''
            if ('host' in event_info_i) and event_info_i['host']:
                continue
            '''
            # Host name condition removed, 052519, YJ
            # Some hostless SNe have host names! (Anon)

            # skip events without valid redshift
            if not (('redshift' in event_info_i) \
                    and event_info_i['redshift']):
                continue

            # skip events without type classification
            if not (('claimedtype' in event_info_i) \
                    and event_info_i['claimedtype']):
                continue

            # skip events with only a `Candidate` or 'LGRB' flag.
            type_descr_i = claimedtype_to_str(event_info_i['claimedtype'])
            if not type_descr_i:
                continue

            # skip events without coordinates
            if ('ra' not in event_info_i) or ('dec' not in event_info_i) \
                    or (not event_info_i['ra']) or (not event_info_i['dec']):
                continue

            # get RA, Dec, redshift of this event.
            ra_i, dec_i = select_coord(event_info_i['ra'], event_info_i['dec'])

            # get redshift of the event (only the first one.)
            zred_i = event_info_i['redshift'][0]['value']

            # New: only select events within z~0.1 (YJ, 20190506)
            if float(zred_i) > 0.1:
                continue

            # this is a candidate event.
            cand_i = [event_name_i, type_descr_i, ra_i, dec_i, zred_i]
            print(fmtstr.format(*cand_i))

            # save into dict.
            candidate_events[event_name_i] = OrderedDict([
                ('ra', ra_i),
                ('dec', dec_i),
                ('type', type_descr_i),
                ('redshift', zred_i),
            ])

    # save into a file.
    with open('candidate-events.json', 'w') as fp:
        json.dump(candidate_events, fp, indent=4)
    print('Number of candidates:', len(candidate_events))

# EOF
