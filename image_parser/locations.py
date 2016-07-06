#!/usr/bin/env python

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Extracts the current state of the database for consistent testing.'
    )
    argparser.add_argument('datafile', type=argparse.FileType('r'), help='Data file for the observations')
    argparser.add_argument('fin', type=argparse.FileType('r'), help='Filename for reading')
    argparser.add_argument('fout', type=argparse.FileType('w'), help='Filename for saving')
    args = argparser.parse_args()

    from image_parser.locations import LocationJson
    r = LocationJson(data_file=args.datafile)
    r.location_file(f=args.fin, fout=args.fout)
