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
    'DES': 256 * 0.25 / 0.9375,
    'DECaLS': 256 * 0.25 / 0.9375,
    'MzLS-BASS': 256 * 0.25 / 0.9375,
    'ps1': 120.,
}

plot_colors = {
    'SDSS': '#4286f4', # blue
    'LS': '#41d3f4', # cyan
    'PS1': '#f47a42', # orange
    'DES': '#e83be8', # magenta
    '2MASS-PSC': '#d11440', # rosy
    '2MASS-XSC': '#d11440',
    'HyperLEDA': '#ffffff',
    '6dFGS': '#ffffff',
    'Gaia2': '#ffffff'
}

def annotate_image(event_name, event_info, survey_name, image_file,
        nearby_srcs, draw_crosshair=True, crosshair_len=(0.015, 0.035),
        draw_sources=True, draw_source_groups=True, group_rad=2.0,
        draw_cicle=True, circle_radius_kpc=25., desti_dir='./tmp-img/',
        filename_suffix='', linewidth_factor=1):

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
        imdraw.line([r2pix(0., 0.05), r2pix(0., 0.2)],
                fill=ch_c, width=linewidth_factor)
        imdraw.line([r2pix(0.051, 0.), r2pix(0.2, 0.)],
                fill=ch_c, width=linewidth_factor)

    # draw nearby sources
    if draw_sources or draw_source_groups:

        # get supernova coordinates,
        crd_c = SkyCoord(ra=event_info['ra'],
                         dec=event_info['dec'],
                         unit=('hour', 'deg'))
        ra_c, dec_c = crd_c.ra.deg, crd_c.dec.deg
        cos_dec_c = np.cos(crd_c.dec.radian)

        d2pix = lambda dra, ddec, dscale: r2pix(\
                -2. * dra * asec_per_deg / dscale, \
                2. * ddec * asec_per_deg / dscale)

    if draw_sources:

        # for each catalog src, calculate relative shift.
        for src_i in nearby_srcs:

            # convert relative coord to pixel coord.
            crd_i = SkyCoord(ra=src_i[2], dec=src_i[3], unit=('deg', 'deg'))

            dra_i, ddec_i = ((crd_i.ra.deg - ra_c) * cos_dec_c, \
                    (crd_i.dec.deg - dec_c)) # now in degrees.
            xp_i, yp_i = d2pix(dra_i, ddec_i, stamp_sizes[survey_name])

            im_s = np.sqrt(im_h * im_w)
            ch_li, ch_lo = crosshair_len[0] * im_s, crosshair_len[1] * im_s

            if (xp_i < ch_lo or yp_i < ch_lo) or \
                    (xp_i > im_w - (1 + ch_lo) or yp_i > im_h - (1 + ch_lo)):
                continue # beyond image box.

            imdraw.line([(xp_i - ch_lo, yp_i), (xp_i - ch_li, yp_i)],
                        fill=plot_colors[src_i[0]], width=linewidth_factor)
            imdraw.line([(xp_i, yp_i + ch_lo), (xp_i, yp_i + ch_li)],
                        fill=plot_colors[src_i[0]], width=linewidth_factor)

    if draw_source_groups:

        # arrange sources into
        src_groups = dict()
        for src_i in nearby_srcs:
            if src_i[-1] not in src_groups:
                src_groups[src_i[-1]] = list()
            src_groups[src_i[-1]].append(src_i)

        # plot groups
        for grp_id, grp_srcs in src_groups.items():

            # use proper motion in Gaia DR2 to separate galaxies and stars
            is_stellar = False
            for src_i in grp_srcs:
                if (src_i[0] == 'Gaia2') and (not(src_i[4] is None)):
                    if src_i[4] / src_i[5] > 2.:
                        is_stellar = True
                        # this is a Gaia source with large proper motion.

            # convert relative coord to pixel coord.
            crd_i = SkyCoord(ra=grp_srcs[0][2],
                             dec=grp_srcs[0][3],
                             unit=('deg', 'deg'))
            dra_i, ddec_i = ((crd_i.ra.deg - ra_c) * cos_dec_c, \
                    (crd_i.dec.deg - dec_c)) # now in degrees.
            xp_i, yp_i = d2pix(dra_i, ddec_i, stamp_sizes[survey_name])

            crad = np.sqrt(im_h * im_w) * (group_rad / stamp_sizes[survey_name])
            if (xp_i < crad or yp_i < crad) or \
                    (xp_i > im_w - (1 + crad) or yp_i > im_h - (1 + crad)):
                continue # beyond image box.

            if is_stellar:
                imdraw.ellipse([xp_i - crad, yp_i - crad, \
                        xp_i + crad, yp_i + crad], outline='#333fff',
                        width=linewidth_factor)
            else:
                imdraw.ellipse([xp_i - crad, yp_i - crad, \
                        xp_i + crad, yp_i + crad], outline='#ef6221',
                        width=linewidth_factor)

    if draw_cicle:

        # calc radius.
        zred = float(event_info['redshift'])
        kpc_per_asec = cosmo.kpc_proper_per_arcmin(zred).value / 60.

        if kpc_per_asec != 0.: # in case of bad redshift
            arad = (circle_radius_kpc / kpc_per_asec) \
                    / (stamp_sizes[survey_name] / im_w)
            imdraw.ellipse([(im_w - 1) / 2. - arad, (im_h - 1) / 2. - arad, \
                    (im_w - 1) / 2. + arad, (im_h - 1) / 2. + arad],
                    outline='#999999', width=linewidth_factor)
        else:
            pass

    del imdraw

    # generate new filenames.
    src_dir, src_fname = os.path.split(image_file)
    if filename_suffix:
        src_fn_sp = src_fname.split('.')
        src_fn_sp = src_fn_sp[:-1] + [filename_suffix] + src_fn_sp[-1:]
        desti_fname = '.'.join(src_fn_sp)
    else:
        desti_fname = src_fname

    # write annotated image to new position.
    new_fpath = os.path.join(desti_dir, desti_fname)
    with open(new_fpath, 'wb') as fp:
        img.save(fp, 'JPEG', quality=90, optimize=True)

    # return filename.
    return new_fpath

