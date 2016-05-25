#!/usr/bin/env python

import os
import datetime
import MySQLdb as mysql

def internal_save_db(cursor, statement, fname):
    """Saves the internal command to the db"""
    rows = 0

    f = open(fname, 'w')
    f.write('project_id,image_id,image_observation_id,image_observation_box_id,user_id,archive_filename,x,y,width,height,species_id')

    cursor.execute(statement)
    row = cursor.fetchone()
    while row:
        (p_id, i_id, io_id, iob_id, user_id, archive_filename, x, y, width, height, s_id, watermarked_filename) = row
        if watermarked_filename:
            archive_filename = watermarked_filename
        f.write('\n{},{},{},{},{},{},{},{},{},{},{}'.format(p_id,i_id, io_id, iob_id, user_id, archive_filename, x, y, width, height, s_id))
        rows = rows + 1
        row = cursor.fetchone()

    f.close()
    return rows

def save_db(host, database, username, password, fname):
    """Saves the currrent state of the database."""

    select = (
        "SELECT i.project_id, i.id, io.id, iob.id, io.user_id, i.archive_filename, iob.x, iob.y, iob.width, iob.height, iob.species_id, i.watermarked_filename "
        "FROM image_observations as io "
            "INNER JOIN images as i ON i.id = io.image_id "
            "INNER JOIN image_observation_boxes as iob ON iob.image_observation_id = io.id "
        "WHERE "
            "io.nothing_here = 0"
    )

    select_single = "{} AND i.views = 1".format(select)
    select_multiple = "{} AND i.views > 1".format(select)

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
    singles = 0
    multiples = 0
    try:
        singles = internal_save_db(cursor, select_single, '{}_single.txt'.format(fname))
        multiples = internal_save_db(cursor, select_multiple, '{}_multiple.txt'.format(fname))
    except:
        # print out any errors
        print "Error reading from the DB"
        print "\t", sys.exc_info()[0]
        return False
    finally:
		# close the cursor and connection
		cursor.close()
		cnx.close()

    return singles + multiples
