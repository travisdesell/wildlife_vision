#!/usr/bin/env python

"""
This program goes through our database created via jxlparser.py and splits the
images into multiple images, storing them in our database based on
image_splitter.sql.
"""

import os
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
	# split the image without saving
	tiles = image_slicer.slice(image.filename, split, save=False)

	# start our storage structure
	split_images = []
	width = int(image.width / sqrt(split))
	height = int(image.height / sqrt(height))

	# go through and create the images for return and save
	for tile in tiles:
		# create the split image
		split_image = SplitImage(
			prefix + '{%d}.png'.format(tile.number),
			(tile.row() - 1) * height,
			(tile.col() - 1) * width,
			width,
			height
		)

		# save and append to our array
		tile.save(
			filename=os.path.join(directory, split_image.name),
			prefix='jpg'
		)

		split_images.append(split_image)

	# return the split images array
	return split_images

def split_image_to_db(image, prefix, cnx, directory, split):
	"""Splits an image into multiple images and saves the to the given
	directory and stores their metadata in the database.
	"""

	tiles = split_and_save_images(image, prefix, directory, split)
	success = True

	try:
		addSplitImage = (
			"INSERT INTO tblSplitImages "
			"(imageId, name, top, left, width, height) "
			"VALUES ('{}', '{}', '{}', '{}', '{}', '{}')"
		)

		# make sure it doesn't exist yet
		cursor = cnx.cursor()
		cursor.execute(
			"SELECT imageId FROM tblSplitImages "
			"WHERE imageId={}".format(image.imageId)
		)

		if cursor.fetchone():
			skipped = skipped + 1
			return True

		# prepare each tile insertion
		count = 0
		for tile in tiles:
			cursor.execute(addSplitImage.format(
				image.imageId,
				tile.name,
				tile.top,
				tile.left,
				tile.width,
				tile.height
			))
			count = count + 1

		# save the changes
		cnx.commit()
		print 'Added {} split images.'.format(count)
		added = added + 1
	except:
		print 'Error submitting split images to the database.'
		success = False
		cnx.rollback()
	finally:
		cursor.close()

	return success

def split_all_images_to_db(host, database, username, password, directory, split):
	"""Splits all the images (that haven't been split) and stores
	the saved split images to the database and directory."""

	try:
		# connect to the database
		cnx = mysql.connect(
			host=host,
			user=username,
			passwd=password,
	        db=database
	    )
	except:
		# print out any errors
	  	print "Error connecting to the DB"
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
				image,
				flightId,
				cnx,
				directory,
				split
			)

		print 'Added {} split images.'.format(added)
	except:
		# print out any errors
		print "Error submitting to database"
		success = False
	finally:
		# close the cursor and connection
		cursor.close()
		cnx.close()

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