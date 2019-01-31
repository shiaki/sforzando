#!/usr/bin/python

'''
    draw reticles and mark sources in image stamps
'''

import os, sys, json
from collections import OrderedDict, deque

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.cosmology import WMAP9 as cosmo

from PIL import Image, ImageDraw

from catalogs import *

asec_per_deg = 3.6e3

# image size in arcseconds for image files.
stamp_sizes = {
    'SDSS': 256 * 0.20,
    'DES': 256 * 0.25,
    'DECaLS': 256 * 0.25,
    'MzLS-BASS': 256 * 0.25,
}

plot_colors = {
    'SDSS': '#4286f4', # blue
    'LS': '#41d3f4', # cyan
    'PS1': '#f47a42', # orange
    'DES': '#e83be8', # magenta
    '2MASS-PSC': '#d11440', # rosy
    '2MASS-XSC': '#d11440',
    'HyperLEDA': '#ffffff',
    '6dFGS': '#ffffff'
}

def annotate_image(event_name, event_info, survey_name, image_file,
        nearby_srcs, draw_crosshair=True, draw_sources=True, draw_cicle=True,
        circle_radius_kpc=15., desti_dir='./tmp-img/', filename_suffix='',):

    # read image file.
    img = Image.open(image_file)

    # get image size and pixel scale.
    im_w, im_h = img.size
    r2pix = lambda x, y: \
            ((0.5 * x + 0.5) * (im_w - 1.), (0.5 - 0.5 * y) * (im_h - 1))

    imdraw = ImageDraw.Draw(img)

    # draw crosshair
    if draw_crosshair:
        ch_c = '#ffffff'
        imdraw.line([r2pix(0., 0.05), r2pix(0., 0.2)], fill=ch_c, width=1)
        imdraw.line([r2pix(0.051, 0.), r2pix(0.2, 0.)], fill=ch_c, width=1)

    # draw nearby sources
    if draw_sources:

        # get supernova coordinates,
        crd_c = SkyCoord(ra=event_info['ra'],
                         dec=event_info['dec'],
                         unit=('hour', 'deg'))
        ra_c, dec_c = crd_c.ra.deg, crd_c.dec.deg
        cos_dec_c = np.cos(crd_c.dec.radian)

        d2pix = lambda dra, ddec, dscale: r2pix(\
                -2. * dra * asec_per_deg / dscale, \
                2. * ddec * asec_per_deg / dscale)

        # for each catalog src, calculate relative shift.
        for src_i in nearby_srcs:

            # convert relative coord to pixel coord.
            crd_i = SkyCoord(ra=src_i[2], dec=src_i[3], unit=('deg', 'deg'))

            dra_i, ddec_i = ((crd_i.ra.deg - ra_c) * cos_dec_c, \
                    (crd_i.dec.deg - dec_c)) # now in degrees.
            xp_i, yp_i = d2pix(dra_i, ddec_i, stamp_sizes[survey_name])

            if xp_i < 10 or yp_i < 10 \
                    or xp_i > im_w - 1 - 10 or yp_i > im_h - 1 - 10:
                continue # beyond image box.

            imdraw.line([(xp_i - 10, yp_i), (xp_i - 5, yp_i)], fill=plot_colors[src_i[0]])
            imdraw.line([(xp_i, yp_i + 10), (xp_i, yp_i + 5)], fill=plot_colors[src_i[0]])

    if draw_cicle:

        # calc radius.
        zred = float(event_info['redshift'])
        kpc_per_asec = cosmo.kpc_proper_per_arcmin(zred).value / 60.
        arad = (circle_radius_kpc / kpc_per_asec) \
                / (stamp_sizes[survey_name] / im_w)

        imdraw.ellipse([(im_w - 1) / 2. - arad, (im_h - 1) / 2. - arad, \
                (im_w - 1) / 2. + arad, (im_h - 1) / 2. + arad],
                outline='#999999')

    del imdraw

    # generate new filenames.
    src_dir, src_fname = os.path.split(image_file)
    if filename_suffix:
        src_fn_sp = src_fname.split('.')
        src_fn_sp = src_fn_sp[:-1] + [filename_suffix] + src_fn_sp[-1:]
        desti_fname = '.'.join(src_fn_sp)
    else:
        desti_fname = src_fname

    with open(os.path.join(desti_dir, desti_fname), 'wb') as fp:
        img.save(fp, 'JPEG', quality=90, optimize=True)

if __name__ == '__main__':

    # read files.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read nearest host candidates.
    with open('nearest-host-candidate.json', 'r') as fp:
        nearest_hosts = json.load(fp, object_pairs_hook=OrderedDict)

    with open('image-cutout.json', 'r') as fp:
        image_cutout = json.load(fp, object_pairs_hook=OrderedDict)

    # for each single event, for every image stamp
    for event_i, image_info_i in image_cutout.items():
        for imgsrc_i, imgfile_i in image_info_i.items():

            # skip empty images.
            if imgfile_i is None: continue

            # annotate and save.
            nhs_i = nearest_hosts[event_i]
            annotate_image(event_i, cand_events[event_i], imgsrc_i, imgfile_i,
                    nhs_i, filename_suffix='meow')
