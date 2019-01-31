#!/usr/bin/python

'''
    Get image stamps from major sky surveys.
'''

import os
import sys
import json
from collections import namedtuple, OrderedDict

from tqdm import tqdm
import requests

from astropy.coordinates import SkyCoord

def get_stamp_skyviewer(ra, dec, saveto=None, zoom=14, layer='ls-dr67'):

    '''
    Get image cutout of an object from legacysurvey.org Sky Viewer.
    http://legacysurvey.org/viewer/

    Parameters
    ----------
    ra, dec : float
        R.A. and declination of the image center in degrees.

    saveto : str
        File name of output image ('jpg' automatically added).
        Use `None` to return the image data directly.

    zoom : int
        Level of zoom. Every level scales by a factor of 2.
        Default: 14 for 0.25 arcsec/pix.

    layer : str
        Which survey (and data release) to retrieve.
        Options are: 'sdssco', 'ls-dr67', 'decals-dr7', 'mzls+bass-dr6',
        'decals-dr5', 'des-dr1', 'unwise-neo'

    Returns
    -------
    Saved filename, or binary image data when `saveto` is None.
    '''

    # sanity check
    if layer not in ['sdssco', 'ls-dr67', 'decals-dr7',
            'mzls+bass-dr6', 'decals-dr5', 'des-dr1', 'unwise-neo']:
        raise RuntimeError('Invalid `layer` option.')

    ls_url = '''http://legacysurvey.org//viewer/jpeg-cutout'''
    req_payload = dict(ra=ra, dec=dec, zoom=zoom, layer=layer)
    resp = requests.get(ls_url, params=req_payload)

    # test if empty
    if resp.url.endswith('blank.jpg'):
        raise RuntimeError('Coordinates outside survey footprint.')

    # if nowhere to save, return binary image directly
    if saveto is None:
        return resp.content

    # add jpeg suffix
    if not saveto.endswith('.jpg'):
        saveto += '.jpg'

    # or alternatively, save as an image
    with open(saveto, 'wb') as fp:
        fp.write(resp.content)

    return saveto

def get_stamp_sdss(ra, dec, saveto=None, scale=0.4,):

    '''
    Get image cutout of an object from SDSS DR14 SkyServer.

    Parameters
    ----------
    ra, dec : float
        R.A. and declination of the image center in degrees.

    saveto : str
        File name of output image ('jpg' automatically added).
        Use `None` to return the image data directly.

    scale : float
        Pixel scale of the returned image, in arcsec/pix.

    Returns
    -------
    Filename, or binary image data when `saveto` is None.
    '''

    ss_url = '''http://skyserver.sdss.org/dr14/SkyServerWS/ImgCutout/getjpeg'''
    req_payload = dict(TaskName='Skyserver.Chart.List',
            ra=ra, dec=dec, scale=scale, width=400, height=400, opt='')
    resp = requests.get(ss_url, params=req_payload)

    # if nowhere to save.
    if saveto is None:
        return resp.content

    # add jpeg suffix
    if not saveto.endswith('.jpg'):
        saveto += '.jpg'

    with open(saveto, 'wb') as fp:
        fp.write(resp.content)

    return saveto

if (__name__ == '__main__') and ('run' in sys.argv):

    # read events.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read nearest host candidates.
    with open('nearest-host-candidate.json', 'r') as fp:
        nearest_hosts = json.load(fp, object_pairs_hook=OrderedDict)

    if os.path.isfile('image-cutout.json'):
        with open('image-cutout.json', 'r') as fp:
            image_cutout = json.load(fp, object_pairs_hook=OrderedDict)
    else:
        image_cutout = OrderedDict()

    fname_fmt = './image-stamps/{}-{}.jpg'

    # for events in the list, find their image in major surveys.
    I_counter = 0
    for event_i, event_info_i in tqdm( \
            cand_events.items(), total=len(cand_events)):

        if event_i in image_cutout:
            continue # already retrieved, skip.

        # get its nearest host candidate
        nh_i = nearest_hosts[event_i] # could be empty tuple/list.

        # skip if the nearest host candidate is within 15 kpc.
        if nh_i and nh_i[0][-1] < 15.:
            continue

        # read RA, Dec of the event,
        crd_i = SkyCoord(ra=event_info_i['ra'],
                         dec=event_info_i['dec'],
                         unit=('hour', 'deg'))

        img_files_i = OrderedDict()

        # get image from legacysurvey dr6/7
        fname_i = fname_fmt.format(event_i.replace(' ', '_'), 'DECaLS')
        try:
            img_files_i['DECaLS'] = get_stamp_skyviewer(crd_i.ra.deg, \
                    crd_i.dec.deg, saveto=fname_i, layer='decals-dr7')
        except Exception as err:
            if 'outside survey footprint' in str(err):
                img_files_i['DECaLS'] = None
            else:
                raise

        #
        fname_i = fname_fmt.format(event_i.replace(' ', '_'), 'MzLS-BASS')
        try:
            img_files_i['MzLS-BASS'] = get_stamp_skyviewer(crd_i.ra.deg, \
                    crd_i.dec.deg, saveto=fname_i, layer='mzls+bass-dr6')
        except Exception as err:
            if 'outside survey footprint' in str(err):
                img_files_i['MzLS-BASS'] = None
            else:
                raise
        # due to an unknowm problem in SkyViewer API,
        # we have to retrieve them separately

        # get DES
        fname_i = fname_fmt.format(event_i.replace(' ', '_'), 'DES')
        try:
            img_files_i['DES'] = get_stamp_skyviewer(crd_i.ra.deg, \
                    crd_i.dec.deg, saveto=fname_i, layer='des-dr1')
        except Exception as err:
            if 'outside survey footprint' in str(err):
                img_files_i['DES'] = None
            else:
                raise

        # get SDSS
        fname_i = fname_fmt.format(event_i.replace(' ', '_'), 'SDSS')
        try:
            img_files_i['SDSS'] = get_stamp_skyviewer(crd_i.ra.deg, \
                    crd_i.dec.deg, saveto=fname_i, layer='sdssco')
        except Exception as err:
            if 'outside survey footprint' in str(err):
                img_files_i['SDSS'] = None
            else:
                raise

        image_cutout[event_i] = img_files_i

        I_counter += 1
        if not I_counter % 97:
            with open('image-cutout.json', 'w') as fp:
                json.dump(image_cutout, fp)

    #
    with open('image-cutout.json', 'w') as fp:
        json.dump(image_cutout, fp)

#
if (__name__ == '__main__') and ('test' in sys.argv):

    # ra, dec = 141.3007, -6.8299, IC 2471, a lovely galaxy.
    get_stamp_skyviewer(141.3007, -6.8299, saveto='test.jpg',)
