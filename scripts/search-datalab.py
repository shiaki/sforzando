#!/usr/bin/python

'''
    Seach DataLab for potential host of these events in DES DR1 and LS DR7
'''

import os
import sys
import json
from collections import OrderedDict, namedtuple

import numpy as np
from tqdm import tqdm

from astropy.coordinates import SkyCoord
from dl import authClient as ac, queryClient as qc
from dl.helpers.utils import convert
from getpass import getpass

if __name__ == '__main__':

    # initialize datalab
    token = ac.login(input('Data Lab user name: '), getpass('Password: '))

    # read candidates
    with open('candidate-events.json', 'r') as fp:
        candidate_events = json.load(fp, object_pairs_hook=OrderedDict)

    if os.path.isfile('candidate-hosts-dl.json'):
        with open('candidate-hosts-dl.json', 'r') as fp:
            candidate_hosts = json.load(fp, object_pairs_hook=OrderedDict)
    else:
        candidate_hosts = OrderedDict()

    # 'radius' of the box.
    box_radius = 30. / 60. / 60. # in degrees

    # for each event: search for
    I_counter = 0
    for cand_i, cand_info_i in tqdm(candidate_events.items(),
                                    total=candidate_events.__len__()):

        if cand_i in candidate_hosts:
            continue

        crd_i = SkyCoord(ra=cand_info_i['ra'],
                         dec=cand_info_i['dec'],
                         unit=('hour', 'deg'))
        cos_delta_i = np.cos(crd_i.dec.radian)

        # DES
        des_query = '''
            SELECT coadd_object_id AS objid, ra, dec
            FROM des_dr1.galaxies
            WHERE ra BETWEEN %f AND %f
                AND dec BETWEEN %f AND %f
        ''' % (
            crd_i.ra.deg  - box_radius / cos_delta_i,
            crd_i.ra.deg  + box_radius / cos_delta_i,
            crd_i.dec.deg - box_radius,
            crd_i.dec.deg + box_radius
        )
        des_qr = qc.query(token, sql=des_query)

        # Legacy Survey DR7
        ls_query = '''
            SELECT ref_id, ra, dec
            FROM ls_dr7.galaxy
            WHERE ra BETWEEN %f AND %f
                AND dec BETWEEN %f AND %f
        ''' % (
            crd_i.ra.deg  - box_radius / cos_delta_i,
            crd_i.ra.deg  + box_radius / cos_delta_i,
            crd_i.dec.deg - box_radius,
            crd_i.dec.deg + box_radius
        )
        ls_qr = qc.query(token, sql=ls_query)

        # put into dict.
        candidate_hosts[cand_i] = OrderedDict([
            ('DES', des_qr),
            ('LS', ls_qr),
        ])

        I_counter += 1
        if not (I_counter % 269): # save into a file.
            with open('candidate-hosts-dl.json', 'w') as fp:
                json.dump(candidate_hosts, fp, indent=4)

    with open('candidate-hosts-dl.json', 'w') as fp:
        json.dump(candidate_hosts, fp, indent=4)
