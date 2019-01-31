#!/usr/bin/python

'''
    For events in the candidate list, sort out those without nearby objects by
    projected phiscial distance.
'''

import os
import sys
import json
import glob
from collections import OrderedDict, namedtuple

from tqdm import tqdm

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.cosmology import WMAP9 as cosmo

from catalogs import *

def parse_datalab_csv(tab):
    ''' parse src_id, ra, dec from Data Lab '''
    tab = [w.split(',') for w in tab.split('\n')][1:]
    tab = [(str(r[0]), float(r[1]), float(r[2])) for r in tab if len(r) == 3]
    return tab

if __name__ == '__main__':

    # read list of event candidates.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read list of possible hosts (vizier)
    with open('candidate-hosts.json', 'r') as fp:
        cand_hosts_v = json.load(fp, object_pairs_hook=OrderedDict)

    # read list of possible hosts (datalab)
    with open('candidate-hosts-dl.json', 'r') as fp:
        cand_hosts_dl = json.load(fp, object_pairs_hook=OrderedDict)

    # nearest source in any survey.
    nearest_src = OrderedDict()

    # for candidate events
    for event_i, event_info_i in tqdm(cand_events.items(),
                                      total=len(cand_events)):

        # list of nearby sources for this event:
        srcs_i = list()

        # construct coord
        crd_i = SkyCoord(ra=event_info_i['ra'],
                         dec=event_info_i['dec'],
                         unit=('hour', 'deg'))

        # scale of projected distance
        kpc_per_asec_i = cosmo.kpc_proper_per_arcmin( \
                float(event_info_i['redshift'])).value / 60.

        # for Vizier sources:
        tabs_i = cand_hosts_v[event_i]
        for cat_j, tab_j in tabs_i.items():
            ra_colid_j, dec_colid_j = radec_cols[cat_j][0]
            radec_units_j = radec_cols[cat_j][1]
            for rec_k in tab_j:
                try:
                    crd_k = SkyCoord(ra=rec_k[ra_colid_j],
                                     dec=rec_k[dec_colid_j],
                                     unit=radec_units_j)
                except:
                    continue # not my fault :)
                sep_k = crd_i.separation(crd_k).arcsec
                srcs_i.append((
                    cat_names[cat_j],
                    str(rec_k[srcid_cols[cat_j]]),
                    crd_k.ra.deg, crd_k.dec.deg,
                    sep_k,
                    sep_k * kpc_per_asec_i
                ))

        # for DataLab catalogs,
        tabs_i = cand_hosts_dl[event_i]
        for cat_j, tab_j in tabs_i.items():
            tab_ps_j = parse_datalab_csv(tab_j)
            for rec_k in tab_ps_j:
                crd_k = SkyCoord(ra=rec_k[1],
                                 dec=rec_k[2],
                                 unit=('deg', 'deg'))
                sep_k = crd_i.separation(crd_k).arcsec
                srcs_i.append((
                    cat_j,
                    rec_k[0],
                    rec_k[1], rec_k[2],
                    sep_k,
                    sep_k * kpc_per_asec_i
                ))

        # sort then by projected physical dist.
        srcs_i = list(filter(lambda x: x[-1] < 50., srcs_i)) # within 50 kpc
        srcs_i = sorted(srcs_i, key=lambda x: x[-1])

        # put into dict.
        if srcs_i:
            nearest_src[event_i] = srcs_i
        else:
            nearest_src[event_i] = list()

    # save into file.
    with open('nearest-host-candidate.json', 'w') as fp:
        json.dump(nearest_src, fp, indent=4)

# EOF
