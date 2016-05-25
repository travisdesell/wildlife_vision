#!/usr/bin/env python

if __name__ == '__main__':
    import argparse
    argparser = argparse.ArgumentParser(
        description='Extracts the current state of the database for consistent testing.'
    )
    argparser.add_argument('fname', type=str, help='Base filename to save as with no extension')
    argparser.add_argument('--host', type=str, help='Database host address', default='localhost')
    argparser.add_argument('--database', type=str, help='Database', default='')
    argparser.add_argument('--username', type=str,
        help='Username for database connection', default=''
    )
    argparser.add_argument('--password', type=str,
        help='Password for database connection', default=''
    )
    args = argparser.parse_args()

    from image_parser.instance import save_db
    save_db(
        host=args.host,
        database=args.database,
        username=args.username,
        password=args.password,
        fname=args.fname
    )
