#! python3

# TODO: on a -m move, remove empty directories back up to the source path.

"""
Update the location and names of FLAC audio files, as well as any associated
files in the same directory, according to the tags found in the FLAC files.

Usage: RearrangeAudioFiles [-m] <source-root> [<destination-root>]

FLAC files are copied/moved based on the [Profile] and [Compilation] tags:

[Profile]=Classical, [Compilation] not present
    Pathname=Classical\[ComposerSort]\[Album] - [AlbumArtistTerse] ([Date])\
[Profile]=Classical, [Compilation] present
    Pathname=Classical\Compilations\[Album] - [AlbumArtistTerse] ([Date])\
[Profile]=Pop/Rock, by default
    Pathname=[AlbumArtist]\[Album] ([Date])\
[Profile]=Pop/Rock, with command line option -s
    Pathname=[Album Artist Sort]\[Album] ([Date])\

An error is reported for any other value of [Profile], or if any of the tags
mentioned above aren't present and identical across all FLAC files in a
directory.

FLAC files are renamed based on the [Profile] and [DiscTotal] tags:

[Profile]=Classical, [DiscTotal] = 1
    Filename=[TrackNumber] [Title] ([ComposerTerse] - [ArtistTerse])
[Profile]=Classical, [DiscTotal] > 1
    Filename=Disc [DiscNumber] - [TrackNumber] [Title] ([ComposerTerse] - [ArtistTerse])
[Profile]=Pop/Rock, [DiscTotal] = 1
    Filename=[TrackNumber] [Title] ([Artist])
[Profile]=Pop/Rock, [DiscTotal] > 1
    Filename=Disc [DiscNumber] - [TrackNumber] [Title] ([Artist])

An error is reported if [DiscTotal] or [TrackNumber] aren't integers in the
range 1 to 99, any of the other tags mentioned aren't present in all FLAC
files in a directory, or any of the tags mentioned other than [Title], [Artist],
[ArtistTerse], [DiscNumber], or [TrackNumber] aren't identical across all FLAC
files in the directory.

The cuesheet and audio extraction log files are renamed based on [DiscTotal]:

[DiscTotal] = 1
    Filename=[AlbumArtist] - [Album].{txt,cue}
[DiscTotal] > 1
    Filename=[AlbumArtist] - [Album] (Disc [DiscNumber]).{txt,cue}

Note: any errors detected as mentioned above will cancel any modifications made
to the source directory files.

If the script is just passed the <source-root>, then files are renamed in
place.  If a <destination-root> is also given, the files are also moved
to a new directory under <destination-root>.  In addition, any files not
renamed as above will also be moved to the destination.

For safety, <source-root> and <destination-root> must be different.  Also for
safety, by default files are actually copied to a new destination, not moved.
This can be overridden with the --move (-m) option.
"""

import argparse
from collections import OrderedDict
import fnmatch
import mutagen.flac
import os
import re
import shutil
import sys

from CommonUtils import *
from CommonUtils import uprint as print

default_maxpath = 259

known_profiles = ('Classical', 'Pop/Rock')

prog = sys.argv[0]
args = None
msgs = None


class Error(Exception):
    # We need the equivalent of a DOS 'pause' before exiting the script, so
    # use a private exception whenever we need to exit early.
    pass


def parse_args():
    global args, prog
    parser = argparse.ArgumentParser(description='''
            Rename and copy/move FLAC files and associated files according to
            the tags in those FLAC files.''')
    parser.add_argument('source', help='Root of tree with files to process')
    parser.add_argument('dest', nargs='?',
                        help='Root of tree to which files are moved/copied. '
                             'If omitted, then files are renamed in place as '
                             'necessary and not copied/moved to a new location')
    parser.add_argument('-l', '--len', type=int, default=default_maxpath, metavar='max',
                        help="Truncate generated pathnames that exceed 'max' "
                             "characters (default %d)" % default_maxpath)
    parser.add_argument('-m', '--move', action='store_true',
                        help='Move files to the destination instead of copying')
    parser.add_argument('-n', '--dry-run', action='store_true',
                        help="Don't actually move/copy/rename, just show what "
                             "would be done (implies -vv)")
    parser.add_argument('-o', '--override', action='append', nargs=2,
                        metavar=('tag', 'value'),
                        help="Override a tag by marking it as identical across "
                             "an album, with the given new value. Useful for "
                             "overriding the values which are used to create "
                             "the path to an album's new location. Separate "
                             "multiple values for a tag with semicolons. "
                             'Example: -o artist "John Doe;Jane Smith"')
    parser.add_argument('-p', '--pause', action='store_true',
                        help='Pause before exiting')
    parser.add_argument('-s', '--sorted-artist', action='store_true',
                        help="For non-classical albums, use the [Album Artist Sort] "
                             "tag, not [AlbumArtist], for the top-level directory "
                             "under which albums are written.")
    parser.add_argument('-t', '--truncate-warn', action='store_false',
                        help='Disable the warning if a file needs to be truncated')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Output more info about what's being done. Repeated"
                             "uses (-vv) will display even more info.")
    args = parser.parse_args()
    prog = parser.prog
    if not os.path.exists(args.source):
        raise Error('source path does not exist')
    args.source = os.path.abspath(args.source)
    if args.dest:
        args.dest = os.path.abspath(args.dest)
            raise Error('source and destination arguments must be different')
    if args.dry_run:
        args.verbose = 2
        print('Note: This is a dry run; no changes are being made')


