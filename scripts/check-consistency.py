#!/usr/bin/python

import os, sys
import json
import glob
from collections import OrderedDict

if __name__ == '__main__':

    # read list of available images.
    with open('./annotated-images.json', 'r') as fp:
        annotated_images = json.load(fp, object_pairs_hook=OrderedDict)

    # create a flattened list of images.
    image_stamps = list()
    for event_i, images_i in annotated_images.items():
        for imsrc_j, imfile_j in images_i.items():
            if not imfile_j:
                continue
            image_stamps.append((event_i, imsrc_j, imfile_j))

    # read existing inspection results.
    inspection_results = list()
    for file_i in glob.glob('./visual-inspection-??.json'):
        fp_i = open(file_i, 'r')
        inspection_results.append(json.load( \
                fp_i, object_pairs_hook=OrderedDict))
        fp_i.close()
    N_dataset = len(inspection_results)

    # construct new
    inspection_cb = OrderedDict()
    for event_i, imsrc_j, imfile_j in image_stamps:
        result_i = list()
        for set_i in inspection_results:
            if (event_i in set_i) and (imsrc_j in set_i[event_i]):
                result_i.append(set_i[event_i][imsrc_j])
        result_i = list(set([w.replace('f', '') for w in result_i]))
        if len(result_i) == 0: # no result
            pass
        elif len(result_i) == 1: # consistent results
            if event_i not in inspection_cb:
                inspection_cb[event_i] = OrderedDict()
            inspection_cb[event_i][imsrc_j] = result_i[0]
        else: # inconsistent results.
            pass

    # save new results.
    with open('visual-inspection-combined.json', 'w') as fp:
        json.dump(inspection_cb, fp, indent=4)
