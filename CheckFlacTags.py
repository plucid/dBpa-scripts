#! python3

# Check FLAC files for tag consistency.  Used when ripping CDs to make sure
# the resulting files are cleaned up and ready for moving to the master tree
# of audio files.
#
# Can perform the following checks:
#
# * Check that all required tags are present in all FLAC tracks.
# * Check that tags which should be the same across tracks of a single album
#   are in fact the same.
# * Check that tags which should be different across tracks of a single album
#   are in fact different.
# * Check that all tags present are already known to this script.
# * There for tags which have been replaced with newer ones (e.g. prefer Label
#   to Organization).  Check that either old or new versions, but not both,
#   are present.  Optionally warn if the old version is used.
# * Miscellaneous checks for reasonableness - for instance, make sure that the
#   tracks for an album have consecutive track numbers.

import argparse
import collections
from collections import defaultdict
import os
import re
import sys

from CommonUtils import *
from CommonUtils import uprint as print

def enum(*args):
    enums = dict(zip(args, range(len(args))))
    return type('Enum', (), enums)

TagKind = enum('Required', 'ReqClassical', 'Optional', 'Mapped')
TagQual = enum('AllSame', 'DiscSame', 'AllDiff', 'Ignored')

known_tags = {
    # Tag name                Kind                  Qualifier         Multivalued
    'accurateripdiscid':     (TagKind.Required,     TagQual.AllDiff,  False),
    'accurateripresult':     (TagKind.Required,     TagQual.Ignored,  False),
    'album':                 (TagKind.Required,     TagQual.AllSame,  False),
    'album artist sort':     (TagKind.Required,     TagQual.AllSame,  False),
    'albumartist':           (TagKind.Required,     TagQual.AllSame,  False),
    'albumartistterse':      (TagKind.ReqClassical, TagQual.AllSame,  False),
    'artist sort':           (TagKind.Optional,     TagQual.Ignored,  True),
    'artist':                (TagKind.Required,     TagQual.Ignored,  True),
    'artistterse':           (TagKind.ReqClassical, TagQual.Ignored,  False),
    'catalog #':             (TagKind.Optional,     TagQual.Ignored,  False),
    'cddb disc id':          (TagKind.Required,     TagQual.DiscSame, False),
    'cdgap':                 (TagKind.Required,     TagQual.AllDiff,  False),
    'cdindex':               (TagKind.Required,     TagQual.AllDiff,  False),
    'cdtoc':                 (TagKind.Required,     TagQual.DiscSame, False),
    'comment':               (TagKind.Optional,     TagQual.Ignored,  False),
    'compilation':           (TagKind.Optional,     TagQual.AllSame,  False),
    'composer':              (TagKind.Required,     TagQual.Ignored,  True),
    'composersort':          (TagKind.ReqClassical, TagQual.Ignored,  True),
    'composerterse':         (TagKind.ReqClassical, TagQual.Ignored,  False),
    'conductor':             (TagKind.Optional,     TagQual.Ignored,  False),
    'conductorsort':         (TagKind.Optional,     TagQual.Ignored,  False),
    'crc':                   (TagKind.Required,     TagQual.Ignored,  False),
    'date':                  (TagKind.Required,     TagQual.AllSame,  False),
    'description':           (TagKind.Optional,     TagQual.Ignored,  False),
    'discnumber':            (TagKind.Required,     TagQual.DiscSame, False),
    'disctotal':             (TagKind.Required,     TagQual.AllSame,  False),
    'encoded by':            (TagKind.Required,     TagQual.AllSame,  False),
    'encoder':               (TagKind.Required,     TagQual.AllSame,  False),
    'encoder settings':      (TagKind.Required,     TagQual.AllSame,  False),
    'genre':                 (TagKind.Required,     TagQual.DiscSame, False),
    'hdcd':                  (TagKind.Optional,     TagQual.Ignored,  False),
    'instrument':            (TagKind.Optional,     TagQual.Ignored,  False),
    'isrc':                  (TagKind.Optional,     TagQual.Ignored,  False),
    'label':                 (TagKind.Required,     TagQual.AllSame,  False),
    'length':                (TagKind.Required,     TagQual.Ignored,  False),
    'mbid':                  (TagKind.Optional,     TagQual.Ignored,  False),
    'orchestra':             (TagKind.Optional,     TagQual.Ignored,  False),
    'organization':          (TagKind.Mapped,       TagQual.AllSame,  False),
    'performer':             (TagKind.Optional,     TagQual.Ignored,  False),
    'period':                (TagKind.ReqClassical, TagQual.Ignored,  False),
    'pre-emphasis':          (TagKind.Optional,     TagQual.Ignored,  False),
    'profile':               (TagKind.Required,     TagQual.AllSame,  False),
    'rating':                (TagKind.Optional,     TagQual.Ignored,  False),
    'replaygain_album_gain': (TagKind.Required,     TagQual.DiscSame, False),
    'replaygain_album_peak': (TagKind.Required,     TagQual.DiscSame, False),
    'replaygain_track_gain': (TagKind.Required,     TagQual.Ignored,  False),
    'replaygain_track_peak': (TagKind.Required,     TagQual.Ignored,  False),
    'soloists':              (TagKind.Optional,     TagQual.Ignored,  True),
    'soloistssort':          (TagKind.Optional,     TagQual.Ignored,  True),
    'source':                (TagKind.Required,     TagQual.AllSame,  False),
    'style':                 (TagKind.Optional,     TagQual.AllSame,  True),
    'title':                 (TagKind.Required,     TagQual.Ignored,  False),
    'totaldiscs':            (TagKind.Mapped,       TagQual.AllSame,  False),
    'totaltracks':           (TagKind.Mapped,       TagQual.DiscSame, False),
    'tracknumber':           (TagKind.Required,     TagQual.Ignored,  False),
    'tracktotal':            (TagKind.Required,     TagQual.DiscSame, False),
    'upc':                   (TagKind.Required,     TagQual.DiscSame, False),
}