def process_tag_overrides(album):
    # Handle the -o cmdline option, overriding the values of tags in
    # album.identical.
    if args.override:
        for override in args.override:
            album.identical[override[0]] = override[1].split(';')


def check_tag_validity(album):
    # Make sure all necessary tags are available for the desired rename/
    # move/copy operation.
    def test_identical(tags):
        for tag in tags:
            if tag not in album.common:
                msgs.error("Tag '%s' is not present in all tracks" % tag)
            elif tag not in album.identical:
                msgs.error("Tag '%s' is not identical across all tracks" % tag)

    def test_identical_or_missing(tags):
        for tag in tags:
            if tag in album.tagset and tag not in album.identical:
                msgs.error("Tag '%s' is not identical across all tracks" % tag)

    def test_common(tags):
        for tag in tags:
            if tag not in album.common:
                msgs.error("Tag '%s' is not present in all tracks" % tag)

    if 'profile' not in album.identical:
        msgs.error("Tag 'profile' is not identical across all tracks, "
                    "aborting further tests")
        return
    profile = flatten_tag(album.identical['profile'])
    if profile not in known_profiles:
        msgs.error("Profile '%s' is not known, aborting further tests" % profile)
        return
    album.classical = (profile == 'Classical')
    test_identical(('disctotal', 'album', 'albumartist'))
    test_common(('tracknumber', 'title', 'discnumber'))
    if album.classical:
        album.compilation = ('compilation' in album.tagset)
        test_common(('composerterse', 'artistterse'))
        if args.dest:
            test_identical(('albumartistterse', 'date'))
            test_identical_or_missing(('compilation',))
            if not album.compilation:
                test_identical(('composersort',))
    else:
        test_common(('artist',))
        if args.dest:
            test_identical(('date',))
        if args.sorted_artist:
            test_identical(('album artist sort',))


def get_new_path(album):
    # If moving/copying files to a new destination, determine the path to
    # the new location for an album.
    assert args.dest
    if album.classical:
        dirs = ['Classical']
        if album.compilation:
            dirs.append('Compilations')
        else:
            dirs.append(album.identical['composersort'][0])
    elif args.sorted_artist:
        dirs = [album.identical['album artist sort'][0]]
    else:
        dirs = [album.identical['albumartist'][0]]
    name = album.identical['album'][0]
    if album.classical:
        name += ' - %s' % album.identical['albumartistterse'][0]
    name += ' (%s)' % album.identical['date'][0]
    dirs.append(name)
    return os.path.join(args.dest, *[replace_reserved_chars(d) for d in dirs])


def get_new_audio_file_name(album, discnum, tracknum, track):
    name = '%02d %s' % (tracknum, track['title'][0])
    if track['disctotal'][0] != '1':
        name = ('Disc %d - ' % discnum) + name
    if album.classical:
        name += ' (%s - %s)' % (track['composerterse'][0], track['artistterse'][0])
    else:
        name += ' (%s)' % track['artist'][0]
    name += '.flac'
    return replace_reserved_chars(name)


def get_new_auxiliary_file_basename(discnum, disc):
    name = '%s - %s' % (disc.identical['albumartist'][0],
                        disc.identical['album'][0])
    if disc.identical['disctotal'][0] != '1':
        name += ' (Disc %d)' % discnum
    return replace_reserved_chars(name)


def record_file_to_process(album, old_name, new_name):
    # Record the 2-way mapping between old album file and new, after first
    # running some checks.  If the full new pathname is too long, try to
    # truncate it, with an error if that's not possible.
    path = album.new_path if args.dest else album.path
    new_fullpath = os.path.join(path, new_name)
    if len(new_fullpath) > args.len:
        base, ext = os.path.splitext(new_name)
        shrink = len(new_fullpath) - args.len + len('..')
        if len(base) - shrink < 10:
            # Error if truncating the name won't retain at least
            # 10 characters from the original base filename.
            msgs.error('New filename is too short to truncate to keep pathname'
                        ' in limits')
            msgs.error('  %s' % new_fullpath)
        else:
            truncated_name = base[:-shrink] + '..' + ext
            if args.truncate_warn:
                msgs.warn('New filename will be truncated')
                msgs.warn('  from: %s' % new_name)
                msgs.warn('  to:   %s' % truncated_name)
            new_name = truncated_name
            new_fullpath = os.path.join(path, new_name)
    if new_name in album.new_files:
        prev_old_name = album.new_files[new_name]
        msgs.error('Two files will be renamed to the same new name:')
        msgs.error('  %s' % prev_old_name)
        msgs.error('  %s' % old_name)
        msgs.error('  -> %s' % new_name)
    if args.dest:
        new_fullpath = os.path.join(album.new_path, new_name)
        if os.path.exists(new_fullpath):
            msgs.error('New file already exists in new directory:')
            msgs.error('  %s' % old_name)
            msgs.error('  -> %s' % new_fullpath)
    album.old_files[old_name] = new_name
    album.new_files[new_name] = old_name


