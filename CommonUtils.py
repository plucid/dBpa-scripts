#! python3

# Contains some utility code used by my dBpoweramp FLAC-handling scripts.

import fnmatch
import mutagen.flac
import os
import sys


class Messages:
    """
    Keeps track of all errors and warning associated with a single album or
    disc.
    """
    def __init__(self):
        self.messages = []
        self.errors = 0
        self.warnings = 0

    def __bool__(self):
        return bool(self.messages)

    def __str__(self):
        if not self.messages:
            return ''
        return '  ' + '\n  '.join(self.messages)

    def clear(self):
        self.messages = []

    def error(self, text):
        self.messages.append(text)
        self.errors += 1

    def warn(self, text):
        self.messages.append(text)
        self.warnings += 1

    def note(self, text):
        self.messages.append(text)


class Track(dict):
    """
    Per-track data.  Subclasses a dictionary of the track tags.  Code also
    creates these instance attributes:
    track.file = name of the FLAC file
    track.tagset = set of all tags found
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.tagset = set(self)


class Disc(dict):
    """
    Per-disc data.  Subclasses a dictionary of Tracks, keyed on the int track
    number.  Code also creates these instance attributes:
    disc.tagset = set of all tags used in any of the disc's tracks
    disc.identical = Track object of all tags with identical values across all
        of the disc's tracks
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.tagset = set()


class Album(dict):
    """
    Per-album data.  Subclasses a dictionary of Discs, keyed on the int disc
    number.  Code also creates these instance attributes:
    album.path = the path to the album directory
    album.tagset = set of all tags used in any of the album's tracks
    album.disc_count = number of discs in the album
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.tagset = set()


def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    # Work around UnicodeEncodeErrors when attempting to print to the Windows
    # console using a non-unicode code page.  Replacement for builtin print()
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)


reserved_chars_map = str.maketrans(r'"><?:\/*|', "'\u00bb\u00ab\u00bf;----")


def replace_reserved_chars(filename):
    # When creating a filename from generic text (say, an album title),
    # dBpoweramp will replace any reserved characters with allowed variants.
    # Perform the same mapping here.
    return filename.translate(reserved_chars_map)


def flatten_tag(tag, sep='; '):
    if not isinstance(tag, list):
        return tag
    else:
        return sep.join(tag)


def find_albums(root, pattern='*.flac'):
    # Generator to find album directories.
    # Walk tree under root and yield all dirs that have at least
    # one .flac file in them.
    for path, subdirs, files in sorted(os.walk(root)):
        for file in files:
            if fnmatch.fnmatch(file, pattern):
                yield path
                break


def get_track(album_path, trackfile):
    # Read all the metadata tags from a FLAC file into a Track object.
    # Use mutagen to retrieve the tags.
    path = os.path.join(album_path, trackfile)
    tags = mutagen.flac.Open(path).items()
    track = Track(tags)
    track.file = trackfile
    return track


def check_critical_tag(track, tag, msgs):
    # Check that a critical tag ('discnumber' or 'tracknumber') is present and
    # an int.  Return None if an error is encountered, else the int value
    # of the tag.
    if tag not in track:
        msgs.error("Track '%s' missing the %s tag, ignored" % (track.file, tag))
        return None
    try:
        val = int(flatten_tag(track[tag]))
        if val not in range(1,100):
            msgs.error("Track '%s': %s tag %d is not 1 to 99, ignored" % (track.file, tag, val))
            val = None
    except ValueError:
        msgs.error("Track '%s': %s tag '%s' not a number, ignored" % (track.file, tag, track[tag]))
        val = None
    return val


def get_album(album_path):
    # Retrieve the data for all FLAC track files within an album directory.
    # Returns an Album object, which wraps a dictionary of Disc objects keyed
    # on the disc number.  A Disc object wraps a dictionary of Track objects
    # keyed on the track number.
    #
    # Also returns a list of error messages detected while reading the FLAC
    # files.
    msgs = Messages()
    album = Album()
    album.path = album_path
    for trackfile in [f for f in os.listdir(album_path) if f.endswith('.flac')]:
        track = get_track(album_path, trackfile)
        discnumber = check_critical_tag(track, 'discnumber', msgs)
        if discnumber is None:
            continue
        tracknumber = check_critical_tag(track, 'tracknumber', msgs)
        if tracknumber is None:
            continue
        if discnumber not in album:
            album[discnumber] = Disc({tracknumber: track})
        elif tracknumber not in album[discnumber]:
            album[discnumber][tracknumber] = track
        else:
            msgs.error("Track '%s': same disc/track # as previous track, ignored" % track.file)
            continue
#        if len(album_path) + len(trackfile) + 1 > 260:
#            msgs.error("Path too long: %s" % os.path.join(album_path, trackfile))
    for disc in album.values():
        for track in disc.values():
            disc.tagset |= track.tagset
        album.tagset |= disc.tagset
    return (album, msgs)


def find_common_disc_tags(disc):
    # Determine which tags are present in all tracks of a disc.  Initializes
    # disc.common, a set of the common tags.
    common = None
    for track in disc.values():
        if common is None:
            common = track.tagset.copy()
        else:
            common &= track.tagset
    disc.common = common


def find_common_album_tags(album):
    # Determine which tags are present in all tracks of an album.  Initializes
    # album.common, a set of the common tags.
    common = None
    for disc in album.values():
        find_common_disc_tags(disc)
        if common is None:
            common = disc.common.copy()
        else:
            common &= disc.common
    album.common = common


def find_identical_disc_tags(disc):
    # Determine which tags have identical values across all tracks of a disc.
    # Initializes disc.identical, which is a Track object of identical tags and
    # their values.
    identical = None
    for track in disc.values():
        if identical is None:
            identical = Track(track.copy())
        else:
            for tag in identical.tagset - track.tagset:
                del identical[tag]
            identical.tagset &= track.tagset
            different = set()
            for tag in identical.tagset:
                if identical[tag] != track[tag]:
                    different |= {tag}
                    del identical[tag]
            identical.tagset -= different
    disc.identical = identical


def find_identical_album_tags(album):
    # Determine which tags have identical values across all discs of an album.
    # Initializes album.identical, which is a Track object of identical tags and
    # their values.
    identical = None
    for disc in album.values():
        find_identical_disc_tags(disc)
        if identical is None:
            identical = Track(disc.identical.copy())
        else:
            identical.tagset &= disc.identical.tagset
            different = set()
            for tag in identical.tagset:
                if identical[tag] != disc.identical[tag]:
                    different |= {tag}
                    del identical[tag]
            identical.tagset -= different
    album.identical = identical