known_tags_set = set(known_tags)

required_tags = {k for k, v in known_tags.items() if v[0] == TagKind.Required}
required_classical_tags = required_tags | {k for k, v in known_tags.items()
                                           if v[0] == TagKind.ReqClassical}
optional_tags = {k for k, v in known_tags.items() if v[0] == TagKind.Optional}

identical_tags_across_discs = {k for k, v in known_tags.items() if v[1] == TagQual.AllSame}
identical_tags_within_disc = {k for k, v in known_tags.items()
                              if v[1] in (TagQual.AllSame, TagQual.DiscSame)}
different_tags = {k for k, v in known_tags.items() if v[1] == TagQual.AllDiff}

allowed_multivalued_tags = {k for k, v in known_tags.items() if v[2]}

mapped_tags = {
    'organization': 'label',
    'totaldiscs':   'disctotal',
    'totaltracks':  'tracktotal',
}

sorted_tags = {
    'artist':      'artist sort',
    'albumartist': 'album artist sort',
    'composer':    'composersort',
    'conductor':   'conductorsort',
    'soloists':    'soloistssort',
}

test_leading_The_tags = ['artist', 'albumartist', 'composer']

default_path = 'D:\\CDRip'

args = None
msgs = None

album_count = 0
disc_count = 0
track_count = 0
warn_count = 0


