#!/usr/bin/python

'''
    List events with the nearest source beyond 30 proper kpc

    190506: Flags for survey coverage (YJ)
'''

import json
from collections import namedtuple, OrderedDict

import numpy as np
from astropy.coordinates import SkyCoord

survey_datasets = [
    'SDSS',
    'PS1',
    'DES',
    'LS',
    # 'HyperLEDA',
    # '2MASS-PSC',
    # '6dFGS',
    # '2MASS-XSC',
    'Gaia2',
]

source_name_order = [
    'HyperLEDA', '2MASS-XSC', '2MASS-PSC',
    'SDSS', 'PS1', 'DES', 'LS',
    '6dFGS', 'Gaia2',
]

if __name__ == '__main__':

    # read events.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read nearest host candidates.
    with open('nearest-host-candidate.json', 'r') as fp:
        nearest_hosts = json.load(fp, object_pairs_hook=OrderedDict)

    # read survey coverage
    with open('survey-coverage.json', 'r') as fp:
        survey_coverage = json.load(fp, object_pairs_hook=OrderedDict)

    fmtstr_event = '{:32} {:28} {:16} {:16} {:16}'
    fmtstr_hostcand = '{:16} {:24} {:10.5f} {:10.5f} {:10.5f} {:10.5f}'
    fmtstr_hostcand_alt = '{:16} {:24} {:10} {:10} {:10} {:10}'
    fmtstr_coverage = '{:6} {:6} {:6} {:6} {:6}'
    fmtstr_links = '{:96} {:96}'

    print(fmtstr_event.format('Event', 'Type', 'RA', 'Dec', 'z') + ' ' \
            + fmtstr_coverage.format(*survey_datasets) + ' ' \
            + fmtstr_hostcand_alt.format('Src', 'Id', 'RA', 'Dec',
                'Dist_asec', 'Dist_kpc') + ' ' \
            + fmtstr_links.format('LS_Link', 'OSC_Link'))

    for event_i, event_info_i in cand_events.items():

        line_1 = fmtstr_event.format(
            event_i,
            event_info_i['type'],
            event_info_i['ra'],
            event_info_i['dec'],
            event_info_i['redshift'],
        )

        # find survey coverage.
        coverage_i = survey_coverage[event_i]
        cov_i = [('Y' if w in coverage_i else ' ') for w in survey_datasets]
        line_2 = fmtstr_coverage.format(*cov_i)

        # get list of nearby host candidates, and group by cross-matching.
        cands_i, cand_group_i = nearest_hosts[event_i], OrderedDict()
        for src_j in cands_i:
            if src_j[-1] not in cand_group_i:
                cand_group_i[src_j[-1]] = list()
            cand_group_i[src_j[-1]].append(src_j)

        # check if object is stellar-like
        is_stellar_i = OrderedDict()
        for j_obj, srcs_j in cand_group_i.items():
            is_stellar_i[j_obj] = any([w[6] == 'S' for w in srcs_j])

        # calc mean proper dist. from field center.
        prop_dist_i = OrderedDict()
        for j_obj, srcs_j in cand_group_i.items():
            prop_dist_i[j_obj] = np.mean([w[8] for w in srcs_j])

        # check cross-matched soruces (groups) within 30 proper kpc.
        nearby_grp_id_i = [k for (k, v) in prop_dist_i.items() \
                if (v < 30.) and (not is_stellar_i[k])]

        # do we have multiple objects?
        N_nearby_grps_i = len(nearby_grp_id_i)

        # locate the nearest group.
        if N_nearby_grps_i:
            nearby_grps_dist_i = [prop_dist_i[i] for i in nearby_grp_id_i]
            i_nearest_grp = nearby_grp_id_i[np.argmin(nearby_grps_dist_i)]
        else:
            i_nearest_grp = -1

        # nearby object found: choose which to display.
        if i_nearest_grp > -1:
            nearest_src_datasrc_i = [source_name_order.index(src_j[0]) \
                    for src_j in cand_group_i[i_nearest_grp]]
            nearest_src_i = cand_group_i[i_nearest_grp][\
                    np.argmin(nearest_src_datasrc_i)]
            nearest_src_i = nearest_src_i[:4] + nearest_src_i[7:]
        else:
            nearest_src_i = None

        # determine what to display at the third column.
        if nearest_src_i:
            line_3 = fmtstr_hostcand.format(*(nearest_src_i))
        else:
            line_3 = fmtstr_hostcand_alt.format('', '', '', '', '', '')

        # before printing the table:
        if nearest_src_i and nearest_src_i[-2] < 20.:
            continue

        # create legacysurvey viewer link.
        event_crd_i = SkyCoord(ra=event_info_i['ra'],
                               dec=event_info_i['dec'],
                               unit=('hour', 'deg'))
        ls_link = 'http://legacysurvey.org/viewer' \
                + '?ra={:.7f}&dec={:.7f}&zoom=16'.format( \
                event_crd_i.ra.deg, event_crd_i.dec.deg)
        osc_link = 'https://sne.space/sne/{:}/'.format(event_i)
        line_4 = fmtstr_links.format(ls_link, osc_link)

        print(' '.join((line_1, line_2, line_3, line_4)))
