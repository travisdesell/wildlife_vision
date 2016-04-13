#!/usr/bin/env python

"""
This program goes through our database created via jxlparser.py and splits the
images into multiple images, storing them in our database based on
image_splitter.sql.
"""

import os, sys
import datetime
import MySQLdb as mysql

# disable max image size since these are HUGE
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

import image_slicer
skipped = 0
added = 0

class Image:
    def __init__(self, imageId, filename):
        self.imageId = imageId
        self.filename = filename

class SplitImage:
    def __init__(self, name, x, y, width, height, directory, number):
        self.name = name
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.filename = os.path.join(directory, name)
        self.number = number
        self.imageId = 0

def split_and_save_images(image, directory, split):
    print "Slicing image: {}".format(image.filename)

    # split the image without saving
    try:
        tiles = image_slicer.slice(image.filename, split, save=False)
        if not tiles[1].image:
            print "\tError slicing image"
            return None
    except:
        print "\tError slicing image"
        print "\t", sys.exc_info()[0]
        raise

    # start our storage structure
    split_images = []

    # go through and create the images for return and save
    count = 0
    for tile in tiles:
        # create the split image
        split_image = SplitImage(
                name='{}.jpg'.format(tile.number),
                x=tile.coords[0],
                y=tile.coords[1],
                width=tile.image.size[0],
                height=tile.image.size[1],
                directory=directory,
                number=count
        )
        count = count + 1

        # save and append to our array
        #print "\tSaving image: {}".format(os.path.join(directory, split_image.name))
        try:
            tile.image.save(
                    split_image.filename,
                    'jpeg'
                    )
            print "\tImage saved: ", split_image.filename
            split_images.append(split_image)
        except:
            print "\tError saving image!"
            print "\t", sys.exc_info()[0]
            raise

    # return the split images array
    return split_images

def split_image_to_db(image, cnx, directory, split):
    """Splits an image into multiple images and saves the to the given
    directory and stores their metadata in the database.
    """

    global skipped, added

    addImage = (
        "INSERT INTO images "
        "(`datetime`, `archive_filename`, `camera_id`, `species`, `year`, `project_id`) "
        "VALUES ('{}', '{}', '0', 2, 2016, 4)"
    )

    addSplitImage = (
        "INSERT INTO mosaic_split_images "
        "(`mosaic_image_id`, `image_id`, `number`, `x`, `y`, `width`, `height`) "
        "VALUES ({}, {}, {}, {}, {}, {}, {})"
    )

    try:
        # make sure it doesn't exist yet
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT mosaic_image_id from mosaic_split_images "
            "WHERE mosaic_image_id={}".format(image.imageId)
        )

        if cursor.fetchone():
            skipped = skipped + 1
            print "\tSkipping already submitted image: {}".format(image.imageId)
            cursor.close()
            return True

        # see if we can get the splits from the images table but not the mosaic_split_images table
        # split and save the files
        tiles = split_and_save_images(image, directory, split)
        if not tiles:
            print "No tiles created for", image.imageId
            return False
        success = True

        # prepare each tile insertion
        count = 0
        print "\n"
        for tile in tiles:
            # first, add the tiles in to the images database
            now = datetime.datetime.now()
            statement = addImage.format(
                now.strftime("%Y-%m-%d %H:%M:%S"),
                tile.filename
            )

            count = count + 1
            cursor.execute(statement)
            tile.imageId = cursor.lastrowid
            print '\tAdded:', tile.filename

        cnx.commit()
        print 'Added {} split images to the main table.\n'.format(count)
        count = 0

        for tile in tiles:
            # crappy way to do this, but it's the way i'm doing it
            statement = addSplitImage.format(
                image.imageId,
                tile.imageId,
                tile.number,
                tile.x,
                tile.y,
                tile.width,
                tile.height
            )
            print "\t", statement

            cursor.execute(statement)
            count = count + 1
            print '\tAdded:', tile.filename

        # save the changes
        cnx.commit()
        print 'Added {} split images to mosaic table.\n'.format(count)
        added = added + 1
    except:
        print 'Error submitting split images to the database.'
        print "\t", sys.exc_info()[0]
        success = False
        cnx.rollback()
    finally:
        cursor.close()

    return success

def split_all_images_to_db(host, database, username, password, directory, split):
    """Splits all the images (that haven't been split) and stores
    the saved split images to the database and directory."""

    global skipped, added

    try:
        # connect to the database
        cnx = mysql.connect(
            host=host,
            user=username,
            passwd=password,
            db=database
        )

        cnx2 = mysql.connect(
            host=host,
            user=username,
            passwd=password,
            db=database
        )
    except:
        # print out any errors
        print "Error connecting to the DB"
        print "\t", sys.exc_info()[0]
        return False

    cursor = cnx.cursor()
    success = True

    try:
        cursor.execute(
            "SELECT id, filename "
            "FROM mosaic_images"
        )

        # go through all the images and split them
        row = cursor.fetchone()
        while row:
            (imageId, filename) = row

            outdir = os.path.join(directory, 'mosaic_{}'.format(imageId))
            if not os.path.exists(outdir):
                os.makedirs(outdir)

            print "\nSaving split images to:", outdir
            image = Image(
                imageId=imageId,
                filename=filename,
            )

            success = success and split_image_to_db(
                image=image,
                cnx=cnx2,
                directory=outdir,
                split=split
            )

            # next row
            row = cursor.fetchone()

        print 'Split {} images.'.format(added)
    except:
        # print out any errors
        print "Error submitting to database"
        print "\t", sys.exc_info()[0]
        success = False
    finally:
        # close the cursor and connection
        cursor.close()
        cnx2.close()
        cnx.close()

    if skipped:
        print 'Skipped {} images.'.format(skipped)
    return success

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Parse our mosaic table to split.'
    )
    argparser.add_argument('directory', type=str, help='Directory to output files to')
    argparser.add_argument('--host', type=str, help='Database host address', default='localhost')
    argparser.add_argument('--database', type=str, help='Database', default='')
    argparser.add_argument('--username', type=str,
        help='Username for database connection', default=''
    )
    argparser.add_argument('--password', type=str,
        help='Password for database connection', default=''
    )
    argparser.add_argument('--split', type=int, help='Amount to split images into (default: 100)', default=100)
    args = argparser.parse_args()

    split_all_images_to_db(
        host=args.host,
        database=args.database,
        username=args.username,
        password=args.password,
        directory=args.directory,
        split=args.split
    )