def parse_args():
    global args
    parser = argparse.ArgumentParser(description='Check FLAC files for tag consistency.')
    parser.add_argument('path', nargs='*', default=[default_path],
                        help='root of the tree to search for albums of FLAC files (default: %s)' % default_path)
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show every album processed, not just ones with issues')
    parser.add_argument('-m', '--missing', action='store_false',
                        help="Don't warn about missing required tags")
    parser.add_argument('-M', '--mapping', action='store_false',
                        help="Don't warn about mapping obsolete tags to newer ones")
    parser.add_argument('-o', '--other', action='store_false',
                        help="Don't warn about missing non-FLAC files")
    parser.add_argument('-p', '--pause', action='store_true',
                        help='Pause before exiting')
    parser.add_argument('-s', '--sort-tag-mismatch', action='store_false',
                        help="Don't warn about mismatches between a tag and the "
                             "sort tag variant (e.g. Artist vs. Artist Sort)")
    parser.add_argument('-S', '--no-sort-tag', action='store_true',
                        help="Warn if a sort tag (e.g. Artist Sort) is missing on all "
                             "tracks of a disc, not just some")
    parser.add_argument('-t', '--tag', action='append',
                        help='Find all tracks with the given tag')
    args = parser.parse_args()
    if args.tag:
        def flatten_args(el):
            if isinstance(el, collections.Iterable) and not isinstance(el, str):
                return [a for b in el for a in flatten_args(b)]
            else:
                return [el]

        tags = flatten_args([_.split(',') for _ in args.tag])
        args.tag = {_.strip().lower() for _ in tags}
    else:
        args.tag = set()


def track_list(tracks, track_count):
    # Format a list of tracks as something like 'Tracks 1, 4-6, 10', with
    # special cases for 'All tracks' and a single track.  The track list
    # should already be sorted on entry.
    if len(tracks) == track_count:
        return 'All tracks'
    if len(tracks) == 1:
        return 'Track %d' % tracks[0]
    grouped = list(zip(tracks, tracks))
    pos = len(grouped)
    while pos > 1:
        pos -= 1
        if grouped[pos][0] == grouped[pos - 1][1] + 1:
            grouped[pos - 1] = (grouped[pos - 1][0], grouped[pos][1])
            grouped.pop(pos)
    return 'Tracks %s' % ', '.join(['%d' % x1 if x1 == x2 else '%d-%d' % (x1, x2)
                                    for x1, x2 in grouped])


def output_dict_of_bad_tracks(track_dict, disc, method=None):
    # Helper for messages which display something like:
    #   All tracks: message1
    #   Track 1: message2
    #   Tracks 4-7: message3
    # track_dict is the dictionary mapping the messages to output as the
    # key to the list of pertinent tracks as the value.
    method = method or msgs.error
    for message, tracks in sorted(track_dict.items(), key=lambda i: i[1]):
        method('  %s: %s' % (track_list(tracks, len(disc)), message))


def check_disc_numbers(album):
    # Check the disc numbers and disctotal tag to find missing discs or tracks
    # with an unreasonable/inconsistent disctotal.
    disctotals = defaultdict(list)
    for discnum, disc in album.items():
        for tracknum, track in disc.items():
            try:
                disctotal = flatten_tag(track['disctotal'])
            except:
                # Tag mapping not yet done, so check old form of tag
                disctotal = flatten_tag(track.get('totaldiscs'))
            try:
                disctotal = int(disctotal)
            except:
                pass
            disctotals[disctotal].append((discnum, tracknum))
    if len(disctotals) != 1:
        msgs.error('Inconsistent values of disctotal:')
        for disctotal in sorted(disctotals):
            msgs.error('  %s: Tracks ' % disctotal +
                        ', '.join(['%d/%d' % x for x in sorted(disctotals[disctotal])]))
        try:
            disc_count = max([x for x in album if isinstance(x, int)])
        except:
            disc_count = 1
    else:
        disc_count = next(iter(disctotals.keys()))
    album.disc_count = disc_count
    disc_set = set(album)
    expected_disc_set = set(range(1, disc_count + 1))
    missing_discs = expected_disc_set - disc_set
    extra_discs = disc_set - expected_disc_set
    if missing_discs:
        msgs.error('Missing Discs: ' + ', '.join(map(str, sorted(missing_discs))))
    if extra_discs:
        msgs.error('Unexpected Discs: ' + ', '.join(map(str, sorted(extra_discs))))


