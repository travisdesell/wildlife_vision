#!/usr/bin/env python

"""
This program goes through our database created via jxlparser.py and splits the
images into multiple images, storing them in our database based on
image_splitter.sql.
"""

import os, sys
import datetime
import MySQLdb as mysql
import math

from wand.image import Image

skipped = 0
added = 0

class ImageBase:
    def __init__(self, imageId, filename, project_id):
        self.imageId = imageId
        self.filename = filename
        self.project_id = project_id

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
        self.size = 0

def split_and_save_images(image, directory, max_tile_width, max_tile_height):
    print "Slicing image: {} into with max dimensions {}x{}".format(image.filename, max_tile_width, max_tile_height)

    # split the image without saving
    try:
        tiles = []

        with Image(filename=image.filename) as base_img:
            if base_img.sequence:
                img = base_img.sequence[0]
            else:
                img = base_img

            print img.size

            # get the number of columns and the width of each tile
            cols = int(math.ceil(img.size[0] / float(max_tile_width)))
            tile_width = max_tile_width

            # the last two tiles are special
            if cols > 1:
                last_tiles_width = img.size[0] - (tile_width * (cols - 2))
                last_tiles_width = int(last_tiles_width / 2)
            else:
                last_tiles_width = img.size[0]

            # get the number of rows and the height of each tile
            rows = int(math.ceil(img.size[1] / float(max_tile_height)))
            tile_height = max_tile_height

            # the final two rows is special
            if rows > 1:
                last_tiles_height = img.size[1] - (tile_height * (rows - 2))
                last_tiles_height = int(last_tiles_height / 2)
            else:
                last_tiles_height = img.size[1]

            print img.size[0], 'x', img.size[1], ' => ', rows, 'x', cols

            y_loc = 0
            number = 0
            for y in range(rows):
                if y >= (rows - 2):
                    height = last_tiles_height
                else:
                    height = tile_height

                x_loc = 0
                for x in range(cols):
                    if x >= (cols - 2):
                        width = last_tiles_width
                    else:
                        width = tile_width

                    number = number + 1
                    tile = SplitImage(
                        name='{}.png'.format(number),
                        x=x_loc, y=y_loc,
                        width=width, height=height,
                        directory=directory,
                        number=number
                    )

                    # skip files we already have
                    if os.path.exists(tile.filename):
                        print '\t', tile.filename, 'exists... Skipping.'
                        tiles.append(tile)
                        continue

                    print '\t', tile.filename

                    with img.clone() as i:
                        print '\t\t(', x_loc, ',', y_loc, ') =>', width, 'x', height
                        i.crop(x_loc, y_loc, width=width, height=height)
                        i.format = 'png'
                        i.save(filename=tile.filename)
                        tile.size = os.path.getsize(tile.filename)
                        tiles.append(tile)

                    x_loc = x_loc + width

                y_loc = y_loc + height

            # cleanup our sequence files
            if base_img.sequence:
                for x in range(len(base_img.sequence)):
                    base_img.sequence[x].destroy()

        if not tiles or len(tiles) < (rows * cols):
            print "\tError slicing image"
            return None
    except:
        print "\tError slicing image"
        print "\t", sys.exc_info()[:2]
        raise

    # return the split images array
    return tiles

def split_image_to_db(image, cnx, directory, max_tile_width, max_tile_height):
    """Splits an image into multiple images and saves the to the given
    directory and stores their metadata in the database.
    """

    global skipped, added

    addImage = (
        "INSERT INTO images "
        "(`datetime`, `archive_filename`, `camera_id`, `species`, `year`, `project_id`, `size`) "
        "VALUES ('{}', '{}', '0', 2, 2016, '{}', '{}')"
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
        tiles = split_and_save_images(image, directory, max_tile_width, max_tile_height)
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
                tile.filename,
                image.project_id,
                tile.size
            )

            count = count + 1
            cursor.execute(statement)
            tile.imageId = cursor.lastrowid
            print '\tAdded:', tile.filename

        cnx.commit()
        print 'Added {} split images to the main table.\n'.format(count)
        count = 0

        empty = 0
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

            if tile.size < 100000:
                empty = empty + 1

            cursor.execute(statement)
            count = count + 1
            print '\tAdded:', tile.filename

        # save the changes
        cnx.commit()
        print 'Added {} split images to mosaic table.\n'.format(count)

        # update the mosaic count
        statement = 'UPDATE mosaic_images SET split_count = {}, empty_count = {} WHERE id = {}'.format(len(tiles), empty, image.imageId)
        cursor.execute(statement)
        print 'Updatd the mosaic_images.split_count to {} and empty_count to {}'.format(len(tiles), empty)
        cnx.commit()

        added = added + 1
    except:
        print 'Error submitting split images to the database.'
        print "\t", sys.exc_info()[:2]
        success = False
        cnx.rollback()
    finally:
        cursor.close()

    return success

def split_all_images_to_db(host, database, username, password, directory, max_tile_width, max_tile_height):
    """Splits all the images (that haven't been split) and stores
    the saved split images to the database and directory."""

    global skipped, added

    try:
        print "Connection info: ", username, "@", host, ":", database, "(", password, ")"

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
        print "\t", sys.exc_info()[:2]
        return False

    cursor = cnx.cursor()
    success = True

    try:
        cursor.execute(
            "SELECT id, filename, project_id "
            "FROM mosaic_images"
        )

        # go through all the images and split them
        row = cursor.fetchone()
        while row:
            (imageId, filename, project_id) = row

            outdir = os.path.join(directory, 'mosaic_{}'.format(imageId))
            if not os.path.exists(outdir):
                os.makedirs(outdir)

            print "\nSaving split images to:", outdir
            image = ImageBase(
                imageId=imageId,
                filename=filename,
                project_id=project_id
            )

            success = success and split_image_to_db(
                image=image,
                cnx=cnx2,
                directory=outdir,
                max_tile_width=max_tile_width,
                max_tile_height=max_tile_height
            )

            # next row
            row = cursor.fetchone()

        print 'Split {} images.'.format(added)
    except:
        # print out any errors
        print "Error submitting to database"
        print "\t", sys.exc_info()[:2]
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
    argparser.add_argument('--max_tile_width', type=int, help='Maximum width of each tile (default: 1024)', default=1024)
    argparser.add_argument('--max_tile_height', type=int, help='Maximum height of each tile (default: 768)', default=768)
    args = argparser.parse_args()

    split_all_images_to_db(
        host=args.host,
        database=args.database,
        username=args.username,
        password=args.password,
        directory=args.directory,
        max_tile_width=args.max_tile_width,
        max_tile_height=args.max_tile_height
    )
