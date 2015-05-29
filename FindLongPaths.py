#! python3

import sys, os, glob, fnmatch, argparse

default_path = 'D:\\CDRip'

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    # Work around UnicodeEncodeErrors when attempting to print to the Windows
    # console using a non-unicode code page.  Replacement for print()
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def parse_args():
    parser = argparse.ArgumentParser(
            description='Find files with long pathnames.',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('path', nargs='*', default=[default_path],
                        help='root of tree to search for long paths')
    parser.add_argument('-l', '--len', type=int, default=250,
                        help='minimum path length to be reported')
    return parser.parse_args()


args = parse_args()
for root in args.path:
    for path, _, files in os.walk(root):
        for file in files:
            p = os.path.join(path, file)
            if len(p) >= args.len:
                uprint('%d %s' % (len(p), p))
