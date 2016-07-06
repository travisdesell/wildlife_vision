#!/usr/bin/env python

import os, json

def create_csv(f, out_dir=None):
    """Creates a CSV file from a single file."""
    fname = os.path.basename(f.name).split('.')[0]
    if not out_dir:
        out_dir = os.path.dirname(f.name)

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    data = json.load(f)
    for p_id, images in data.iteritems():
        opath = os.path.join(out_dir, p_id)
        if not os.path.exists(opath):
            os.mkdir(opath)

        fmatched = open(
                os.path.join(
                    opath,
                    '{}_{}_matched.csv'.format(p_id, fname)
                ),
                'w'
        )

        funmatched = open(
                os.path.join(
                    opath,
                    '{}_{}_unmatched.csv'.format(p_id, fname)
                ),
                'w'
        )

        try:
            fmatched.write('ImageId,UserId1,UserId2,SpeciesId1,SpeciesId2,SameSpecies,MaxCornerDistance,AreaOverlap\n')
            funmatched.write('ImageId,UserId,SpeciesId\n')

            for i_id, i_data in images.iteritems():
                if not isinstance(i_data, dict) or not 'results' in i_data:
                    continue

                # write each result to the csv
                for result in i_data['results']:
                    fmatched.write('{},{},{},{},{},{},{},{}\n'.format(
                        i_id,
                        result['user_1']['user_id'],
                        result['user_2']['user_id'],
                        result['user_1']['s_id'],
                        result['user_2']['s_id'],
                        result['same_species'],
                        result['distance'],
                        result['percent']
                    ))
        finally:
            fmatched.close()
            funmatched.close()

def match_in_master(p_id, i_id, master_data, user, user2=None):
    """Determines if a given match is in the master."""
    for result in master_data[p_id][i_id]['results']:
        if result['user_1']['iob_id'] == user['iob_id']:
            if not user2 or result['user_2']['iob_id'] == user2['iob_id']:
                return True

        if result['user_2']['iob_id'] == user['iob_id']:
            if not user2 or result['user_1']['iob_id'] == user2['iob_id']:
                return True

    return False


def create_comparison_csv(master, fs, out_dir=None):
    """Creates a comparison CSV file based on the master."""
    if not out_dir:
        out_dir = os.path.dirname(master.name)

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    master_data = json.load(master)
    output = {}

    for f in fs:
        data = json.load(f)
        method = os.path.basename(f.name).split('.')[0]

        for p_id, images in data.iteritems():
            if not p_id in master_data:
                continue

            if not p_id in output:
                output[p_id] = []

            # count the false values
            false_positives = 0
            false_negatives = 0

            for i_id, i_data in images.iteritems():
                if not isinstance(i_data, dict) or not 'results' in i_data:
                    continue

                for result in i_data['results']:
                    matched = match_in_master(
                        p_id=p_id,
                        i_id=i_id,
                        master_data=master_data,
                        user=result['user_1'],
                        user2=result['user_2'],
                    )

                    if not matched:
                        false_positives = false_positives + 1

                if not 'not_matched' in i_data:
                    continue

                for iob_id, not_matched in i_data['not_matched'].iteritems():
                    matched = match_in_master(
                        p_id=p_id,
                        i_id=i_id,
                        master_data=master_data,
                        user=not_matched
                    )

                    if matched:
                        false_negatives = false_negatives + 1

            output[p_id].append((
                method,
                images['count'],
                images['matches'],
                images['missing'],
                images['wrong_species'],
                float(images['matches']) / master_data[p_id]['matches'],
                float(images['missing']) / master_data[p_id]['missing'],
                images['wrong_species'] - master_data[p_id]['wrong_species'],
                false_positives,
                false_negatives
            ))

    for p_id in output:
        fname = os.path.join(out_dir, p_id, '{}_comparison.csv'.format(p_id))
        fout = open(fname, 'w')
        try:
            fout.write('Method,Count,Matched,Missing,WrongSpecies,MatchedRatioVsReal,MissingRatioVsReal,WrongSpeciesDifferenceVsReal,FalsePositives,FalseNegatives\n')

            fout.write('Real,{},{},{},{},1,1,0,0,0\n'.format(
                master_data[p_id]['count'],
                master_data[p_id]['matches'],
                master_data[p_id]['missing'],
                master_data[p_id]['wrong_species']
            ))

            soutput = sorted(output[p_id], key=lambda x: x[0])
            for line in soutput:
                fout.write(','.join(str(x) for x in line))
                fout.write('\n')

        finally:
            fout.close()

def create_csvs(master, fs, out_dir=None):
    """Creates all CSVs"""
    for f in fs:
        create_csv(f=f, out_dir=out_dir)
        f.seek(0, 0)

    create_csv(f=master, out_dir=out_dir)
    master.seek(0, 0)

    create_comparison_csv(master=master, fs=fs, out_dir=out_dir)
