#!/usr/bin/env python

from xml.etree.ElementTree import XMLParser
import argparse

class ParseJXL:
	depth = 0
	parent_tags = {}
	types = {}
	current_data = 0

	"""Called when each tag is opened."""
	def start(self, tag, attrib):
		# see if we already have this tag for its parent
		if self.depth > 0 and tag in self.types[self.parent_tags[self.depth - 1]]:
			self.depth += 1
			return

		# store the parent and initialize an empty dictionary for this tag
		self.parent_tags[self.depth] = tag
		self.types[tag] = []

		# print this new tag and register with parent
		if self.depth > 0:
			self.types[self.parent_tags[self.depth-1]].append(tag)
			print "  " * (self.depth-1),
		print tag,

		if len(attrib) > 0:
			i = len(attrib)
			print "{",
			for key in attrib.iterkeys():
				print key,
				i -= 1
				if i > 0:
					print ",",
			print "}",

		print ""
		self.depth += 1
		self.current_data = 0
		

	"""Called when each tag is closed."""
	def end(self, tag):
		self.depth -= 1

	"""Called for the data for each tag."""
	def data(self, data):
		if len(data.strip()) > 0 and self.current_data == 0:
			print "  " * (self.depth-1), "[", data.strip(), "]"
			self.current_data += 1
		pass

	"""Called at the end of the XML file."""
	def close(self):
		pass

target = ParseJXL()
parser = XMLParser(target=target)

# determine our filename
argparser = argparse.ArgumentParser(description='Print the structure of a JXL file.')
argparser.add_argument('filename', type=str, help='JXL file to parse')
args = argparser.parse_args()

print "Parsing file:", args.filename
print ""

try:
	xml = open(args.filename)
	parser.feed(xml.read())
	parser.close()
except:
	print "Error opening or reading file."