#!/usr/bin/env python

# basic imports
import sys, os, random

# allow for the conversion of datatypes
import struct

# image manipulation
from PIL import Image

# globals
scriptname = sys.argv[0]
obs_size = 18
half_obs_size = 9
species_whitelist = (-1, 2, 1000000)


usage = """
{} outdir imgdir test% background (binfiles...)
====================================================================================
outdir      - the directory to symlink the generated dataset
imgdir      - the directory where the MSI images are stored
test%       - the % of the dataset that should be for testing only (0-100)
background  - the number of background per MSI (5-10)
binfile     - the location binfiles to include
""".format(scriptname)

def load_binfile(binfile):
    """Loads data from a binfile."""
    global species_whitelist

    data = {}
    with open(binfile, 'rb') as fp:
        # get the number of MSIs in the bin file
        msi_count = struct.unpack('I', fp.read(4))[0]

        # get the data for each msi
        for i in range(msi_count):
            msi_id = struct.unpack('I', fp.read(4))[0]
            msi_observations = struct.unpack('I', fp.read(4))[0]

            data[msi_id] = []

            # read in each observation
            for j in range(msi_observations):
                observation = struct.unpack('IIIII', fp.read(20))

                # make sure the species is allows
                if not observation[0] in species_whitelist:
                    continue

                data[msi_id].append({
                    'species_id': observation[0],
                    'x': observation[1],
                    'y': observation[2],
                    'width': observation[3],
                    'height': observation[4]
                })

    return data

def link_msis(imgdir, dstdir, locations):
    for msi_id in locations:
        filename = '{}.png'.format(msi_id)
        src = os.path.join(imgdir, filename)
        dst = os.path.join(dstdir, filename)
        os.symlink(src, dst)

def does_overlap(x, y, width, height, obs):
    """Determines if the given x, y, width, height has an overlap in the observations."""
    for ob in obs:
        if ob['x'] > (x + width) or (ob['x'] + ob['width']) > x:
            continue

        if ob['y'] > (y + height) or (ob['y'] + ob['height']) > y:
            continue

        return True

    return False

def get_random_location(width, height, obs):
    """Gets a random location within bounds."""
    global obs_size

    max_x = width - obs_size - 1
    max_y = height - obs_size - 1
    overlap = True

    while overlap:
        x = random.randint(0, max_x)
        y = random.randint(0, max_y)
        overlap = does_overlap(x, y, obs_size, obs_size, obs)

    return {
        'species_id': -1,
        'x': x,
        'y': y ,
        'width': obs_size,
        'height': obs_size
    }

def generate_background(imgdir, background, locations):
    global obs_size, half_obs_size

    for msi_id, obs in locations.iteritems():
        imgname = '{}.png'.format(msi_id)
        bg_obs = []

        with Image.open(os.path.join(imgdir, imgname)) as img:
            (width, height) = img.size

            # normalize observations
            for ob in obs:
                x = ob['x'] + int(ob['width'] / 2) - half_obs_size
                y = ob['y'] + int(ob['height'] / 2) - half_obs_size

                if (x + obs_size) >= width:
                    x = width - obs_size - 1
                if x < 0:
                    x = 0
                if (y + obs_size) >= height:
                    y = height - obs_size - 1
                if y < 0:
                    y = 0

                ob['x'] = x
                ob['y'] = y
                ob['width'] = obs_size
                ob['heigh'] = obs_size

            for i in range(background):
                newob = get_random_location(width, height, obs)
                obs.append(newob)
                bg_obs.append(newob)

            # switch obs with bg_obs
            del obs[:]
            for ob in bg_obs:
                obs.append(ob)

