#!/usr/bin/env python

import os, json
import math
from . import Observation

class ConfirmTests:
    def __init__(self, fname, out_dir):
        self.out_dir = out_dir
        self.data = {}

        # create the out_dir if needed
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)

        # read in the data
        f = open(fname, 'r')
        f.readline()
        for line in f:
            (p_id, i_id, io_id, iob_id, user_id, archive_filename, x, y, width, height, s_id) = [z.strip() for z in line.split(',')]

            # only create the project once
            if not p_id in self.data:
                self.data[p_id] = {}

            # only create the image once
            if not i_id in self.data[p_id]:
                self.data[p_id][i_id] = {}

            # only create the user once
            if not user_id in self.data[p_id][i_id]:
                self.data[p_id][i_id][user_id] = []

            # store the observation
            self.data[p_id][i_id][user_id].append(Observation(user_id, s_id, x, y, width, height, iob_id))

        # close the file
        f.close()

    def test_all(self):
        """Runs all of our tests."""
        self.area_test(50)
        self.area_test(60)
        self.area_test(70)
        self.area_test(80)
        self.area_test(90)

        self.point_test(5)
        self.point_test(10)
        self.point_test(15)
        self.point_test(20)

    def test(self, fileName, comparisonMethod, comparisonValue, comparisonType):
        results = {}

        for p_id, images in self.data.iteritems():
            results[p_id] = {}
            p_matches = 0
            p_missing = 0
            p_count = 0

            for i_id, users in images.iteritems():
                user_ids = users.keys()
                results[p_id][i_id] = {'matches': 0, 'results': [], 'count': 0}
                i_matches = 0
                i_missing = 0
                i_count = 0

                # get the image count
                for user_id in user_ids:
                    i_count = i_count + len(users[user_id])

                # add all our last row to the not_matched dict
                not_matched = {}
                for o in users[user_ids[len(user_ids)-1]]:
                    not_matched[o.iob_id] = {
                            'user_id': o.user_id,
                            's_id': o.s_id,
                            'iob_id': o.iob_id
                    }

                # go from left to right, not looking back
                for i in range(len(user_ids)-1):
                    for o1 in users[user_ids[i]]:
                        matched = False

                        # go from the next user through to the end
                        for j in range(i+1, len(user_ids)):
                            for o2 in users[user_ids[j]]:

                                # compare these two observations
                                comp = getattr(o1, comparisonMethod)(o2)
                                if (comparisonType < 0 and comp <= comparisonValue) or \
                                            (comparisonType > 0 and comp >= comparisonValue) or \
                                            (comparisonType == 0 and comp == comparisonValue):

                                    # add to last matched, if needed
                                    if (j == (len(user_ids) - 1)):
                                        if o2.iob_id in not_matched:
                                            del not_matched[o2.iob_id]

                                    matched = True
                                    i_matches = i_matches + 1
                                    results[p_id][i_id]['results'].append({
                                        'user1': {
                                            'user_id': o1.user_id,
                                            's_id': o1.s_id,
                                            'iob_id': o1.iob_id
                                        },

                                        'user2': {
                                            'user_id': o2.user_id,
                                            's_id': o2.s_id,
                                            'iob_id': o2.iob_id
                                        },

                                        'same_species': (o1.s_id == o2.s_id),
                                        'distance': math.sqrt(o1.point_proximity(o2)),
                                        'percent': o1.area_overlap(o2)
                                    })

                        if not matched:
                            not_matched[o1.iob_id] = {
                                    'user_id': o1.user_id,
                                    's_id': o1.s_id,
                                    'iob_id': o1.iob_id
                            }

                # store the non-matched values for later calcs
                results[p_id][i_id]['not_matched'] = not_matched

                # store the count for this image
                i_missing = len(not_matched)
                results[p_id][i_id]['missing'] = i_missing
                p_missing = p_missing + i_missing

                results[p_id][i_id]['count'] = i_count
                p_count = p_count + i_count

                results[p_id][i_id]['matches'] = i_matches
                p_matches = p_matches + i_matches

            # store the count for this project
            results[p_id]['matches'] = p_matches
            results[p_id]['missing'] = p_missing
            results[p_id]['count'] = p_count

        # save the results
        fname = os.path.join(self.out_dir, '{}.json'.format(fileName))
        f = open(fname, 'w')
        json.dump(results, f)
        f.close()

    def point_test(self, distance):
        """Runs a pointwise test for a given max distance."""
        distance = int(distance)
        self.test(
                fileName=os.path.join(self.out_dir, 'point_{}'.format(distance)),
                comparisonMethod='point_proximity',
                comparisonValue=(distance*distance),
                comparisonType=-1
        )

    def area_test(self, percent):
        """Runs an area test for a given percentage."""
        percent = int(percent)
        self.test(
                fileName=os.path.join(self.out_dir, 'area_{}'.format(percent)),
                comparisonMethod='area_overlap',
                comparisonValue=(float(percent) / 100.0),
                comparisonType=1
        )
