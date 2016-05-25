#!/usr/bin/env python

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Extracts the current state of the database for consistent testing.'
    )
    argparser.add_argument('fname', type=str, help='Filename for the multiple user csv file')
    argparser.add_argument('--out_dir', type=str, default='', help='Output directory (if different than the fname directory')
    args = argparser.parse_args()

    import os
    out_dir = args.out_dir
    if not out_dir:
        out_dir = os.path.join(os.path.dirname(args.fname), 'confirmation')
    out_dir = os.path.realpath(out_dir)

    from image_parser.confirm import ConfirmTests
    tester = ConfirmTests(fname=args.fname, out_dir=out_dir)
    tester.test_all()