def check_identical_tags_across_discs(album):
    # Check for tags which should be identical across all discs within a multi-disc set.
    # Only checks one track per disc, since check_identical_tags will do a more exhaustive
    # check for tracks within a disc.
    if len(album) == 1:
        return
    mismatches = []
    tag_values = {}
    for tag in identical_tags_across_discs & album.tagset:
        for discnum, disc in album.items():
            if tag not in disc.tagset:
                mismatches.append(tag)
                break
            for tracknum, track in disc.items():
                if tag in track:
                    tag_value = track[tag]
                    break
            else:
                assert False or "Didn't find tag in any track as expected"
            if tag not in tag_values:
                tag_values[tag] = tag_value
            else:
                try:
                    if tag_values[tag] == tag_value:
                        continue
                except:
                    pass
                mismatches.append(tag)
                break
    if mismatches:
        msgs.error('Tags not identical across discs: ' + ', '.join(sorted(mismatches)))


def check_nontag_info(album):
    # Make sure the expected non-FLAC files are found in the album directory.
    # These are
    # * folder.jpg
    # * [AlbumArtist] - [Album] (Disc #).cue    -- (Disc #) only for multi-disc
    # * [AlbumArtist] - [Album] (Disc #).txt    -- (Disc #) only for multi-disc
    if not args.other:
        return

    def check_for_file(filename):
        f = replace_reserved_chars(filename)
        if not os.path.isfile(os.path.join(album.path, f)):
            msgs.error("File '%s' not found" % f)

    def find_tag(tag):
        for disc in album.values():
            for track in disc.values():
                if tag in track:
                    return flatten_tag(track[tag])

    check_for_file('folder.jpg')
    album_artist = find_tag('albumartist')
    album_title = find_tag('album')
    if album_artist and album_title:
        filename = str(album_artist + ' - ' + album_title)
        if album.disc_count == 1:
            check_for_file(filename + '.cue')
            check_for_file(filename + '.txt')
        else:
            for discnum in album:
                discname = '%s (Disc %s)' % (filename, discnum)
                check_for_file(discname + '.cue')
                check_for_file(discname + '.txt')


def handle_mapped_tags(disc):
    # Check for any tags which are obsolete and mapped to newer tags.
    # If old tag found and new tag not found, add new tag with old tag's value.
    # If both old and new tag found, warn if they don't have the same value.
    added = []
    mismatch = []
    for old_tag, new_tag in mapped_tags.items():
        if old_tag not in disc.tagset:
            continue
        disc.tagset |= {new_tag}
        added_tracks = []
        mismatch_tracks = []
        for tracknum, track in disc.items():
            if new_tag not in track:
                added_tracks.append(tracknum)
                track[new_tag] = track[old_tag]
                track.tagset |= {new_tag}
                continue
            try:
                if track[old_tag] == track[new_tag]:
                    continue
            except:
                pass
            mismatch_tracks.append(tracknum)
        if args.mapping and (added_tracks or mismatch_tracks):

            def msg_helper(kind, tracks):
                msg = '  %s %s %s in ' % (old_tag, kind, new_tag)
                if len(tracks) == len(disc):
                    msg += 'all tracks'
                else:
                    msg += 'tracks ' + ', '.join(map(str, sorted(tracks)))
                return msg

            if added_tracks:
                added.append(msg_helper('->', added_tracks))
            if mismatch_tracks:
                mismatch.append(msg_helper('!=', mismatch_tracks))
    if added:
        msgs.error('Obsolete tags need updating:')
        msgs.extend(sorted(added))
    if mismatch:
        msgs.error('Obsolete and updated tags both present with different values:')
        msgs.extend(sorted(mismatch))


def check_profile(disc):
    # Make sure the 'Classical' profile is only used for the 'Classical' genre
    # Don't bother testing if the genre and profile aren't identical across tracks.
    # Sets disc.classical, so run this soon after finding identical tags.
    if 'genre' not in disc.identical or 'profile' not in disc.identical:
        disc.classical = False
        return
    genre = flatten_tag(disc.identical['genre'])
    profile = flatten_tag(disc.identical['profile'])
    classical_genre = (genre.lower() == 'classical')
    classical_profile = (profile.lower() == 'classical')
    disc.classical = classical_profile
    if classical_genre != classical_profile:
        msgs.error("Unexpected profile '%s' for genre '%s'" % (profile, genre))


