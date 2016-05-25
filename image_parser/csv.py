#!/usr/bin/env python

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Creates the CSV files for representation and analysis'
    )
    argparser.add_argument('masterfile', type=argparse.FileType('r'), help='Master JSON file with the real data')
    argparser.add_argument('fs', type=argparse.FileType('r'), help='Filename(s) for comparing', nargs='+')
    argparser.add_argument('--out_dir', type=str, default='', help='Output directory (if different than the masterfile directory')
    args = argparser.parse_args()

    if args.out_dir:
        out_dir = args.out_dir
    else:
        out_dir = None
    print 'Output directory: {}\n\n'.format(out_dir)

    from image_parser.csv import create_csvs
    create_csvs(
            master=args.masterfile,
            fs=args.fs,
            out_dir=out_dir
    )
