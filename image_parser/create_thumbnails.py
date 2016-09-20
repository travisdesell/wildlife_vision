#!/usr/bin/env python

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Extracts thumbnails'
    )
    argparser.add_argument('f', type=argparse.FileType('r'), help='Locations json file')
    argparser.add_argument('project', type=int, help='Project ID')
    argparser.add_argument('width', type=int, help='Width of the thumbnail')
    argparser.add_argument('height', type=int, help='Height of the thumbnail')
    argparser.add_argument('outdir', type=str, help='Output directory')
    args = argparser.parse_args()

    from image_parser.create_thumbnails import create_thumbnails
    create_thumbnails(f=args.f, project=args.project, width=args.width, height=args.height, out_dir=args.outdir)