def check_inaccurate_rips(disc):
    # Check for any rips that failed the AccurateRip test
    inaccurate_tracks = {}
    for tracknum, track in disc.items():
        rip_result = flatten_tag(track.get('accurateripresult', ''))
        if 'inaccurate' in rip_result.lower():
            inaccurate_tracks[tracknum] = rip_result
    if inaccurate_tracks:
        msgs.error('AccurateRip verification failed:')
        for tracknum, rip_result in inaccurate_tracks.items():
            msgs.error('  Track %d: %s' % (tracknum, rip_result))


def check_missing_tags(disc):
    # Check that tags which should be present are actually present in all tracks
    if not args.missing:
        return
    desired_tags = required_classical_tags if disc.classical else required_tags
    disc_missing_tags = desired_tags - disc.tagset
    tracks_missing_tags = defaultdict(list)
    track_desired_tags = desired_tags - disc_missing_tags
    for tracknum, track in disc.items():
        track_missing_tags = track_desired_tags - track.tagset
        if track_missing_tags:
            missing_tags_str = ', '.join(sorted(track_missing_tags))
            tracks_missing_tags[missing_tags_str].append(tracknum)
    if disc_missing_tags or tracks_missing_tags:
        msgs.error('Missing Tags:')
        if disc_missing_tags:
            msgs.error('  All tracks: %s' % ', '.join(sorted(disc_missing_tags)))
        if tracks_missing_tags:
            output_dict_of_bad_tracks(tracks_missing_tags, disc)


def check_unknown_tags(disc):
    # Check that all tags are in the known_tags dictionary
    unknown_tags = disc.tagset - known_tags_set
    if not unknown_tags:
        return
    msgs.error('Unknown Tags:')
    common_track_tags = disc.tagset.copy()
    for track in disc.values():
        common_track_tags &= track.tagset
    disc_unknown_tags = unknown_tags & common_track_tags
    if disc_unknown_tags:
        msgs.error('  All tracks: %s' % ', '.join(sorted(disc_unknown_tags)))
    tracks_unknown_tags_set = unknown_tags - disc_unknown_tags
    if not tracks_unknown_tags_set:
        return
    for tracknum, track in disc.items():
        track_unknown_tags = tracks_unknown_tags_set & track.tagset
        if track_unknown_tags:
            msgs.error('  Track #%d: %s' % (tracknum, ', '.join(sorted(track_unknown_tags))))


def check_multivalued_tags(disc):
    # Check that tags with more than one value for a track are expected.
    for tracknum, track in disc.items():
        multivalued_tags = {tag for tag in track if len(track[tag]) > 1}
        unexpected = multivalued_tags - allowed_multivalued_tags
        if unexpected:
            msgs.error("Track #%d: Unexpected multivalued tracks '%s'" %
                        (tracknum, "', '".join(sorted(unexpected))))


def check_track_numbers(disc):
    # Check the track numbers to find missing tracks or tracks with unreasonable
    # track numbers
    track_count = None
    tracktotal = flatten_tag(disc.identical.get('tracktotal'))
    if tracktotal is None:
        msgs.error("Can't determine last track #: tracktotal not same in all tracks")
    else:
        try:
            track_count = int(tracktotal)
        except:
            msgs.error("Can't determine last track #: tracktotal %s not an int" % tracktotal)
    track_set = set(disc)
    if track_count is not None:
        expected_track_set = set(range(1, track_count + 1))
    else:
        expected_track_set = set(range(1, max(track_set) + 1))
    missing_tracks = expected_track_set - track_set
    extra_tracks = track_set - expected_track_set
    if missing_tracks:
        msgs.error('Missing Tracks: ' + ', '.join(map(str, sorted(missing_tracks))))
    if extra_tracks:
        msgs.error('Unexpected Tracks: ' + ', '.join(map(str, sorted(extra_tracks))))


def check_identical_tags(disc):
    # Check that tags which should be identical across all tracks are identical
    mismatch_tags = (identical_tags_within_disc & disc.tagset) - disc.identical.tagset
    if mismatch_tags:
        msgs.error('Tags not same across all tracks: ' + ', '.join(mismatch_tags))