if (__name__ == '__main__') and ('runls' in sys.argv):

    # read files.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read nearest host candidates.
    with open('nearest-host-candidate.json', 'r') as fp:
        nearest_hosts = json.load(fp, object_pairs_hook=OrderedDict)

    # image cutouts for legacysurvey SkyViewer
    with open('image-cutout.json', 'r') as fp:
        image_cutout = json.load(fp, object_pairs_hook=OrderedDict)

    # get (or create) the list of annotated image stamps.
    if os.path.isfile('./annotated-images.json'):
        with open('./annotated-images.json', 'r') as fp:
            annotated_images = json.load(fp, object_pairs_hook=OrderedDict)
    else:
        annotated_images = OrderedDict()

    # for each single event, for every image stamp
    for event_i, image_info_i in image_cutout.items():

        # output images.
        if event_i not in annotated_images:
            annotated_images[event_i] = OrderedDict()

        for imgsrc_i, imgfile_i in image_info_i.items():

            # skip empty images.
            if imgfile_i is None:
                annotated_images[event_i][imgsrc_i] = None
                continue

            # annotate and save.
            nhs_i = nearest_hosts[event_i]
            outfile_i = annotate_image(event_i, cand_events[event_i],
                    imgsrc_i, imgfile_i, nhs_i, desti_dir='./annotated/')
            annotated_images[event_i][imgsrc_i] = outfile_i

    # save to json.
    with open('annotated-images.json', 'w') as fp:
        json.dump(annotated_images, fp, indent=4)

if (__name__ == '__main__') and ('runps1' in sys.argv):

    # read files.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read nearest host candidates.
    with open('nearest-host-candidate.json', 'r') as fp:
        nearest_hosts = json.load(fp, object_pairs_hook=OrderedDict)

    # image cutouts for panstarrs
    with open('image-cutout-ps1.json', 'r') as fp:
        image_cutout_ps1 = json.load(fp, object_pairs_hook=OrderedDict)

    # get (or create) the list of annotated image stamps.
    if os.path.isfile('./annotated-images.json'):
        with open('./annotated-images.json', 'r') as fp:
            annotated_images = json.load(fp, object_pairs_hook=OrderedDict)
    else:
        annotated_images = OrderedDict()

    for event_i, image_info_i in image_cutout_ps1.items():

        # output images.
        if event_i not in annotated_images:
            annotated_images[event_i] = OrderedDict()

        for imgsrc_i, imgfile_i in image_info_i.items():

            # skip empty images.
            if imgfile_i is None:
                annotated_images[event_i][imgsrc_i] = None
                continue

            # annotate and save.
            nhs_i = nearest_hosts[event_i]
            outfile_i = annotate_image(event_i, cand_events[event_i],
                    imgsrc_i, imgfile_i, nhs_i, desti_dir='./annotated/',
                    draw_crosshair=False, linewidth_factor=3)
            annotated_images[event_i][imgsrc_i] = outfile_i

    # save to json.
    with open('annotated-images.json', 'w') as fp:
        json.dump(annotated_images, fp, indent=4)
