#!/usr/bin/env python

"""
This program goes through our database created via jxlparser.py and splits the
images into multiple images, storing them in our database based on
image_splitter.sql.
"""

import os, sys
import datetime
import image_slicer
import MySQLdb as mysql

skipped = 0
added = 0

class Image:
	def __init__(self, imageId, directory, name, width, height):
		self.imageId = imageId
		self.directory = directory
		self.name = name
		self.width = width
		self.height = height
		self.filename = os.path.join(directory, name)

class SplitImage:
	def __init__(self, name, top, left, width, height):
		self.name = name
		self.top = top
		self.left = left
		self.width = width
		self.height = height

def split_and_save_images(image, prefix, directory, split):
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
		return None

	# start our storage structure
	split_images = []

	# go through and create the images for return and save
	for tile in tiles:
		# create the split image
		split_image = SplitImage(
			name='{}{}.jpg'.format(prefix, tile.number),
			top=tile.coords[1],
			left=tile.coords[0],
			width=tile.image.size[0],
			height=tile.image.size[1]
		)

		# save and append to our array
		#print "\tSaving image: {}".format(os.path.join(directory, split_image.name))
		try:
			tile.image.save(
				os.path.join(directory, split_image.name),
				'jpeg'
			)
			split_images.append(split_image)
		except:
			print "\tError saving image!"
			print "\t", sys.exc_info()[0]

	# return the split images array
	return split_images

def split_image_to_db(image, prefix, cnx, directory, split):
	"""Splits an image into multiple images and saves the to the given
	directory and stores their metadata in the database.
	"""

	global skipped, added

	try:
		addSplitImage = (
			"INSERT INTO tblSplitImages "
			"(`imageId`, `name`, `top`, `left`, `width`, `height`) "
			"VALUES ({}, '{}', {}, {}, {}, {})"
		)

		# make sure it doesn't exist yet
		cursor = cnx.cursor()
		cursor.execute(
			"SELECT imageId FROM tblSplitImages "
			"WHERE imageId={}".format(image.imageId)
		)

		if cursor.fetchone():
			skipped = skipped + 1
			print "Skipping already submitted image: {}".format(image.imageId)
			cursor.close()
			return True

		# split and save the files
		tiles = split_and_save_images(image, prefix, directory, split)
		if not tiles:
			print "No tiles created"
			return False
		success = True

		# prepare each tile insertion
		count = 0
		for tile in tiles:
			statement = addSplitImage.format(
				image.imageId,
				tile.name,
				tile.top,
				tile.left,
				tile.width,
				tile.height
			)
			#print '\t{}'.format(statement)
			cursor.execute(statement)
			count = count + 1

		# save the changes
		cnx.commit()
		print 'Added {} split images.'.format(count)
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
			"SELECT f.flightId, i.imageId, i.name, i.img_height, i.img_width, f.directory "
			"FROM tblFlights AS f "
			"JOIN tblImages AS i "
			"ON i.flightId = f.flightId"
		)
		
		# go through all the images and split them
		row = cursor.fetchone()
		while row:
			(flightId, imageId, name, img_height, img_width, flightDirectory) = row
			image = Image(
				imageId=imageId,
				directory=flightDirectory,
				name=name,
				width=img_width,
				height=img_height
			)

			success = success and split_image_to_db(
				image=image,
				prefix='{}_{}_'.format(flightId, imageId),
				cnx=cnx2,
				directory=directory,
				split=split
			)
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
		description='Parse a JXL file for storage in a database.'
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
	argparser.add_argument('--split', type=int, help='Amount to split images into', default=25)
	args = argparser.parse_args()

	split_all_images_to_db(
		host=args.host,
		database=args.database,
		username=args.username,
		password=args.password,
		directory=args.directory,
		split=args.split
	)