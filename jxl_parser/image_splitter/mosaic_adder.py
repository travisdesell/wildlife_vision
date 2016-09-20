#!/usr/bin/env python

"""
This program goes through our database created via jxlparser.py and splits the
images into multiple images, storing them in our database based on
image_splitter.sql.
"""

import os, sys, glob
import datetime
import image_slicer
import MySQLdb as mysql

skipped = 0
added = 0

def add_mosaics_to_db(host, database, username, password, directory, project_id):
    """Adds all the mosaics in a folder to the database, if they
    haven't already been added."""

    global skipped, added

    try:
		# connect to the database
        print "Connecting to", host, "using", database, "with", username, "//", password, "\n"
        cnx = mysql.connect(
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

    selectStatement = (
        "SELECT id FROM mosaic_images "
        "WHERE filename='{}'"
    )

    addStatement = (
        "INSERT INTO mosaic_images "
        "(`timestamp`, `filename`, `project_id`) "
        "VALUES ('{}', '{}', '{}')"
    )

    # walk the directory
    try:
        for f in glob.iglob(os.path.join(directory, '*.tif')):
            statement = selectStatement.format(f)
            cursor.execute(statement)

            # skip if we've already added
            if cursor.fetchone():
                print "\tSkipped", f
                skipped = skipped + 1
                continue

            now = datetime.datetime.now()
            statement = addStatement.format(now.strftime("%Y-%m-%d %H:%M:%S"), f, project_id)
            cursor.execute(statement)

            cnx.commit()
            print "\tAdded", f
    except:
		# print out any errors
		print "Error submitting to database"
		print "\t", sys.exc_info()[0]
		success = False

    finally:
		# close the cursor and connection
		cursor.close()
		cnx.close()

    if skipped:
		print '\nSkipped {} images.'.format(skipped)
    return success

if __name__ == '__main__':
	import argparse
	argparser = argparse.ArgumentParser(
		description='Adds all mosaics in a directory to the database.'
	)
    argparser.add_argument('project_id', type=int, help='Project ID for the mosaic')
	argparser.add_argument('directory', type=str, help='Directory where the mosaics are')
	argparser.add_argument('--host', type=str, help='Database host address', default='localhost')
	argparser.add_argument('--database', type=str, help='Database', default='')
	argparser.add_argument('--username', type=str,
		help='Username for database connection', default=''
	)
	argparser.add_argument('--password', type=str,
		help='Password for database connection', default=''
	)
	args = argparser.parse_args()

	add_mosaics_to_db(
		host=args.host,
		database=args.database,
		username=args.username,
		password=args.password,
		directory=args.directory,
        project_id=args.project_id
	)
