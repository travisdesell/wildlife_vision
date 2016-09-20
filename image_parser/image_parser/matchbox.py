#!/usr/bin/env python

import os, sys, glob
import datetime, json
from PIL import Image

class MatchBox:
    def __init__(self, datafile, out_dir=None):
        if out_dir:
            self.out_dir = out_dir
        else:
            self.out_dir = os.path.join(os.path.dirname(f), 'matchbox')

        if not os.path.exists(self.out_dir):
            os.mkdir(self.out_dir)

        self.data = {}
        datafile.readline()
        for line in datafile:
            (p_id, i_id, io_id, iob_id, user_id, archive_filename, x, y, width, height, s_id) = [z.strip() for z in line.split(',')]

            if not p_id in self.data:
                self.data[p_id] = {}

            if not i_id in self.data[p_id]:
                self.data[p_id][i_id] = {
                        'archive_filename': archive_filename,
                        'observations': {}
                }

            self.data[p_id][i_id]['observations'][iob_id] = {
                    'x': int(x),
                    'y': int(y),
                    'width': int(width),
                    'height': int(height),
                    'right': int(x) + int(width),
                    'bottom': int(y) + int(height)
            }

    def match(self, f):
        """Matches all the objects"""
        m_data = json.load(f)
        results = {}

        for p_id, images in m_data.iteritems():
            if not p_id in self.data:
                continue

            results[p_id] = {}
            s_counts = {}

            for i_id, i_data in images.iteritems():
                if not isinstance(i_data, dict) or not 'results' in i_data:
                    continue

                observations = self.data[p_id][i_id]['observations']
                results[p_id][i_id] = []
                matched = []
                i_count = 0

                for i in range(len(i_data['results'])):
                    iob_1 = i_data['results'][i]['user_1']['iob_id']
                    iob_2 = i_data['results'][i]['user_2']['iob_id']

                    # don't double count
                    if iob_1 in matched or iob_2 in matched or not iob_1 in observations or not iob_2 in observations:
                        continue

                    species = i_data['results'][i]['user_1']['s_id']
                    boxes = [
                        observations[iob_1],
                        observations[iob_2]
                    ]

                    # see if any future results are also in here
                    for j in range(i+1, len(i_data['results'])):
                        iob_3 = i_data['results'][j]['user_1']['iob_id']
                        iob_4 = i_data['results'][j]['user_2']['iob_id']

                        if iob_3 == iob_1 or iob_3 == iob_2:
                            if not iob_4 in matched and iob_4 in observations:
                                boxes.append(observations[iob_4])
                                matched.append(iob_4)
                        elif iob_4 == iob_1 or iob_4 == iob_2:
                            if not iob_3 in matched and iob_3 in observations:
                                boxes.append(observations[iob_3])
                                matched.append(iob_3)

                    # do the average first
                    x = 0
                    y = 0
                    right = 0
                    bottom = 0
                    for box in boxes:
                        x = x + box['x']
                        y = y + box['y']
                        right = right + box['right']
                        bottom = bottom + box['bottom']

                    average = {
                        'x': int(x / len(boxes)),
                        'y': int(y / len(boxes)),
                        'right': int(right / len(boxes)),
                        'bottom': int(bottom / len(boxes)),
                        'filename': os.path.join(self.out_dir, p_id, i_id, '{}_average.png'.format(i_count)),
                        'fit': 0
                    }

                    # do the intersect next
                    x = 0
                    y = 0
                    right = -1
                    bottom = -1
                    for box in boxes:
                        if box['x'] > x:
                            x = box['x']
                        if box['y'] > y:
                            y = box['y']
                        if right < 0 or box['right'] < right:
                            right = box['right']
                        if bottom < 0 or box['bottom'] < bottom:
                            bottom = box['bottom']

                    if x > right or y > bottom:
                        intersect = {}
                    else:
                        intersect = {
                            'x': x,
                            'y': y,
                            'right': right,
                            'bottom': bottom,
                            'filename': os.path.join(self.out_dir, p_id, i_id, '{}_intersect.png'.format(i_count)),
                            'fit': 0
                        }

                    # save the json
                    i_count = i_count + 1
                    results[p_id][i_id].append({
                        'species': species,
                        'average': average,
                        'intersect': intersect,
                        'boxes': boxes
                    })

                    # save the images
                    if not os.path.exists(os.path.dirname(average['filename'])):
                        os.makedirs(os.path.dirname(average['filename']))
                    img = Image.open(self.data[p_id][i_id]['archive_filename'], 'r')
                    img.crop((average['x'], average['y'], average['right'], average['bottom'])).save(average['filename'])
                    img.close()

                    if intersect:
                        if not os.path.exists(os.path.dirname(intersect['filename'])):
                            os.makedirs(os.path.dirname(intersect['filename']))
                        img = Image.open(self.data[p_id][i_id]['archive_filename'], 'r')
                        img.crop((intersect['x'], intersect['y'], intersect['right'], intersect['bottom'])).save(intersect['filename'])
                        img.close()

                        if not species in s_counts:
                            s_counts[species] = 0

                        # just the intersect for use later
                        ifname = os.path.join(self.out_dir, p_id, 'intersects', species, '{}.png'.format(s_counts[species]))
                        s_counts[species] = s_counts[species] + 1

                        if not os.path.exists(os.path.dirname(ifname)):
                            os.makedirs(os.path.dirname(ifname))
                        img = Image.open(self.data[p_id][i_id]['archive_filename'], 'r')
                        img.crop((intersect['x'], intersect['y'], intersect['right'], intersect['bottom'])).save(ifname)
                        img.close()

        # dump the json results
        fout = open(os.path.join(self.out_dir, 'matchbox.json'), 'w')
        try:
            json.dump(results, fout)
        finally:
            fout.close()