def generate_idx(filename, species_filename, imgdir, background, bg_locations, locations):
    global obs_size, half_obs_size

    total_obs = 0
    bg_obs = 0
    for msi_id, obs in locations.iteritems():
        # skip any MSIs not in the universal BG set
        if not msi_id in bg_locations:
            continue

        # increment our total obs
        bg_obs = bg_obs + len(bg_locations[msi_id])
        total_obs = total_obs + len(obs)

        imgname = '{}.png'.format(msi_id)
        with Image.open(os.path.join(imgdir, imgname)) as img:
            (width, height) = img.size

    print '\t\t\tUser observations  :', total_obs
    print '\t\t\tBG observations    :', bg_obs
    total_obs = total_obs + bg_obs
    print '\t\t\tTotal observations :', total_obs

    # open our file for writing
    with open(filename, 'wb') as fp, open(species_filename, 'wb') as species_fp:
        # 0x00, 0x02 must be the first 2 bytes
        # 0x08 is for unsigned bytes (chars)
        # 4 is for count, W, H, RGB
        fp.write(struct.pack('>BBBB', 0, 0, 8, 4))
        species_fp.write(struct.pack('>BBBB', 0, 0, 0x0C, 1))

        # count
        fp.write(struct.pack('>I', total_obs))
        species_fp.write(struct.pack('>I', total_obs))

        # width / height
        fp.write(struct.pack('>I', obs_size))
        fp.write(struct.pack('>I', obs_size))

        # rgb
        fp.write(struct.pack('>I', 3))

        # go through and get all our RGB data
        for msi_id, obs in locations.iteritems():
            # skip msis not in the BG list
            if not msi_id in bg_locations:
                continue

            imgname = '{}.png'.format(msi_id)
            with Image.open(os.path.join(imgdir, imgname)) as img:
                (width, height) = img.size

                for ob in (obs + bg_locations[msi_id]):
                    # normalize observations
                    x = ob['x'] + int(ob['width'] / 2) - half_obs_size
                    y = ob['y'] + int(ob['height'] / 2) - half_obs_size

                    if (x + obs_size) >= width:
                        x = width - obs_size - 1
                    if x < 0:
                        x = 0
                    if (y + obs_size) >= height:
                        y = height - obs_size - 1
                    if y < 0:
                        y = 0

                    # write out the species
                    species_fp.write(struct.pack('<i', ob['species_id']))

                    # write out the pixels
                    for xpx in range(x, x + obs_size):
                        for ypx in range(y, y + obs_size):
                            (r, g, b) = img.getpixel((xpx, ypx))[:3]
                            fp.write(struct.pack('<BBB', r, g, b))

