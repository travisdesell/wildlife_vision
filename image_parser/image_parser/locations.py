import os, json
import math
from . import Observation

class LocationJson:
    def __init__(self, data_file):
        # load in data to recalculate the JSON
        self.data = {}
        self.archive_filenames = {}
        data_file.readline()
        for line in data_file:
            (p_id, i_id, io_id, iob_id, user_id, archive_filename, x, y, width, height, s_id) = [z.strip() for z in line.split(',')]

            self.data[iob_id] = Observation(
                    user_id=user_id,
                    species_id=s_id,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    iob_id=iob_id
            )

            if not io_id in self.archive_filenames:
                self.archive_filenames[i_id] = archive_filename

        print len(self.data)
        print len(self.archive_filenames)

    def location_file(self, f, fout):
        """Createa a location file"""
        results = json.load(f)
        locations = {}

        print 'Parsing file: {}\n'.format(f.name)

        for p_id, images in results.iteritems():
            print '\tProject: {}'.format(p_id)
            locations[p_id] = {}

            # pop the "cursory data" out
            if 'matches' in images:
                images.pop('matches')
            if 'count' in images:
                images.pop('count')
            if 'missing' in images:
                images.pop('missing')
            if 'wrong_species' in images:
                images.pop('wrong_species')

            matches = {}
            for i_id, i_data in images.iteritems():
                print '\t\tImage: {}'.format(i_id)

                for result in i_data['results']:
                    user_1 = result['user_1']
                    user_2 = result['user_2']

                    user_1['x'] = self.data[user_1['iob_id']].x
                    user_1['y'] = self.data[user_1['iob_id']].y
                    user_1['right'] = self.data[user_1['iob_id']].right
                    user_1['bottom'] = self.data[user_1['iob_id']].bottom

                    user_2['x'] = self.data[user_2['iob_id']].x
                    user_2['y'] = self.data[user_2['iob_id']].y
                    user_2['right'] = self.data[user_2['iob_id']].right
                    user_2['bottom'] = self.data[user_2['iob_id']].bottom

                    if not i_id in matches:
                        matches[i_id] = {
                            'filename': self.archive_filenames[i_id],
                            'pairs': []
                        }

                    matches[i_id]['pairs'].append([
                        user_1,
                        user_2
                    ])

            # now go through all the matches and get the locations
            for i_id, match in matches.iteritems():
                match_data = {
                    'filename': match['filename']
                }

                while len(match['pairs']):
                    user_1 = match['pairs'][0][0]
                    user_2 = match['pairs'][0][1]
                    user_3 = None

                    if len(match['pairs']) > 1:
                        matched_indexes = []

                        for x in range(1, len(match['pairs'])):
                            test = match['pairs'][x]
                            if test[0]['iob_id'] == user_1['iob_id'] or \
                                    test[0]['iob_id'] == user_2['iob_id']:

                                if not user_3:
                                    user_3 = test[1]
                                matched_indexes.append(x)

                            if test[1]['iob_id'] == user_1['iob_id'] or \
                                    test[1]['iob_id'] == user_2['iob_id']:

                                if not user_3:
                                    user_3 = test[0]
                                matched_indexes.append(x)

                        if user_3:
                            matched_indexes.reverse()
                            for x in range(len(matched_indexes)):
                                match['pairs'].pop(x)

                    # get the intersect
                    x = user_1['x']
                    right = user_1['right']
                    y = user_1['y']
                    bottom = user_1['bottom']

                    r = user_2['right']
                    b = user_2['bottom']
                    if r < x or b < y:
                        match['pairs'].pop(0)
                        continue

                    if user_2['x'] > x:
                        x = user_2['x']
                    if user_2['y'] > y:
                        y = user_2['y']
                    if r < right:
                        right = r
                    if b < bottom:
                        bottom = b

                    if user_3:
                        r = user_3['right']
                        b = user_3['bottom']
                        if r < x or b < y:
                            match['pairs'].pop(0)
                            continue

                        if user_3['x'] > x:
                            x = user_3['x']
                        if user_3['y'] > y:
                            y = user_3['y']
                        if r < right:
                            right = r
                        if b < bottom:
                            bottom = b

                    # update with the intersect
                    if not user_1['s_id'] in match_data:
                        match_data[user_1['s_id']] = []

                    match_data[user_1['s_id']].append({
                        'x': x,
                        'y': y,
                        'right': right,
                        'bottom': bottom,
                        'center_x': int((x + right) / 2),
                        'center_y': int((y + bottom) / 2)
                    })

                    match['pairs'].pop(0)

                # add to the locations
                locations[p_id][i_id] = match_data

        # save the data
        json.dump(locations, fout)