def check_different_tags(disc):
    # Check that tags which should be different across all tracks are different
    for tag in different_tags:
        if tag not in disc.tagset:
            continue
        tag_values = {}
        need_warning = False
        for tracknum, track in disc.items():
            if tag in track:
                tag_value = flatten_tag(track[tag])
                if tag_value in tag_values:
                    need_warning = True
                    tag_values[tag_value].append(tracknum)
                else:
                    tag_values[tag_value] = [tracknum]
        if need_warning:
            msgs.error("Tag '%s' duplicated in multiple tracks:" % tag)
            for tag_value, tracks in tag_values.items():
                if len(tracks) > 1:
                    msgs.error('  %s in tracks ' % tag_value + ', '.join(map(str, tracks)))


def check_sort_tags(disc):
    # Check that the sorted version of tags (e.g. 'artist sort' for 'artist')
    # are a reasonable match for the corresponding tag.  The number of values
    # in corresponding tags should match, and the sorted tags should either
    # match the main tags, or be transformable by rearranging.  For example,
    # if the 'artist' tag has the two values 'John Smith' and 'Jane Doe', the
    # 'artist sort' tag should also have two values, the first of which is
    # either 'John Smith' or 'Smith, John', and the second either 'Jane Doe' or
    # 'Doe, Jane'.  Also warn if the sorted tag is missing on some, but not all,
    # tracks (warn on missing everywhere under cmdline option).
    if not args.sort_tag_mismatch:
        return
    for tag, sort_tag in sorted_tags.items():
        if (sort_tag not in disc.tagset and
                not args.no_sort_tag and
                not disc.classical):
            return
        missing = []
        mismatch = defaultdict(list)
        for tracknum, track in disc.items():
            if tag not in track.tagset and sort_tag not in track.tagset:
                continue    # ignore if both tags not present
            len1 = len(track[tag])
            if sort_tag not in track.tagset:
                missing.append(tracknum)
                continue
            tag_val = track.get(tag, [])
            sort_tag_val = track[sort_tag]
            if len(tag_val) == len(sort_tag_val):
                # Both tags have the same number of values.  Pair up the values
                # and compare them.
                for val1, val2 in zip(tag_val, sort_tag_val):
                    if val1 == val2:
                        continue

                    def canon_val(val):
                        # Split a value from a tag into its constituent words
                        # after removing commas and '[...]' comments.  Get rid
                        # of the words 'The' or 'Los' at either the beginning or
                        # end of the list of words.  Replace short last-name
                        # prefixes with their lower case version to avoid case
                        # differences.  E.g. 'Alex de Grassi' would be sorted as
                        # 'De Grassi, Alex', but 'de' vs. 'De' is not a problem.
                        # Return the final list sorted.
                        val = re.sub(r'\[[^]]*\]', '', val)
                        words = val.replace(',', '').split()
                        ignored = {'The', 'Los'}
                        if len(words) > 1 and words[-1] in ignored:
                            words.pop()
                        if len(words) > 1 and words[0] in ignored:
                            words.pop(0)
                        force_lower = {'de', 'van'}
                        for index, word in enumerate(words):
                            word_lower = word.lower()
                            if word_lower in force_lower:
                                words[index] = word_lower
                        return sorted(words)

                    if canon_val(val1) != canon_val(val2):
                        break
                else:
                    # All paired values could be matched, track is fine
                    continue
            # Tags either have different numbers of values, or those values
            # couldn't be matched.
            key = (flatten_tag(tag_val), flatten_tag(sort_tag_val))
            mismatch[key].append(tracknum)
        if missing or mismatch:
            msgs.error("Incompatible values for tags '%s' and '%s':" % (tag, sort_tag))
            errmsgs = []
            if missing:
                errmsgs.append((sorted(missing), "Tag '%s' not found" % sort_tag))
            for vals, tracks in mismatch.items():
                errmsgs.append((sorted(tracks), "'%s' versus '%s'" % vals))
            for tracks, msg in sorted(errmsgs):
                msgs.error("  %s: %s" % (track_list(tracks, len(disc)), msg))


