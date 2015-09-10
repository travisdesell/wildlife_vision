#!/usr/bin/env python

"""
This program corrects image directories for further processing by the Tremble
software that creates the JXL files. The software requires the images to be
sequential and in the same directory; however, during some flights the images
were split into 2 folders and rolled over, restarting at 0.

This program takes 2 directories (primary and secondary), and renames the files
in the 2nd directory to maintain sequencing with the 1st directory. No files
are moved, however, so that the naming can be first verified by hand.
"""

import os, sys

def find_last_image_number(dir):
	"""Finds the last image number in a given directory."""

def rename_images_from_number(dir, start):
	"""Renames the images starting with the given number."""

if __name__ == '__main__':
	import argparse
	argparser = argparse.ArgumentParser(
		description='Correct image sequencing in a primary and secondary directory.'
	)
	argparser.add_argument('dir1', type=str, help='Primary directory')
	argparser.add_argument('dir2', type=str, help='Secondary directory')
	argparser.add_argument('--force', type=bool, help='Force this to run', default=False)
	args = argparser.parse_args()

	# convert to absolute paths
	dir1 = os.path.abspath(args.dir1)
	dir2 = os.path.abspath(args.dir2)

	# make sure that the secondary dir is lower than primary
	lastImageNumber = find_last_image_number(dir=dir1)
	if lastImageNumber < find_last_image_number(dir=dir2) and not args.force:
		print 'Primary/Secondary directories appear reversed. Please confirm and try again.'
		print '\tYou can force this program to run with --force'

	# rename the images with the new starting number (+1)	
	rename_images_from_number(dir=dir2, start=lastImageNumber+1)