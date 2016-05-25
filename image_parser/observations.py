#!/usr/bin/env python

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Extracts the current state of the database for consistent testing.'
    )
    argparser.add_argument('fname', type=str, help='Base filename of the csv files')
    argparser.add_argument('--out_dir', type=str, default='', help='Output directory (if different than the fname directory')
    args = argparser.parse_args()

    out_dir = args.out_dir
    if not out_dir:
        out_dir = os.path.dirname(args.fname)

    from image_parser.observations import parse_csv
    parse_csvs(
        basename=args.fname,
        out_dir=out_dir
    )