def check_dups_in_tags(disc):
    # Check tags with multiple values in lists, and make sure none of the
    # items are duplicated within the list (e.g. composer = [Brian Eno, Brian Eno])
    for tracknum, track in disc.items():
        for tag, tag_value in track.items():
            if len(tag_value) > 1:
                tag_value_set = set(tag_value)
                if len(tag_value) != len(tag_value_set):
                    msgs.error("Track %d has duplicate value in tag '%s': %s" %
                                (tracknum, tag, ', '.join(tag_value)))


def check_leading_the(disc):
    # Check if the 'artist', 'albumartist', or 'composer' tags include entries
    # that start with a leading 'The', e.g. 'The Beatles' instead of 'Beatles, The'.
    error_items = {}  # { bad tag value : (set of tags, set of tracks) }

    def record_error_item(tag, tag_value, tracks):
        error_value = error_items.get(tag_value)
        if error_value:
            error_value = (error_value[0] | {tag}, error_value[1] | tracks)
        else:
            error_value = ({tag}, tracks)
        error_items[tag_value] = error_value

    for tag in test_leading_The_tags:
        if tag in disc.identical:
            for tag_value in disc.identical[tag]:
                if tag_value[0:4].lower() == 'the ':
                    record_error_item(tag, tag_value, set(disc))
        else:
            for tracknum in disc:
                for tag_value in disc[tracknum].get(tag, ''):
                    if tag_value[0:4].lower() == 'the ':
                        record_error_item(tag, tag_value, {tracknum})
    for tag_value, error_tuple in error_items.items():
        fmt_tracks = track_list(sorted(error_tuple[1]), len(disc)).lower()
        msgs.error("'%s' should be '%s': tag%s '%s' in %s" %
                    (tag_value, ', '.join((tag_value[4:], tag_value[0:3])),
                     's' if len(error_tuple[0]) != 1 else '',
                     "', '".join(sorted(error_tuple[0])),
                     fmt_tracks))


def check_multiple_artists(disc):
    # If the 'artist' tag isn't identical across tracks and the 'albumartist'
    # tag isn't found in each track's 'artist' tag, then make sure the
    # 'albumartist' tag is either 'Soundtrack', 'Various Artists', or 'TV Theme'
    # depending on the 'genre' tag. Not done for classical profile.
    if (disc.classical or
        'artist' in disc.identical or
        'albumartist' not in disc.identical or
        'genre' not in disc.identical):
        return
    album_artist = flatten_tag(disc.identical['albumartist'])
    album_artist_low = album_artist.lower()
    genre = flatten_tag(disc.identical['genre']).lower()
    for tracknum, track in disc.items():
        artists = flatten_tag(track['artist'])
        if album_artist_low not in artists.lower():
            expected = ['Soundtrack'] if genre == 'soundtrack' else ['Various Artists', 'TV Theme']
            if album_artist_low not in [x.lower() for x in expected]:
                msgs.error("AlbumArtist should be '%s', not '%s'" %
                            ("' or '".join(expected), album_artist))
            break


def check_compilation(disc):
    # Run checks for compilations:
    # * If profile is 'Classical', make sure the 'composer' tag is not identical across
    #   all tracks.
    # * If genre is 'Soundtrack', make sure the AlbumArtist is also 'Soundtrack'
    # * For other genres, make sure the AlbumArtist is either 'Various Artists' or
    #   'TV Theme'
    if 'compilation' not in disc.tagset:
        return
    if disc.classical:
        if 'composer' in disc.identical:
            msgs.error("For classical compilation, Composer should not be '%s' for all tracks" %
                        flatten_tag(disc.identical['composer']))
        return
    if 'albumartist' not in disc.identical or 'genre' not in disc.identical:
        return
    album_artist = flatten_tag(disc.identical['albumartist'])
    album_artist_low = album_artist.lower()
    genre = flatten_tag(disc.identical['genre']).lower()
    if genre == 'soundtrack':
        if album_artist_low != 'soundtrack':
            msgs.error("For soundtrack compilation, AlbumArtist should be 'Soundtrack', not '%s'" %
                        album_artist)
    else:
        if album_artist_low not in ['various artists', 'tv theme']:
            msgs.error("For this compilation, AlbumArtist should be 'Various Artists', not '%s'" %
                        album_artist)