def check_and_prepare_audio_files(album):
    # Make sure all the track files can be successfully renamed and
    # moved or copied.
    for discnum, disc in album.items():
        for tracknum, track in disc.items():
            new_name = get_new_audio_file_name(album, discnum, tracknum, track)
            record_file_to_process(album, track.file, new_name)


def check_aux_file(album, fname, attrib, ext):
    match = re.search(r'\(Disc (\d+)\)%s$' % ext, fname)
    if match:
        discnum = int(match.group(1))
    else:
        discnum = 1
    if discnum not in album:
        msgs.error("Disc %d not found processing %s '%s'" %
                    (discnum, attrib, fname))
        return
    new_name = get_new_auxiliary_file_basename(discnum, album[discnum]) + ext
    record_file_to_process(album, fname, new_name)


def check_and_prepare_auxiliary_files(album):
    # Find the existing cuesheet and extraction log files and make sure they
    # can be successfully renamed and moved or copied.
    for fname in sorted(os.listdir(album.path)):
        if fname.endswith('.cue'):
            check_aux_file(album, fname, 'cuesheet', '.cue')
        if fname.endswith('.txt'):
            with open(os.path.join(album.path, fname), 'rt', encoding='utf_16_le') as f:
                line = f.readline()
            if re.search('dBpoweramp.*Digital Audio Extraction Log', line):
                check_aux_file(album, fname, 'logfile', '.txt')


def prepare_other_files(album):
    # For a move/copy to a new destination, find any other files which need to be
    # transferred in addition to the audio and auxiliary files.  These files will
    # be moved without renaming.
    if args.dest:
        for fname in sorted(os.listdir(album.path)):
            if fname not in album.old_files:
                record_file_to_process(album, fname, fname)


def remove_empty_directories(path, root):
    # Remove empty directories starting at path and working through the
    # parent directories, stopping at the root path.
    while not os.listdir(path) and path != root:
        try:
            if args.verbose > 1:
                print('rmdir %s' % path)
            os.rmdir(path)
        except Exception as e:
            print('Warning: Failed to remove empty directory %s' % path)
            print(e)
            return
        path = os.path.dirname(path)


def do_move_or_copy(album):
    # Perform the actual move/copy when source and destination are specified.
    operation = 'Move' if args.move else 'Copy'
    if args.verbose > 1:
        print('%s to:   %s' % (operation, album.new_path))
    if not args.dry_run and not os.path.exists(album.new_path):
        os.makedirs(album.new_path)
    for old, new in album.old_files.items():
        if args.verbose > 1:
            print('%s %s\n  -> %s' % (operation, old, new))
        if not args.dry_run:
            old_path = os.path.join(album.path, old)
            new_path = os.path.join(album.new_path, new)
            if args.move:
                shutil.move(old_path, new_path)
            else:
                shutil.copy2(old_path, new_path)
    if args.move:
        remove_empty_directories(album.path, args.source)


def do_rename_in_place(album):
    # Perform any file renames needed when no destination is specified.
    found = False
    for old, new in album.old_files.items():
        if old != new:
            found = True
            if args.verbose > 1:
                print('Rename %s\n    -> %s' % (old, new))
            if not args.dry_run:
                old_path = os.path.join(album.path, old)
                new_path = os.path.join(album.path, new)
                os.rename(old_path, new_path)
    if not found and args.verbose > 1:
        print('No files renamed')


def process_album(album_path):
    global msgs
    album, msgs = get_album(album_path)
    if not msgs.errors:
        find_common_album_tags(album)
        find_identical_album_tags(album)
        process_tag_overrides(album)
        check_tag_validity(album)
    if not msgs.errors:
        if args.dest:
            album.new_path = get_new_path(album)
        album.old_files = OrderedDict()
        album.new_files = {}
        check_and_prepare_audio_files(album)
        check_and_prepare_auxiliary_files(album)
        prepare_other_files(album)
    if msgs:
        kind = ('Errors' if not msgs.warnings
                else 'Warnings' if not msgs.errors
                else 'Errors and warnings')
        print('\n%s found in %s\n%s' % (kind, album_path, msgs))
        if msgs.errors:
            return
    if args.verbose:
        print('\nProcessing %s' % album_path)
    if args.dest:
        do_move_or_copy(album)
    else:
        do_rename_in_place(album)
    return


def main():
    try:
        parse_args()
        for album_path in find_albums(args.source):
            process_album(album_path)
    except Error as e:
        print('%s: error: %s' % (prog, e))
        exit_code = 1
    except Exception as e:
        print(e)
        exit_code = 2
    else:
        exit_code = 0
    if args.pause:
        try:
            input('\nPress Enter when ready...')
        except:
            pass
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
