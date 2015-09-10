#!/usr/bin/env python

"""
This program parses a JXL file created by Trimble software and stores the data
in a given database.
"""

import xml.etree.ElementTree as XMLParser

class JXLFlight:
	"""JXLFlight stores all metadata information about a particular flight in
	the JXL file.

	This information includes timestamp, name, directory, and location extents.
	"""

	def __init__(self, timestamp='', name='', directory='', latitudeN=0.0,
			latitudeS=0.0, longitudeE=0.0, longitudeW=0.0):
		self.timestamp = timestamp
		self.name = name
		self.directory = directory
		self.latitudeN = float(latitudeN)
		self.latitudeS = float(latitudeS)
		self.longitudeE = float(longitudeE)
		self.longitudeW = float(longitudeW)

	def __str__(self):
		"""Return a string representation of this object."""

		return 'JXLFlight {} at {} in {}: (N {}, S {}) x (W {}, E {})'.format(
				self.name,
				self.timestamp,
				self.directory,
				self.latitudeN, self.latitudeS,
				self.longitudeW, self.longitudeE
			)

	def __repr__(self):
		"""Return a string representation of this object."""

		return self.__str__()

	def __unicode__(self):
		"""Return a unicode representation of this object."""

		return u'%s' % self.__str__()

class JXLImage:
	"""JXLImage stores all metadata information about a particular image in
	the JXL file.

	This information includes a timestamp, filename, location, height,
	yaw/pitch/roll, and image height and width.

	Flight information is also stored as a JXLFlight object.
	"""
	
	def __init__(self, timestamp='', filename='', latitude=0.0, longitude=0.0,
			height=0.0, img_width=0, img_height=0, yaw=0.0, pitch=0.0,
			roll=0.0, flight=None):
		self.timestamp = timestamp
		self.filename = filename
		self.latitude = float(latitude)
		self.longitude = float(longitude)
		self.height = float(height)
		self.img_width = int(img_width)
		self.img_height = int(img_height)
		self.yaw = float(yaw)
		self.pitch = float(pitch)
		self.roll = float(roll)
		self.flight = flight

	def __str__(self):
		"""Return a string representation of this object."""

		return 'JXLImage {} at {} from {}: ({}, {}, {}), {}x{}, [{}, {}, {}]'.format(
				self.filename,
				self.timestamp,
				self.flight.name,
				self.latitude, self.longitude, self.height,
				self.img_width, self.img_height,
				self.yaw, self.pitch, self.roll
			)

	def __repr__(self):
		"""Return a string representation of this object."""

		return self.__str__()

	def __unicode__(self):
		"""Return a unicode representation of this object."""

		return u'%s' % self.__str__()