def check_orchestra(disc):
    # For classical discs, make sure there's an orchestra tag if the conductor
    # tag exists.  Also make sure there's an orchestra tag if it looks like the
    # album artist or artist tags name an orchestra.
    if not disc.classical:
        return
    if 'conductor' in disc.tagset:
        no_orchestra = []
        for tracknum, track in disc.items():
            if 'conductor' in track and 'orchestra' not in track:
                no_orchestra.append(tracknum)
        if no_orchestra:
            msgs.error("Tag 'conductor' but no tag 'orchestra': %s" % track_list(no_orchestra, len(disc)))
    # Look for artist names that imply an orchestra, verify the orchestra tag
    # exists if found.
    bad_tracks = defaultdict(list)
    names = ('orchestra', 'symphon', 'philharmon', 'sinfoni')
    for tracknum, track in disc.items():
        artist = flatten_tag(track.get('artist', ''))
        artist_low = artist.lower()
        for name in names:
            if name in artist_low:
                break
        else:
            continue
        if 'orchestra' not in track.tagset:
            bad_tracks[artist].append(tracknum)
    if bad_tracks:
        msgs.error("Artist tag implies an orchestra, but no 'orchestra' tag found:")
        output_dict_of_bad_tracks(bad_tracks, disc)


def find_selected_tags(disc):
    # Not a correctness check - display any tracks using the selected tags.
    for tag in sorted(args.tag & disc.tagset):
        msgs.note("Tag '%s' found:" % tag)
        tag_vals = defaultdict(list)
        for tracknum, track in disc.items():
            if tag in track:
                tag_vals[flatten_tag(track[tag])].append(tracknum)
        output_dict_of_bad_tracks(tag_vals, disc, msgs.note)


def process_album(album_path):
    global msgs, album_count, disc_count, track_count, warn_count
    warn = False
    album_count += 1
    album, msgs = get_album(album_path)
    if album:
        check_disc_numbers(album)
        check_identical_tags_across_discs(album)
        check_nontag_info(album)
    if msgs:
        print("\nEarly checks of '%s' found problems:" % album_path)
        print(msgs)
    for discnum, disc in album.items():
        msgs.clear()
        disc_count += 1
        track_count += len(disc)
        handle_mapped_tags(disc)
        find_identical_disc_tags(disc)
        check_profile(disc)
        check_inaccurate_rips(disc)
        check_missing_tags(disc)
        check_unknown_tags(disc)
        check_multivalued_tags(disc)
        check_track_numbers(disc)
        check_identical_tags(disc)
        check_different_tags(disc)
        check_dups_in_tags(disc)
        check_sort_tags(disc)
        check_leading_the(disc)
        check_multiple_artists(disc)
        check_compilation(disc)
        check_orchestra(disc)
        find_selected_tags(disc)
        if msgs or args.verbose:
            album_display = album_path
            try:
                if int(flatten_tag(next(iter(disc.values())).get("disctotal", '1'))) != 1:
                    album_display += ' (Disc %d)' % discnum
            except ValueError:
                pass
            print("\nChecking '%s'" % album_display)
        if msgs:
            print(msgs)
    if msgs.errors or msgs.warnings:
        warn_count += 1


def main():
    parse_args()
    for root in sorted(args.path):
        for album_path in find_albums(root):
            process_album(album_path)

    def plural(count, name, zero='0'):
        if count == 1:
            return '1 ' + name
        elif count == 0:
            return '%s %ss' % (zero, name)
        else:
            return '%d %ss' % (count, name)

    print("\nProcessed %s, %s, %s - %s with issues" %
          (plural(album_count, 'album'), plural(disc_count, 'disc'),
           plural(track_count, 'track'), plural(warn_count, 'album', zero='No')))
    if args.pause:
        try:
            input('\nPress Enter when ready...')
        except:
            pass

if __name__ == '__main__':
    main()
