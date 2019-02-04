#!/usr/bin/python

'''
'''

import os, sys
import json
import glob, shutil
from collections import OrderedDict

desti_dirs = dict(
    c='./stamps-clsby/',
    y='./stamps-vis/',
    n='./stamps-abs/',
    q='./stamps-lowqual/',
    f='./stamps-fav/'
)

if __name__ == '__main__':

    # read saved images.
    with open('./annotated-images.json', 'r') as fp:
        annotated_images = json.load(fp, object_pairs_hook=OrderedDict)

    # create a flattened list of images.
    image_stamps = list()
    for event_i, images_i in annotated_images.items():
        for imsrc_j, imfile_j in images_i.items():
            if imfile_j: # skip null
                image_stamps.append((event_i, imsrc_j, imfile_j))

    with open('./visual-inspection.json', 'r') as fp:
        inspection = json.load(fp, object_pairs_hook=OrderedDict)

    for event_i, images_i in inspection.items():
        for imsrc_j, iminsp_j in images_i.items():
            imfile_j = annotated_images[event_i][imsrc_j]
            for flag_k, desti_k in desti_dirs.items():
                if flag_k in iminsp_j:
                    shutil.copy2(imfile_j, desti_k)

#.