def parse(filename):
	"""Parse images from a given JXL file and return a dictionary with all
	JXLImages.
	"""

	print "Parsing file:", filename
	print ""

	# open the XML file for parsing
	tree = XMLParser.parse(filename)
	root = tree.getroot()

	# dictionary to hold our parsed images
	images = {}

	# hold our flight information for future
	flight = JXLFlight()

	# grab all the information from ImageRecord, storing in our dictionary by
	# FileName
	for ImageRecord in root.iter('ImageRecord'):
		image = JXLImage()

		image.timestamp = ImageRecord.attrib['TimeStamp']
		image.filename = ImageRecord.find('FileName').text
		image.img_width = int(ImageRecord.find('Width').text)
		image.img_height = int(ImageRecord.find('Height').text)

		images[image.filename.split('.')[0]] = image

	# grab location data from PointRecord corresponding to Name = FileName
	firstPointRecord = True
	for PointRecord in root.iter('PointRecord'):
		image = images[PointRecord.find('Name').text]
		wgs = PointRecord.find('WGS84')

		image.latitude = float(wgs.find('Latitude').text)
		image.longitude = float(wgs.find('Longitude').text)
		image.height = float(wgs.find('Height').text)

		# is this our first image?
		if firstPointRecord:
			flight.latitudeN = image.latitude
			flight.latitudeS = image.latitude
			flight.longitudeE = image.longitude
			flight.longitudeW = image.longitude
			firstPointRecord = False

		# use the lat/long information to update our JXLFlight extents
		if image.latitude > flight.latitudeN:
			flight.latitudeN = image.latitude
		if image.latitude < flight.latitudeS:
			flight.latitudeS = image.latitude
		if image.longitude < flight.longitudeE:
			flight.longitudeE = image.longitude
		if image.longitude > flight.longitudeW:
			flight.longitudeW = image.longitude
			

	# grab orientation data from PhotoStationRecord corresponding to
	# StationName = FileName
	for PhotoStationRecord in root.iter('PhotoStationRecord'):
		image = images[PhotoStationRecord.find('StationName').text]
		DeviceAxisOrientationData = PhotoStationRecord.find(
			'DeviceAxisOrientationData'
		)
		DeviceAxisOrientation = DeviceAxisOrientationData.find(
			'DeviceAxisOrientation'
		)
		BiVector = DeviceAxisOrientation.find('BiVector')

		image.roll = float(BiVector.find('XX').text)
		image.pitch = float(BiVector.find('YY').text)
		image.yaw = float(BiVector.find('ZZ').text)

	# grab flight mission data for all images in this file (one instance)
	FlightMissionRecord = root[0].find('FlightMissionRecord')
	flight.timestamp = FlightMissionRecord.attrib['TimeStamp']
	flight.name = FlightMissionRecord.find('Name').text

	# pull the directory from the JXL file location information
	import os
	flight.directory = os.path.dirname(os.path.abspath(filename))

	# apply the flight mission name to all images
	for key in images:
		images[key].flight = flight

	# return our images
	return images

def save_images_to_db(images, flight, host, database, username, password):
	"""Saves an array of images from a flight to the database using the
	credentials provided.
	"""

	import mysql.connector
	from mysql.connector import errorcode

	try:
		# connect to the database
		cnx = mysql.connector.connect(
			host=host,
			user=username,
			password=password,
	        database=database
	    )
	except mysql.connector.Error as err:
		# print out any errors
	  	if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
			print "Something is wrong with your user name or password"
	  	elif err.errno == errorcode.ER_BAD_DB_ERROR:
			print "Database does not exist"
	  	else:
			print err

		# close the connection and return
	  	cnx.close()
	  	return False

	# prepare our cursor
	cursor = cnx.cursor()
	success = True

	try:
		# prepare our flight for insertion
		addFlight = (
			"INSERT INTO tblFlights "
			"(timestamp, name, latitudeN, latitudeS, longitudeE, longitudeW) "
			"VALUES (%s, %s, %f, %f, %f, %f)"
		)

		flightData = (
			flight.timestamp, flight.name,
			flight.latitudeN, flight.latitudeS,
			flight.longitudeE, flight.longitudeW
		)

		# insert our flight
		cursor.execute(addFlight, flightData)
		flightId = cursor.lastrowid

		# prepare our images for insertion
		addImage = (
			"INSERT INTO tblImages "
			"(flightId, timestamp, name, latitude, longitude, height, yaw, "
			"pitch, roll, img_width, img_height) "
			"VALUES (%d, %s, %s, %f, %f, %f, %f, %f, %f, %d, %d)"
		)

		# add all of our images
		for key, image in images.iteritems():
			imageData = (
				flightId,
				image.timestamp,
				image.filename,
				image.latitude, image.longitude, image.height,
				image.yaw, image.pitch, image.roll,
				image.img_width, image.img_height
			)

			cursor.execute(addImage, imageData)

		# commit our changes to the database
		cnx.commit()
	except mysql.connector.Error as err:
		# print out any errors
		print err
		success = False

		# rollback the changes
		cnx.rollback()
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
	argparser.add_argument('filename', type=str, help='JXL file to parse')
	argparser.add_argument('host', type=str, help='Database host address')
	argparser.add_argument('database', type=str, help='Database')
	argparser.add_argument('username', type=str, 
		help='Username for database connection'
	)
	argparser.add_argument('password', type=str,
		help='Password for database connection'
	)
	args = argparser.parse_args()

	images = parse(args.filename)
	save_images_to_db(
		images=images,
		flight=images.itervalues().next().flight,
		host=args.host,
		database=args.database,
		username=args.username,
		password=args.password
	)
