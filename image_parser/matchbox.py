#!/usr/bin/env python

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Creates the matchboxes for the images.'
    )
    argparser.add_argument('datafile', type=argparse.FileType('r'), help='CSV datafile representing the DB')
    argparser.add_argument('f', type=argparse.FileType('r'), help='JSON file with the real results')
    argparser.add_argument('--out_dir', type=str, default='', help='Output directory (if different than the masterfile directory')
    args = argparser.parse_args()

    if args.out_dir:
        out_dir = args.out_dir
    else:
        out_dir = None
    print 'Output directory: {}\n\n'.format(out_dir)

    from image_parser.matchbox import MatchBox
    mb = MatchBox(datafile=args.datafile, out_dir=out_dir)
    mb.match(args.f)
