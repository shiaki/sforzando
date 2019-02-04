
'''
    Get PanSTARRS image cutout for our event candidates.

    ** For compatibility issues, please run this script under python2
'''

import os, sys, time
import warnings

import logging
import json
from collections import OrderedDict

import numpy as np

from astropy.coordinates import SkyCoord

from panstamps.downloader import downloader
from panstamps.image import image

def to_bytes(s):
    if isinstance(s, unicode):
        return s.encode('utf-8')
    if isinstance(s, list):
        return [to_bytes(item) for item in s]
    if isinstance(s, dict):
        return OrderedDict(
            [(to_bytes(k), to_bytes(v)) for k, v in s.iteritems()
        ])
    return s

if __name__ == '__main__':

    logging.basicConfig()
    log = logging.getLogger()

    # read events.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_hook=to_bytes,)

    # read nearest host candidates.
    with open('nearest-host-candidate.json', 'r') as fp:
        nearest_hosts = json.load(fp, object_hook=to_bytes,)

    if os.path.isfile('image-cutout-ps1.json'):
        with open('image-cutout-ps1.json', 'r') as fp:
            image_cutout = json.load(fp, object_hook=to_bytes,)
    else:
        image_cutout = OrderedDict()

    I_counter = 0
    for event_i, event_info_i in cand_events.iteritems():

        # read RA, Dec
        ra_i, dec_i = event_info_i['ra'], event_info_i['dec']
        crd_i = SkyCoord(ra=ra_i, dec=dec_i, unit=('hour', 'deg'))

        if crd_i.dec.deg < -35.:
            continue # skip very low latitude sources

        # having valid local images, skip
        if (event_i in image_cutout) and (image_cutout[event_i]['ps1']):
            continue

        # get nearby sources,
        nh_i = nearest_hosts[event_i] # could be empty tuple/list.

        # skip if there is something within 25 kpc
        is_cand = True
        for src_j in nh_i:
            # projected distance > 25 kpc, not a star
            if (src_j[-2] < 25.) and ('S' not in src_j[6]):
                is_cand = False
        if not is_cand:
            continue

        time.sleep(1. + np.abs(np.random.randn())) # no hurry

        # locate image
        try:
            fits_files, jpeg_files, color_files = downloader(
                log=log,
                settings=False,
                downloadDirectory='./ps1-stamps/',
                fits=False,
                jpeg=True,
                arcsecSize=120,
                filterSet='gri',
                color=True,
                singleFilters=False,
                ra='%f'%(crd_i.ra.deg,),
                dec="%f"%(crd_i.dec.deg),
                imageType="stack",
                mjdStart=False,
                mjdEnd=False,
                window=False
            ).get()
        except:
            continue
            # there is an undebuggable error here.

        if not color_files:
            image_cutout[event_i] = dict(ps1=None)
            continue # coordinates beyond survey footprint: skip.

        # get image
        myimage = image(
            log=log,
            settings=False,
            imagePath=color_files[0],
            arcsecSize=120,
            crosshairs=True,
            transient=False,
            scale=True,
            invert=False,
            greyscale=False
        ).get()

        # and rename
        dir_i, fname_i = os.path.split(color_files[0])

        # rename.
        new_name_i = dir_i + '/' + event_i + '-' + fname_i
        os.rename(color_files[0], new_name_i)

        # save into dict.
        image_cutout[event_i] = dict(ps1=new_name_i)

        I_counter += 1
        if not I_counter % 7:
            with open('image-cutout-ps1.json', 'w') as fp:
                json.dump(image_cutout, fp)

    with open('image-cutout-ps1.json', 'w') as fp:
        json.dump(image_cutout, fp)
