#!/usr/bin/env python

import os, sys, glob
import datetime
from PIL import Image

def parse_csv(fname, out_dir):
    f = open(fname, 'r')
    f.readline()

    # create our out_dir
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    # go line by line
    for line in f:
        (p_id, i_id, io_id, iob_id, user_id, archive_filename, x, y, width, height, s_id) = [z.strip() for z in line.split(',')]
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        # create project dir
        p_dir = os.path.join(out_dir, p_id)
        if not os.path.exists(p_dir):
            os.mkdir(p_dir)

        # create image dir
        i_dir = os.path.join(p_dir, i_id)
        if not os.path.exists(i_dir):
            os.mkdir(i_dir)

        # skip if this file already exists
        fout = os.path.join(i_dir, '{}_{}_{}.png'.format(user_id, iob_id, s_id))
        if os.path.exists(fout):
            continue

        img = Image.open(archive_filename, 'r')
        img.crop((x, y, x+width, y+height)).save(fout)
        img.close()

    f.close()

def parse_csvs(basename, out_dir):
    parse_csv('{}_single.txt'.format(basename), os.path.join(out_dir, 'single'))
    parse_csv('{}_multiple.txt'.format(basename), os.path.join(out_dir, 'multiple'))