if __name__ == '__main__':
    print ''

    if len(sys.argv) < 6:
        print usage
        sys.exit(1)

    error = False
    outdir = os.path.abspath(sys.argv[1])
    imgdir = os.path.abspath(sys.argv[2])
    test_percent = int(sys.argv[3])
    background = int(sys.argv[4])

    if not os.path.isdir(outdir):
        print 'Cannot find output directory:', outdir
        error = True
    if not os.path.isdir(imgdir):
        print 'Cannot find image directory:', imgdir
        error = True
    if test_percent <= 0 or test_percent >= 100:
        print 'Test percent must be between 1 and 99. Given:', test_percent
        error = True
    if background < 5 or background > 10:
        print 'Background per image must be between 5 and 10. Given:', background
        error = True

    binfiles = []
    for binfile in sys.argv[5:]:
        binfile = os.path.abspath(binfile)
        if not os.path.isfile(binfile):
            print 'Cannot find bin file:', binfile
            error = True
        binfiles.append(binfile)

    if error:
        print ''
        print 'ERRORS OCCURRED. EXITING.'
        exit(1)

    print 'Running', scriptname
    print '-------------------------------------------'
    print 'Output directory:  ', outdir
    print 'Image directory:   ', imgdir
    print 'Test percent:      ', test_percent, '%'
    print 'Background per MSI:', background
    print 'Bin files:'

    for binfile in binfiles:
        print '\t', binfile

    # grab all the data for each binfile
    print 'Loading in all binfile data...'
    binfile_locations = []
    for binfile in binfiles:
        print '\tLoading', binfile
        binfile_locations.append(load_binfile(binfile))
        print '\t\tDone.'
    print len(binfile_locations), 'bin files loaded.'

    # get the union of the data
    print 'Determining the union of MSIs...'
    locations = {}
    obscount = 0
    for msi_id in binfile_locations[0]:
        # make sure that the MSI exists in all binfiles
        in_all = True
        for i in range(1, len(binfile_locations)):
            if not msi_id in binfile_locations[i]:
                in_all = False

        # append all observations for this MSI into the binfile
        if in_all:
            locations[msi_id] = []
            for i in range(len(binfile_locations)):
                for obs in binfile_locations[i][msi_id]:
                    locations[msi_id].append(obs)
                    obscount = obscount + 1
    print '\t', len(locations), 'unioned MSIs.'
    print '\t', obscount, 'total observations.'

    # split the data into non-obs and obs
    print 'Splitting the data into obs and non-obs MSIs...'
    nonobs = []
    for msi_id, obs in locations.items():
        if len(obs) == 0:
            nonobs.append(msi_id)
            del locations[msi_id]

    print '\t', len(locations), 'obs MSIs.'
    print '\t', len(nonobs), 'non-obs MSIs.'

    print 'Splitting into testing MSIs...'
    # split into training and testing MSIs
    test_locations = {}
    test_nonobs = []
    for msi_id, obs in locations.items():
        if random.randint(1, 100) <= test_percent:
            test_locations[msi_id] = obs
            del locations[msi_id]

    # probably an easier way to do the non-obs
    for msi_id in nonobs:
        if random.randint(1, 100) <= test_percent:
            test_nonobs.append(msi_id)

    for msi_id in test_nonobs:
        nonobs.remove(msi_id)

    print '\t', len(test_locations), 'testing obs MSIs (', len(test_locations) / float(len(test_locations) + len(locations)), '%)'
    print '\t', len(test_nonobs), 'testing non-obs MSIs (', len(test_nonobs) / float(len(test_nonobs) + len(nonobs)), '%)'

    # symlink the images
    print 'Symlinking images...'

    testdir = os.path.join(outdir, 'testing')
    traindir = os.path.join(outdir, 'training')
    os.makedirs(testdir)
    os.makedirs(traindir)

    print '\tSymlinking training locations'
    link_msis(imgdir, traindir, locations)
    link_msis(imgdir, traindir, nonobs)

    print '\tSymlinking testing locations'
    link_msis(imgdir, testdir, test_locations)
    link_msis(imgdir, testdir, test_nonobs)

    print '\tPreparing unioned locations for background...'
    for msi_id in nonobs:
        locations[msi_id] = []
    for msi_id in test_nonobs:
        test_locations[msi_id] = []
    del nonobs[:]
    del test_nonobs[:]

    print 'Generating background data...'
    generate_background(traindir, background, locations)
    generate_background(testdir, background, test_locations)
    print '\tDone.'

    print 'Generating IDXs...'
    for i in range(len(binfiles)):
        (basename, ext) = os.path.splitext(os.path.basename(binfiles[i]))
        basename = basename.split("_")[-1]
        idx = os.path.join(outdir, '{}.idx'.format(basename))
        speciesidx = os.path.join(outdir, 'species_{}.idx'.format(basename))
        test_idx = os.path.join(outdir, 'test_{}.idx'.format(basename))
        test_speciesidx = os.path.join(outdir, 'test_species_{}.idx'.format(basename))

        print '\t', basename
        print '\t\tTraining IDX         :', idx
        print '\t\tTraining Species IDX :', speciesidx
        print '\t\tTesting IDX          :', test_idx
        print '\t\tTesting Species IDX  :', test_speciesidx

        print '\t\tGenerating training IDXs (this will take a while)...'
        generate_idx(idx, speciesidx, traindir, background, locations, binfile_locations[i])

        print '\t\tGenerating testing IDXs (this will take less of a while)...'
        generate_idx(test_idx, test_speciesidx, testdir, background, test_locations, binfile_locations[i])
    print 'Done.'
