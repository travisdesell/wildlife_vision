#!/usr/bin/env python

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Extracts the current state of the database for consistent testing.'
    )
    argparser.add_argument('datafile', type=argparse.FileType('r'), help='Data file for the observations')
    argparser.add_argument('fs', type=argparse.FileType('r'), help='Filename(s) for recalculating', nargs='+')
    argparser.add_argument('--out_dir', type=str, default='', help='Output directory (if different than the fname directory')
    args = argparser.parse_args()

    if args.out_dir:
        out_dir = args.out_dir
    else:
        out_dir = None
    print 'Output directory: {}\n\n'.format(out_dir)

    from image_parser.recalculate import RecalculateJson
    r = RecalculateJson(data_file=args.datafile, out_dir=out_dir)
    r.recalculate_files(fs=args.fs)
