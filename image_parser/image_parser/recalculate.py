#!/usr/bin/env python

import os, json
import math
from . import Observation

class RecalculateJson:
    def __init__(self, data_file, out_dir=None):
        self.out_dir = out_dir
        print 'Internal output directory: {}\n\n'.format(self.out_dir)

        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        # load in data to recalculate the JSON
        self.data = {}
        data_file.readline()
        for line in data_file:
            (p_id, i_id, io_id, iob_id, user_id, archive_filename, x, y, width, height, s_id) = [z.strip() for z in line.split(',')]

            self.data[str(iob_id)] = Observation(
                    user_id=user_id,
                    species_id=s_id,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    iob_id=iob_id
            )

        print len(self.data)

    def _recalculate_file(self, f, fout):
        """Recalculate a single file"""
        results = json.load(f)
        new_results = {}

        print 'Parsing file: {}\n'.format(f.name)

        for p_id, images in results.iteritems():
            print '\tProject: {}'.format(p_id)
            new_results[p_id] = {}

            p_matches = 0
            p_count = 0
            p_missing = 0
            p_wrong_species = 0

            # pop the "cursory data" out
            if 'matches' in images:
                images.pop('matches')
            if 'count' in images:
                images.pop('count')
            if 'missing' in images:
                images.pop('missing')
            if 'wrong_species' in images:
                images.pop('wrong_species')

            for i_id, i_data in images.iteritems():
                print '\t\tImage: {}'.format(i_id)
                i_matches = len(i_data['results'])
                i_count = i_data['count']
                i_wrong_species = 0
                i_distinct = []
                i_results = []

                for result in i_data['results']:
                    user_1 = result['user1']
                    user_2 = result['user2']

                    if not str(user_1['iob_id']) in self.data or not str(user_2['iob_id']) in self.data:
                        o1 = Observation(
                                user_id=user_1['user_id'],
                                species_id=user_1['s_id'],
                                iob_id=user_1['iob_id'],
                                x=-1,
                                y=-1,
                                width=1,
                                height=1
                            )
                        o2 = Observation(
                                user_id=user_2['user_id'],
                                species_id=user_2['s_id'],
                                iob_id=user_2['iob_id'],
                                x=-1,
                                y=-1,
                                width=0,
                                height=0
                            )
                    else:
                        o1 = self.data[str(result['user1']['iob_id'])]
                        o2 = self.data[str(result['user2']['iob_id'])]

                    # make sure we record these distinct observations
                    if not o1.iob_id in i_distinct:
                        i_distinct.append(o1.iob_id)
                    if not o2.iob_id in i_distinct:
                        i_distinct.append(o2.iob_id)

                    # add to the wrong_species count if needed
                    if o1.s_id != o2.s_id:
                        i_wrong_species = i_wrong_species + 1

                    # append to the results array
                    i_results.append({
                        'distance': math.sqrt(o1.point_proximity(o2)),
                        'percent': o1.area_overlap(o2),
                        'same_species': o1.s_id == o2.s_id,
                        'user_1': {
                            'iob_id': o1.iob_id,
                            's_id': o1.s_id,
                            'user_id': o1.user_id
                        },
                        'user_2': {
                            'iob_id': o2.iob_id,
                            's_id': o2.s_id,
                            'user_id': o2.user_id
                        }
                    })

                # update our missing count
                i_missing = i_count - len(i_distinct)

                # update project counts
                p_matches = p_matches + i_matches
                p_count = p_count + i_count
                p_missing = p_missing + i_missing
                p_wrong_species = p_wrong_species + i_wrong_species

                # update our new_results
                new_results[p_id][i_id] = {
                    'matches': i_matches,
                    'count': i_count,
                    'missing': i_missing,
                    'wrong_species': i_wrong_species,
                    'results': i_results
                }

            new_results[p_id]['matches'] = p_matches
            new_results[p_id]['count'] = p_count
            new_results[p_id]['missing'] = p_missing
            new_results[p_id]['wrong_species'] = p_wrong_species

        # save the data
        json.dump(new_results, fout)

    def recalculate_files(self, fs):
        """Recalculate all the files in a list/tuple"""
        for f in fs:
            fbase = '{}_recalc.json'.format(os.path.basename(f.name).split('.')[0])
            if self.out_dir:
                fname = os.path.join(self.out_dir, fbase)
            else:
                fname = os.path.join(os.path.dirname(f.name), fbase)

            fout = open(fname, 'w')
            try:
                print ''
                self._recalculate_file(f=f, fout=fout)
            finally:
                fout.close()
