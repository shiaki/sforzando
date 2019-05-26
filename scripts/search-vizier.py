#!/usr/bin/python

'''
    Find possible host galaxies of these candidates.
'''

import os
import sys
import json
from collections import OrderedDict

import numpy as np

from tqdm import tqdm
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.vizier import Vizier

# New, 190506
from astropy.cosmology import WMAP9 as cosmo

from catalogs import *

def as_tuple(rec):
    ''' Convert a table record into a tuple '''
    rv = [w if (not np.ma.is_masked(w)) else None for w in rec]
    return tuple(rv)

# encoder for numpy types from: https://github.com/mpld3/mpld3/issues/434
class npEncoder(json.JSONEncoder):
    """ Special json encoder for np types """
    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
            np.int16, np.int32, np.int64, np.uint8,
            np.uint16,np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
            np.float64)):
            return float(obj)
        elif isinstance(obj,(np.ndarray,)):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

if __name__ == '__main__':

    # read candidates
    with open('candidate-events.json', 'r') as fp:
        candidate_events = json.load(fp, object_pairs_hook=OrderedDict)

    candidate_hosts = OrderedDict()

    # for each event: search for
    I_counter = 0
    for cand_i, cand_info_i in tqdm(candidate_events.items(),
                                    total=candidate_events.__len__()):

        if cand_i in candidate_hosts:
            continue

        # some events do not have complete RA/Dec info.
        if not (cand_info_i['ra'] and cand_info_i['dec']):
            continue

        # construct coord
        crd_i = SkyCoord(ra=cand_info_i['ra'],
                         dec=cand_info_i['dec'],
                         unit=('hour', 'deg'))

        # New 190506: use 30 kpc redshift cut.
        zred_i = np.abs(float(cand_info_i['redshift']))
        try:
            ksc_i = cosmo.kpc_proper_per_arcmin(zred_i).value / 60. # kpc/asec
            rad_i = min(30. / ksc_i, 120.)
        except:
            rad_i = 120.

        # search catalogs. (30" limit)
        tab_list_i = Vizier.query_region(crd_i,
                                         radius=rad_i * u.arcsec,
                                         catalog=vizier_cats)

        sources_i = OrderedDict([('search_radius', rad_i)])
        for cat_name_i, tab_i in tab_list_i._dict.items():
            sources_i[cat_name_i] = list()
            for rec_j in tab_i:
                sources_i[cat_name_i].append(as_tuple(rec_j))

        candidate_hosts[cand_i] = sources_i

        I_counter += 1
        if not (I_counter % 269): # save into a file.
            with open('candidate-hosts.json', 'w') as fp:
                json.dump(candidate_hosts, fp, indent=4, cls=npEncoder)

    # save into a file.
    with open('candidate-hosts.json', 'w') as fp:
        json.dump(candidate_hosts, fp, indent=4, cls=npEncoder)

# EOF
