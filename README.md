# dBpa-scripts

## Scripts to help rip CDs with dBpoweramp and mp3tag

---

I'm in the middle of ripping a couple thousand CDs to FLAC using
[dBpoweramp CD Ripper](https://dbpoweramp.com) for the initial rip and
[mp3tag](http://www.mp3tag.de/en) for tag cleanup.
This repo hosts a group of Python 3.4 scripts I've written which let me
streamline my workflow and catch mistakes made while processing CDs.

### Example workflow

Here's an example of how these scripts help out.
I used CD Ripper to rip a Beethoven CD.
In this case, I started the rip without editing any tags in CD Ripper, to show
what happens.
I've set up my CD Ripper profiles to use the `Run External` DSP to run these
scripts.
When the CD was fully ripped, a console window opened up automatically, and
displayed the following (pressing Enter dismissed the window):

```
Renaming 'cuesheet.cue' to 'Ludwig van Beethoven - Symphonies Nos. 4 & 7 [Karajan].cue'

Checking 'D:\CDRip\Classical\Beethoven, Ludwig van\Symphonies Nos. 4 & 7 [Karajan] - Ludwig van Beethoven (1985)'
  Missing Tags:
    All tracks: album artist sort, albumartistterse, artistterse, composerterse, upc
  Incompatible values for tags 'artist' and 'artist sort':
    All tracks: Tag 'artist sort' not found
  Incompatible values for tags 'albumartist' and 'album artist sort':
    All tracks: Tag 'album artist sort' not found

Processed 1 album, 1 disc, 8 tracks - 1 album with issues

Press Enter when ready...
```

The first line shows the cuesheet file being renamed.
I have CD Ripper set up to write a multi-track cuesheet, but CD Ripper will
always name that file cuesheet.cue.
My scripts rename the cuesheet with the same naming scheme I use for CD
Ripper's Audio Extraction Log file.

Next, the script detected several problems with the tags in the ripped FLAC
files.
There are a number of tags which I always want defined (some just for classical
CDs).
The first error complains about some of those required tags missing in all
tracks.
The other errors are triggered by missing tags as well, but are there to detect
more general problems.
For instance, an `Artist` tag of `John Smith` and an `Artist Sort` tag of
`Smith, George` would trigger a complaint about incompatible values for those
two tags.

The missing tags include three user-defined tags I use to keep pathnames from
getting too long, a big problem with classical CDs.
These tags need to be added.
Also, it's not obvious here, but this album has the composer, Beethoven, listed
as the artist.
I prefer the various artist tags to identify the actual performers, so those
changes will be made manually.
I opened the album folder in mp3tag and made the following changes to all
tracks:

* Set `Album` to `Beethoven Symphonies Nos. 4 & 7`
* Set `Artist` to `Herbert von Karajan\\Berliner Philharmoniker` (`\\` being
  mp3tag's way of separating items in a multi-valued tag, like `;` in
dBpoweramp).
* Set `Artist Sort` to `Karajan, Herbert von\\Berliner Philharmoniker`
* Set `AlbumArtist` to `Herbert von Karajan - Berliner Philharmoniker`
* Set `Album Artist Sort` to `Karajan, Herbert von - Berliner Philharmoniker`
* Set `UPC` to `028941512123`
* Run an mp3tag action that I created, `Add terse fields`, to define the
  `ArtistTerse`, `AlbumArtistTerse`, and `ComposerTerse` fields from the
associated sort fields.  This will set these user-defined tags to `Karajan`,
`Karajan`, and `Beethoven` respectively.

I've defined three external tools in mp3tag which run my scripts, so I can
quickly check the status of my tag edits and know when I'm done.
Pressing Ctrl-1 in mp3tag runs the `CheckFlacTags.py` script which repeats part
of the post-rip script, but now generates the following:

```
Early checks of 'D:\CDRip\Classical\Beethoven, Ludwig van\Symphonies Nos. 4 & 7 [Karajan] - Ludwig van Beethoven (1985)' found problems:
  File 'Herbert von Karajan - Berliner Philharmoniker - Beethoven Symphonies Nos. 4 & 7.cue' not found
  File 'Herbert von Karajan - Berliner Philharmoniker - Beethoven Symphonies Nos. 4 & 7.txt' not found

Checking 'D:\CDRip\Classical\Beethoven, Ludwig van\Symphonies Nos. 4 & 7 [Karajan] - Ludwig van Beethoven (1985)'

Processed 1 album, 1 disc, 8 tracks - 1 album with issues

Press Enter when ready...
```

This says that the tag issues have all been cleared up, but the cuesheet and
extraction log files no longer have the expected names.
No problem - pressing Ctrl-2 runs the `RearrangeAudioFiles.py` script in dry-run
mode, and shows this:

```
Note: This is a dry run; no changes are being made

Processing D:\CDRip\Classical\Beethoven, Ludwig van\Symphonies Nos. 4 & 7 [Karajan] - Ludwig van Beethoven (1985)
Rename to: D:\CDRip\Classical\Beethoven, Ludwig van\Beethoven Symphonies Nos. 4 & 7 - Karajan (1985)
Rename 01 Symphony No. 4 in B flat major; I Adagio - Allegro vivace (Ludwig van Beethoven - Ludwig van Beethoven).flac
    -> 01 Symphony No. 4 in B flat major; I Adagio - Allegro vivace (Beethoven - Karajan).flac
Rename 02 Symphony No. 4 in B flat major; II Adagio (Ludwig van Beethoven - Ludwig van Beethoven).flac
    -> 02 Symphony No. 4 in B flat major; II Adagio (Beethoven - Karajan).flac
Rename 03 Symphony No. 4 in B flat major; III Allegro vivace (Ludwig van Beethoven - Ludwig van Beethoven).flac
    -> 03 Symphony No. 4 in B flat major; III Allegro vivace (Beethoven - Karajan).flac
Rename 04 Symphony No. 4 in B flat major; IV Allegro ma non troppo (Ludwig van Beethoven - Ludwig van Beethoven).flac
    -> 04 Symphony No. 4 in B flat major; IV Allegro ma non troppo (Beethoven - Karajan).flac
Rename 05 Symphony No. 7 in A major; I Poco sostenuto - vivace (Ludwig van Beethoven - Ludwig van Beethoven).flac
    -> 05 Symphony No. 7 in A major; I Poco sostenuto - vivace (Beethoven - Karajan).flac
Rename 06 Symphony No. 7 in A major; II Allegretto (Ludwig van Beethoven - Ludwig van Beethoven).flac
    -> 06 Symphony No. 7 in A major; II Allegretto (Beethoven - Karajan).flac
Rename 07 Symphony No. 7 in A major; III Presto (Ludwig van Beethoven - Ludwig van Beethoven).flac
    -> 07 Symphony No. 7 in A major; III Presto (Beethoven - Karajan).flac
Rename 08 Symphony No. 7 in A major; IV Allegro con brio (Ludwig van Beethoven - Ludwig van Beethoven).flac
    -> 08 Symphony No. 7 in A major; IV Allegro con brio (Beethoven - Karajan).flac
Rename Ludwig van Beethoven - Symphonies Nos. 4 & 7 [Karajan].cue
    -> Herbert von Karajan - Berliner Philharmoniker - Beethoven Symphonies Nos. 4 & 7.cue
Rename Ludwig van Beethoven - Symphonies Nos. 4 & 7 [Karajan].txt
    -> Herbert von Karajan - Berliner Philharmoniker - Beethoven Symphonies Nos. 4 & 7.txt

Press Enter when ready...
```

This looks reasonable; the FLAC and associated files, as well as the album
folder, will all be renamed using the new versions of various tags.
Pressing Ctrl-3 runs `RearrangeAudioFiles.py` to make the actual changes (with
output text almost identical to the dry-run output).
After that, pressing Ctrl-1 to rerun `CheckFlacTags.py` shows this:

```
Checking 'D:\CDRip\Classical\Beethoven, Ludwig van\Beethoven Symphonies Nos. 4 & 7 - Karajan (1985)'

Processed 1 album, 1 disc, 8 tracks - No albums with issues

Press Enter when ready...
```

The album directory is now cleaned up and ready for moving to my NAS.
<!-- vim: set tw=80: -->
