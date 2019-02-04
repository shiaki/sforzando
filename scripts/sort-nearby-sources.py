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
import itertools as itt

from tqdm import tqdm

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.cosmology import WMAP9 as cosmo

from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

import matplotlib.pyplot as plt

from catalogs import *

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

def simple_match(ra_c, dec_c, srcs, dist_tol=2.):

    '''
    "Cross-match" sources within the patch.

    Parameters
    ----------

    '''

    # convert into delta-arcseconds
    cos_d = np.cos(dec_c * np.pi / 180.)
    dasec = lambda w: ((w[2] - ra_c) * 3.6e3 * cos_d, (w[3] - dec_c) * 3.6e3)
    N_srcs, src_crds = len(srcs), list(map(dasec, srcs))

    # calc local dist matrix.
    D = np.zeros((N_srcs, N_srcs), dtype='i4')
    for si_i, si_j in itt.combinations(range(N_srcs), 2):
        sr_i, sr_j = src_crds[si_i], src_crds[si_j]
        if abs(sr_i[0] - sr_j[0]) > dist_tol \
                or abs(sr_i[1] - sr_j[1]) > dist_tol:
            continue
        if np.sqrt((sr_i[0] - sr_j[0]) ** 2 \
                + (sr_i[1] - sr_j[1]) ** 2) > dist_tol:
            continue
        D[si_i, si_j] = D[si_j, si_i] = 1
    D = csr_matrix(D)

    # find connected components
    N_cps, cps_label = connected_components(D)

    # pack and return
    return [si + (li,) for si, li in zip(srcs, cps_label)]

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
                pm_k, pm_err_k, star_flag_k = None, None, 'NA'
                if 'gaia' in cat_j: # for Gaia sources: find proper motion
                    if rec_k[7] is None or rec_k[7] is None:
                        pass
                    else: # find total proper motion and its error.
                        pm_k = np.sqrt(rec_k[7] ** 2 + rec_k[9] ** 2)
                        pm_err_k = np.sqrt((rec_k[7] * rec_k[8]) ** 2 \
                                + (rec_k[9] * rec_k[10]) ** 2) / pm_k
                        star_flag_k = 'S' if (pm_k / pm_err_k > 2.) else '?'
                srcs_i.append((
                    cat_names[cat_j],
                    str(rec_k[srcid_cols[cat_j]]),
                    crd_k.ra.deg, crd_k.dec.deg,
                    pm_k, pm_err_k, star_flag_k,
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
                    None, None, 'NA', # no proper motion in DataLab catalogs.
                    sep_k,
                    sep_k * kpc_per_asec_i
                ))

        # sort then by projected physical dist.
        # srcs_i = list(filter(lambda x: x[-1] < 50., srcs_i)) # within 50 kpc
        # srcs_i = sorted(srcs_i, key=lambda x: x[-1])
        # do NOT perform 50 proper kpc cut.
        srcs_i = simple_match(crd_i.ra.deg, crd_i.dec.deg, srcs_i)

        # put into dict.
        if srcs_i:
            nearest_src[event_i] = srcs_i
        else:
            nearest_src[event_i] = list()

    # save into file.
    with open('nearest-host-candidate.json', 'w') as fp:
        json.dump(nearest_src, fp, indent=4, cls=npEncoder,)

# EOF
