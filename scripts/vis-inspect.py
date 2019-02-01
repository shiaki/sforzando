#!/usr/bin/python

'''
    Inspect image stamps.

    This is a quick-and-dirty mini-application.
'''

import sys
import os
import json
from collections import OrderedDict, deque, namedtuple

from tkinter import *
import PIL
from PIL import ImageTk, Image

import numpy as np

if __name__ == '__main__':

    # read events.
    with open('candidate-events.json', 'r') as fp:
        cand_events = json.load(fp, object_pairs_hook=OrderedDict)

    # read saved images.
    with open('./annotated-images.json', 'r') as fp:
        annotated_images = json.load(fp, object_pairs_hook=OrderedDict)

    # create a flattened list of images.
    image_stamps, i_current, i_sequence = list(), -1, list()
    for event_i, images_i in annotated_images.items():
        for imsrc_j, imfile_j in images_i.items():
            if imfile_j: # skip null
                image_stamps.append((event_i, imsrc_j, imfile_j))

    # read existing results.
    if os.path.isfile('./visual-inspection.json'):
        with open('./visual-inspection.json', 'r') as fp:
            inspection = json.load(fp, object_pairs_hook=OrderedDict)
    else:
        inspection = OrderedDict()

    # get next image.
    def next_image(): # better into an iterator.
        global i_current, i_sequence
        i_sequence.append(i_current)
        i_current += 1
        while True: # fast-forward to the first uninspected image.
            event_i, imsrc_i, imfile_i = image_stamps[i_current]
            if event_i not in inspection: break
            if imsrc_i not in inspection[event_i]: break
            i_current += 1
        return image_stamps[i_current]

    # get next image.
    def prev_image():
        global i_current, i_sequence
        if i_current == 0: # first image, do nothing.
            return image_stamps[i_current]
        i_current = i_sequence.pop() # or step back
        return image_stamps[i_current]

    # before showing images: ff to the next image.
    event_i, imsrc_i, imfile_i = next_image()
    print(i_current, event_i, imsrc_i, imfile_i)

    # display an empty window.
    root = Tk()
    root.geometry('800x800')

    basewidth = 800
    canvas = Canvas(root, height=basewidth, width=basewidth)
    image_i = Image.open(imfile_i)
    wpercent = (basewidth / float(image_i.size[0]))
    hsize = int((float(image_i.size[1]) * float(wpercent)))
    image_i = image_i.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
    photo_i = ImageTk.PhotoImage(image_i)
    canvas_image = canvas.create_image(400, 400, image=photo_i)
    canvas.pack(side=TOP, expand=True, fill=BOTH)

    def render(imfile_i):
        image_i = Image.open(imfile_i)
        image_i = image_i.resize((basewidth, hsize), PIL.Image.ANTIALIAS)
        canvas.img = ImageTk.PhotoImage(image_i)
        canvas.create_image(400, 400, image=canvas.img)

    def prev_key(event):
        canvas.delete('all')
        event_i, imsrc_i, imfile_i = prev_image()
        print(i_current, event_i, imsrc_i, imfile_i)
        render(imfile_i)

    def next_key(event):
        canvas.delete('all')
        event_i, imsrc_i, imfile_i = next_image()
        print(i_current, event_i, imsrc_i, imfile_i)
        render(imfile_i)

    def mark_as_uncertain(event): # mark host as uncertain.
        print(i_current, 'Marked as uncertain')
        event_i, imsrc_i, imfile_i = image_stamps[i_current]
        if event_i not in inspection:
            inspection[event_i] = OrderedDict()
        inspection[event_i][imsrc_i] = '?'
        next_key(event)

    def mark_as_visible(event): # mark host as visible.
        print(i_current, 'Marked as visible')
        event_i, imsrc_i, imfile_i = image_stamps[i_current]
        if event_i not in inspection:
            inspection[event_i] = OrderedDict()
        inspection[event_i][imsrc_i] = 'y'
        next_key(event)

    def mark_as_absent(event): # mark host as absent
        print(i_current, 'Marked as invisible')
        event_i, imsrc_i, imfile_i = image_stamps[i_current]
        if event_i not in inspection:
            inspection[event_i] = OrderedDict()
        inspection[event_i][imsrc_i] = 'n'
        next_key(event)

    def save_progress(event): # mark host as uncertain.
        with open('./visual-inspection.json', 'w') as fp:
            json.dump(inspection, fp, indent=4)
        print('File saved.')

    root.bind('<Left>', prev_key)
    root.bind('<Right>', next_key)

    root.bind('<Up>', mark_as_visible)
    root.bind('<Down>', mark_as_absent)
    root.bind('q', mark_as_uncertain)
    root.bind('s', save_progress)

    # run program.
    root.mainloop()

    # save again upon exit.
    with open('./visual-inspection.json', 'w') as fp:
        json.dump(inspection, fp, indent=4)
