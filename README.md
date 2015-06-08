# dBpa-scripts

## Scripts to help rip CDs with dBpoweramp and mp3tag

---

I'm in the middle of ripping a thousand or so CDs to FLAC using the paid
Reference version of [dBpoweramp CD Ripper](https://dbpoweramp.com) for the
initial rip and [mp3tag](http://www.mp3tag.de/en) for tag cleanup.
This repo hosts a group of Python 3.4 scripts I've written which let me
streamline my workflow and catch mistakes made while processing CDs.

These scripts are intended to be run from the command line on Windows, as well
as be integrated into CD Ripper and mp3tag via those programs' abilities to
invoke external programs.

The scripts enforce my particular tag and naming scheme, so they'll probably
need some editing for use elsewhere.
Thankfully, Python turns out to be far easier to understand and change than the
C/C++ I'm more used to (this doubled as my 'learn Python' project).

---

### Example workflow

Here's an example of how these scripts help out.
I used CD Ripper to rip a Beethoven CD.
In this case, I started the rip without editing any tags in CD Ripper, to show
what happens.
I've set up my CD Ripper profiles to use the **Run External** DSP to run these
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
For instance, an **Artist** tag of **John Smith** and an **Artist Sort** tag of
**Smith, George** would trigger a complaint about incompatible values for those
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

* Set **Album** to **Beethoven Symphonies Nos. 4 & 7**
* Set **Artist** to **Herbert von Karajan\\\\Berliner Philharmoniker** ('\\\\' being
  mp3tag's way of separating items in a multi-valued tag, like ';' in
dBpoweramp).
* Set **Artist Sort** to **Karajan, Herbert von\\\\Berliner Philharmoniker**
* Set **AlbumArtist** to **Herbert von Karajan - Berliner Philharmoniker**
* Set **Album Artist Sort** to **Karajan, Herbert von - Berliner Philharmoniker**
* Set **UPC** to **028941512123**
* Run an mp3tag action that I created, **Add terse fields**, to define the
  **ArtistTerse**, **AlbumArtistTerse**, and **ComposerTerse** fields from the
associated sort fields. This will set these user-defined tags to **Karajan**,
**Karajan**, and **Beethoven** respectively.

I've defined three external tools in mp3tag which run my scripts, so I can
quickly check the status of my tag edits and know when I'm done.
Pressing Ctrl-1 in mp3tag runs the **CheckFlacTags.py** script which repeats part
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
No problem - pressing Ctrl-2 runs the **RearrangeAudioFiles.py** script in dry-run
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
Pressing Ctrl-3 runs **RearrangeAudioFiles.py** to make the actual changes (with
output text almost identical to the dry-run output).
After that, pressing Ctrl-1 to rerun **CheckFlacTags.py** shows this:

```
Checking 'D:\CDRip\Classical\Beethoven, Ludwig van\Beethoven Symphonies Nos. 4 & 7 - Karajan (1985)'

Processed 1 album, 1 disc, 8 tracks - No albums with issues

Press Enter when ready...
```

The album directory is now cleaned up and ready for moving to my NAS.
Running the **FindLongPaths.py** script before and after running
**RearrangeAudioFiles.py** above shows that the longest path was reduced from 214
characters to 177.

---

### The Scripts

The following scripts are available:

* **CheckFlacTags.py**: Analyzes FLAC and associated files gathered together in an
  album folder. The FLAC file tags are run through a large number of validity
  checks.
* **RearrangeAudioFiles.py**: Update the names of FLAC and associated files in
  an album folder. Can either rename the files and the album folder in place,
or copy/move the album folder to a new location.
* **FindLongPaths.py**: Find all files under some root with pathnames that
  exceed a given limit. I use this to see how close I'm getting to Window's
260-character pathname limit, to avoid truncating filenames.
* **LogRippedTrack.py**: Helper executed by a **Run External** DSP after each
  track is ripped in CD Ripper. **Run External** can't pass dynamic info like the
album directory and tag names to the external script when run after the entire
disc is ripped, so I do this after each track instead, saving the same data each
time to a temporary file.
* **PostRipProcess.py**: Helper executed by a **Run External** DSP after an entire
  disc is ripped in CD Ripper. Takes the info saved by **LogRippedTrack.py** and
uses it to rename the cuesheet.cue file and run **CheckFlacTags.py** on the disc
that was just ripped.
* **CommonUtils.py**: Shared module for other scripts.

#### CheckFlacTags.py

```
usage: CheckFlacTags.py [-h] [-v] [-m] [-M] [-o] [-p] [-s] [-S] [-t TAG]
                        [path [path ...]]

Check FLAC files for tag consistency.

positional arguments:
  path                  root of the tree to search for albums of FLAC files
                        (default: D:\CDRip)

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Show every album processed, not just ones with issues
  -m, --missing         Don't warn about missing required tags
  -M, --mapping         Don't warn about mapping obsolete tags to newer ones
  -o, --other           Don't warn about missing non-FLAC files
  -p, --pause           Pause before exiting
  -s, --sort-tag-mismatch
                        Don't warn about mismatches between a tag and the sort
                        tag variant (e.g. Artist vs. Artist Sort)
  -S, --no-sort-tag     Warn if a sort tag (e.g. Artist Sort) is missing on
                        all tracks of a disc, not just some
  -t TAG, --tag TAG     Find all tracks with the given tag
```

**CheckFlacTags** will find all album folders (directories with one or more FLAC
files) under a given root path, and run a large number of tests on the album
files. As of this writing, the following tests are run:

* Test if the **DiscNumber** or **TrackNumber** tags are missing or malformed, or if
  the same Disc/Track settings are found in multiple files.
* Test that the **DiscTotal** tag is identical across all files, and that all disc
  numbers from 1 to **DiscTotal**, and no others, are found in the FLAC files.
* For multi-disc albums, test that tags which should be identical across discs
  are so.
* Test non-FLAC files. Make sure the cover file folder.jpg exists, and that the
  cuesheet and extraction log files are present and have the expected names.
* Test if obsolete forms of certain tags are present. CD Ripper used to use the
  tags **Organization**, **TotalDiscs**, and **TotalTracks** instead of the current
  **Label**, **DiscTotal**, and **TrackTotal**.
* Test that the CD Ripper profile setting is **Classical** if and only if the
  **Genre** tag is also **Classical**.
* Test that AccurateRip was successful in all tracks.
* Test that tags which should be present in all tracks are so.
* Test that no unknown tags were found.
* Test that the only multivalued tags found were tags that permit multivalues
  (e.g. **Artist** or **Soloists**).
* Test that the **TrackTotal** tag is identical across all files for a single
  disc, and that all track numbers from 1 to **TrackTotal**, and no others, are
  found in the disc's FLAC files.
* Test that tags which should be identical across tracks of a single disc are
  so.
* Test that tags which should have unique values in each track are so.
* Test that multivalued tags don't repeat one of those values (e.g. an **Artist**
  tag of **John Doe; John Doe**).
* Test that the regular and sorted version of paired tags (e.g. **Artist** and
  **Artist Sort**) have the same values, ignoring ordering.
* Test if certain tags start with a leading 'The ', e.g. **The Beatles** should
  instead be **Beatles, The**.
* For non-classical CDs where the **Artist** tag varies across tracks, the
  **AlbumArtist** tag should either be found in the **Artist** tag, or the
  **AlbumArtist** should be **Various Artists**, **Soundtrack**, or **TV Theme**.
* If a disc is marked as a compilation (the **Compilation** tag exists), make sure
  the compilation status makes sense. For classical CDs, the 'Composer' tag
  should not be identical across tracks. If the **Genre** is Soundtrack, the
  **AlbumArtist** should be as well. Otherwise, the **AlbumArtist** should be
  either **Various Artists** or **TV Theme**.
* For classical discs, test that the **Orchestra** tag is present if it looks like
  it should, because either an artist's name includes something like 'Orchestra'
  or 'Symphony', or there's a **Conductor** tag.
* (Not a validity test) If the --tag option is used, output all tracks which use
  the tags to search for.

If these tests aren't quite what you want, the code should be pretty easy to
tweak. In particular, you might need to change one of the items initialized
towards the front of the script, **known_tags**, **mapped_tags**, **sorted_tags**, and
**test_leading_The_tags**.

#### RearrangeAudioFiles.py

```
usage: RearrangeAudioFiles.py [-h] [-l max] [-m] [-n] [-o tag value] [-p] [-s]
                              [-t] [-v]
                              source [dest]

Rename and copy/move FLAC files and associated files according to the tags in
those FLAC files.

positional arguments:
  source                Root of tree with files to process
  dest                  Root of tree to which files are moved/copied. If
                        omitted, then files and album folders are renamed in
                        place as necessary and not copied/moved to a new
                        location.

optional arguments:
  -h, --help            show this help message and exit
  -l max, --len max     Truncate generated pathnames that exceed 'max'
                        characters (default 259)
  -m, --move            Move files to the destination instead of copying
  -n, --dry-run         Don't actually move/copy/rename, just show what would
                        be done (implies -vv)
  -o tag value, --override tag value
                        Override a tag by marking it as identical across an
                        album, with the given new value. Useful for overriding
                        the values which are used to create the path to an
                        album's new location. Separate multiple values for a
                        tag with semicolons. Example: -o artist "John Doe;Jane
                        Smith"
  -p, --pause           Pause before exiting
  -s, --sorted-artist   For non-classical albums, use the [Album Artist Sort]
                        tag, not [AlbumArtist], for the top-level directory
                        under which albums are written.
  -t, --truncate-warn   Disable the warning if a file needs to be truncated
  -v, --verbose         Output more info about what's being done. Repeated
                        uses (-vv) will display even more info.
```

**RearrangeAudioFiles** is basically a stand-alone version of the **Arrange
Audio** utility codec for dBpoweramp's Batch Converter. I wrote it because I
needed more flexibility, since the Arrange Audio utility won't copy all the
album files when rearranging, just the FLAC files and folder.jpg. Once it was
written, I found it very useful as an external tool for mp3tag.

The script has two modes of operation. When invoked with a single root
directory, it will find all album folders under that root and rename the files
within that album folder and the folder itself according to the tags found in
the album's FLAC files. The renaming scheme is hard-wired to match the one I
use (documented later on). This mode won't rename any parent folders of the
album folder.

When invoked with two directories, which can't point to the same place, the
script will copy or move the album files to new paths under the second,
destination path, while renaming the files in the same fashion as the in-place
rename (single root) mode.

#### FindLongPaths.py

```
usage: FindLongPaths.py [-h] [-l LEN] [path [path ...]]

Find files with long pathnames.

positional arguments:
  path               root of tree to search for long paths (default:
                     ['D:\\CDRip'])

optional arguments:
  -h, --help         show this help message and exit
  -l LEN, --len LEN  minimum path length to be reported (default: 250)
```

**FindLongPaths** is a simple utility which I find useful for working with
extremely long pathnames, as commonly happens with classical CDs. It just walks
the tree from a root and shows every path whose length exceeds a limit
(defaulting to 250). I use it when dealing with long paths, to know when I
might need to tweak some track or folder titles to keep path lengths reasonable.

Note that **RearrangeAudioFiles** has its own ability to warn about long paths.
I often use that instead of **FindLongPaths**, using the --dry-run and --len
options to see if moving albums to a new location might run into problems.

#### PostRipProcess.py and LogRippedTrack.py

**PostRipProcess** is meant to be invoked by CD Ripper upon completing a disc
rip. It mostly exists to invoke **CheckFlacTags** on the just-ripped album
folder, for a quick look at the results. Sometimes, when things are really off,
it's better to just delete and rerip than try to fix things in mp3tag.

The script also works around a limitation of CD Ripper. My workflow includes
creating a multi-track cuesheet, which I want to name the same as the audio
extraction log. But while CD Ripper allows you to control the log file's name,
it always uses 'cuesheet.cue' for the cuesheet. That's insufficient, especially
when storing multi-disc CD sets in the same album folder (as I do).
**PostRipProcess** renames the cuesheet appropriately as one of its tasks.

There is another complication of CD Ripper to be worked around. While you can
use the **Run External** DSP to run something after a disc is ripped, that
script can't be passed any dynamic information. To work around that, I have CD
Ripper invoke **LogRippedTrack** using another **Run External** DSP after every
track is ripped. Dynamic arguments can be passed at that time, so
**LogRippedTrack** just saves some information away for **PostRipProcess** to
find.

One more thing - these scripts insist on being invoked by CD Ripper. That's
because they're made to handle ripping more than one CD at a time, using
multiple CD drives and multiple instances of CD Ripper. **LogRippedTrack** and
**PostRipProcess** communicate via a temporary file whose name depends on the
process ID of the CD Ripper instance invoking the scripts.

---

### Configuration

There's a lot of configuration involved in getting these scripts to work. The
following describes my setup. The scripts are hard-wired to match some of these
settings, so it'll help to know what my setup looks like if you want to
personalize the scripts.

#### Python

I'm using
[ActiveState's ActivePython](http://www.activestate.com/activepython/downloads),
version 3.4.1.0. I use Python 3 instead of the more common Python 2 because I
found it easier to work with Unicode data using Python 3 (classical and Celtic
CDs use a lot of accented characters).

You'll need to install the **mutagen** module, which is used to read the tags in
FLAC files. Using the Python3 version of pypm, run **pypm install mutagen**.

The scripts use a shell-bang comment of **#! python3** as the first line to make
sure Python 3 is used instead of Python 2 when invoking the script directly
(e.g. running **CheckFlacTags** at the command line instead of **python3
CheckFlacTags.py**). That shebang depends on the correct associations for
the Python extensions, which should look something like these:

```
C:\Tools\Scripts\dBpa>assoc | findstr /i python
.py=Python.File
.pyc=Python.CompiledFile
.pyo=Python.CompiledFile
.pyw=Python.NoConFile

C:\Tools\Scripts\dBpa>ftype | findstr /i python
Python.CompiledFile="C:\Tools\Python34\py.exe" "%1" %*
Python.File="C:\Tools\Python34\py.exe" "%1" %*
Python.NoConFile="C:\Tools\Python34\pyw.exe" "%1" %*
```

#### dBpoweramp CD Ripper

Configuration steps:
* Define profiles
* Set up **ID Tag Processing** DSP
* Set up **ReplayGain** DSP
* Set up **CUE Sheet - Multiple Files** DSP
* Set up two instances of the **Run External** DSP
* Configure tags selection
* Configure audio extraction log naming

I have two CD Ripper profiles defined, **Pop/Rock** and **Classical**. These
are identical except for the **Naming** value, defining where ripped files are
stored. Both profiles rip FLAC files to **D:\CDRip**. These profile names are
hard-wired into **RearrangeAudioFiles.py**. The **Classical** profile name is
hard-wired into **CheckFlacTags.py**.

The **Pop/Rock** profile has the following **Naming** value:

```
[IFVALUE]album artist,[album artist],[IFCOMP]Various Artists[][IF!COMP][artist][][]\[album] ([year])\[IFMULTI]Disc [disc] - [][track] [title] ([artist])
```

The **Classical** profile uses this (ridiculously long) **Naming** setting:

```
Classical\[IFVALUE]compilation,Compilations,[IFVALUE]composersort,[tag]composersort[],[composer][][]\[album][IFVALUE]albumartistterse, - [tag]AlbumArtistTerse[],[IFVALUE]album artist, - [album artist],[][] ([year])\[IFMULTI]Disc [disc] - [][track] [title] ([IFVALUE]composerterse,[tag]composerterse[],[composer][] - [IFVALUE]artistterse,[tag]artistterse[],[artist][])
```

Both of these values are written to create reasonable paths even before the tags
have been cleaned up after a rip. When all the proper tags exist, though, as
checked by **CheckFlacTags** and required by **RearrangeAudioFiles**, the
effective paths are simpler:

```
Pop/Rock profile:
[album artist]\[album] ([year])\[IFMULTI]Disc [disc] - [][track] [title] ([artist])
Examples:
Dire Straits\Love Over Gold (1982)\01 Telegraph Road (Dire Straits).flac
Peter Gabriel\Scratch My Back (2010)\Disc 1 - 01 Heroes (Peter Gabriel).flac
Various Artists\For the Kids (2002)\07 The Hoppity Song (John Ondrasik of Five For Fighting).flac

Classical profile:
Classical\[IFVALUE]compilation,Compilations,[tag]composersort[][]\[album] - [tag]AlbumArtistTerse[] ([year])\[IFMULTI]Disc [disc] - [][track] [title] ([tag]composerterse[] - [tag]artistterse[])
Examples:
Classical\Beethoven, Ludwig van\Beethoven Symphonies Nos. 5 & 6 'Pastorale' - Karajan-Berlin Phil. (1982)\03 Symphony No. 5; 3. Allegro (Beethoven - Karajan).flac
Classical\Compilations\Horowitz in Moscow - Horowitz (1986)\13 Traumerei (Schumann - Horowitz).flac
```

My naming scheme for classical CDs depends on three user-defined
tags which are used to limit the length of file paths. **CheckFlacTags** and
**RearrangeAudioFiles** will issue errors if these do not exist, and I've
configured an mp3tag action to generate these tags from the associated sort
tags.

* **ArtistTerse**: A short version of the **Artist Sort** tag (e.g. **Horowitz**
  for **Horowitz, Vladimir**).
* **AlbumArtistTerse**: A short version of the **Album Artist Sort** tag (e.g.
  **Serkin/Ozawa/BSO** for **Serkin, Rudolf - Ozawa, Seiji - Boston Symphony**)
* **ComposerTerse**: A short version of the **ComposerSort** tag (e.g.
  **Beethoven** for **Beethoven, Ludwig van**).

There are two other user-defined tags which are required in all tracks,
**CDGap** and **CDIndex**. These expose hidden functionality in CD Ripper.
First, you must enable the **Gap (Pre-Track)** and **Index Positions** columns
in CD Ripper. When these columns are shown, CD Ripper will detect the gaps and
index values defined on a CD, making those available via internal hidden tags
**_cdgap** and **_cdindex**.

Next, in the DSP tab at the bottom of CD Ripper, add the **ID Tag Processing**
DSP, and bring up its settings dialog. On the Map tab, add two mappings, from
**_cdgap** to **CDGap**, and from **_cdindex** to **CDIndex**. You might need to
first install the **DSP Effects** package from
[here](https://www.dbpoweramp.com/dbpoweramp-dsp.htm). Be sure to add this DSP
to all your profiles.

I populate these two user-defined tags because I'm trying to record as much info
from a ripped CD as reasonable. If I want to reburn a CD in the future, I'll
need the gap and index info to make a faithful copy. Note: the CD gap/index
functionality is a little flaky. **CheckFlacTags** will sometimes complain
about missing **CDGap** and **CDIndex** tags after a rip. Hitting Refresh in CD
Ripper will usually correct that, and then I have to delete and re-rip. I try
to glance at the Gap column in CD Ripper's display before hitting Rip, so I
notice the missing info and refresh before ripping.

I've got a few other DSPs enabled in CD Ripper. Again in the DSP tab, add the
**ReplayGain** DSP, bring up its settings dialog, and choose **Track & Album
Gain** in the **Write** selection list. I also install the **CUE Sheet -
Multiple Files** DSP, with **UTF-8 Encoding** enabled in its settings. You can
install that DSP according to the instructions in the dBpoweramp forums
[here](https://forum.dbpoweramp.com/showthread.php?18981-CUE-Sheet-Image-Utility-Codec).

Next, two instances of the **Run External** DSP need to be added to invoke the
scripts automatically during ripping. Add the first instance of **Run
External**, bring up its settings dialog, and make the following entries:

* **Run**: set to **After Conversion**
* **Program**: Press **Set** and type **%comspec%** for the **File name**. This
  will set the Program to cmd.exe.
* **Command Line**: Set to the following, changing the paths to **python3.exe**
  and **LogRippedTrack.py** as appropriate:

```
/c C:\Tools\Python34\python3.exe C:\Tools\Scripts\dBpa\LogRippedTrack.py "[IFVALUE]album artist,[album artist],[IFCOMP]Various Artists[][IF!COMP][artist][][] - [album][IFMULTI] (Disc [disc])[].cue" "[TRIMLASTFOLDER][outfilelong][]\"
```

Add the second instance of the **Run External** DSP, making the following
entries into its settings:

* **Run**: Set to **After Batch**
* **Program**: Press **Set** and type **%comspec%** for the **File name**. This
* **Command Line**: Set to the following, changing the paths to **python3.exe**
  and **PostRipProcess.py** as appropriate:

```
/c C:\Tools\Python34\python3.exe c:\tools\scripts\dBpa\PostRipProcess.py
```

Make sure you add these 5 DSPs to both the **Classical** and the **Pop/Rock**
profiles.

I enable the audio extraction log for each rip. In CD Ripper, select
**Options** , then enable **Secure** under the Ripping Method, and bring up the
**Secure Settings** dialog. At the bottom, you'll see the **Secure Extraction
Log** section. Enable both **Write To File** and **Add To Information Log**.
Then set the **Log Filename** path to:

```
[rippedtopath]\[IFVALUE]album artist,[album artist],[IFCOMP]Various Artists[][IF!COMP][artist][][] - [album][IFMULTI] (Disc [disc])[].txt
```

Finally, tell CD Ripper to write every tag it knows about. Select **Options**,
then in the **Meta Data** section, select **Options** for **Meta Data & ID
Tag**. Scroll down to the **Write ID Tags** section of the resulting dialog, and
enable every tag there (currently, those go from **AccurateRip Result** to
**HDCD**). I also enable **Force no date on year**, so the date I add to the
album folder names is just the 4-digit year.

CD Ripper should now be configured for interacting with the **CheckFlacTags**
script automatically.

#### mp3tag

I add three external tools to mp3tag to invoke **CheckFlacTags.py** and
**RearrangeAudioFiles.py** from within the program. Select **Tools** from the
menu bar, then **Tools** in the **Mp3tag Option** dialog. Click **New** (the
button with the star) to add each of these three external tools:

Tool #1 (invoked with Ctrl-1):
* **Name**: Set to **CheckFlacTags**
* **Path**: Path to **python3.exe** (C:\Tools\Python34\python3.exe in my case)
* **Parameter**: Set to **C:\Tools\Scripts\dBpa\CheckFlacTags.py -pSv "$cutRight(%_folderpath%,1)"**

Tool #2 (invoked with Ctrl-2):
* **Name**: Set to **Rename files in-place (preview)**
* **Path**: Path to **python3.exe** (C:\Tools\Python34\python3.exe in my case)
* **Parameter**: Set to **C:\Tools\Scripts\dBpa\RearrangeAudioFiles.py -p -n "$cutRight(%_folderpath%,1)"**

Tool #3 (invoked with Ctrl-3):
* **Name**: Set to **Rename files in-place**
* **Path**: Path to **python3.exe** (C:\Tools\Python34\python3.exe in my case)
* **Parameter**: Set to **C:\Tools\Scripts\dBpa\RearrangeAudioFiles.py -p -vv "$cutRight(%_folderpath%,1)"**

Replace the paths to python3.exe and the scripts as appropriate for your
installation.

I also define a couple action groups to make it easier to define the tags that
**CheckFlacTags** will be looking for:

The first action group, **Artist to ArtistSort**, is useful when the ArtistSort
tag is missing. It guesses the appropriate name for the sort tag by rearranging
the artist tag, for instance, rearranging 'Jane Doe [Violin]' to 'Doe, Jane
[Violin]'.

* Name of action group: Set to **A&rtist to ArtistSort**
* Action 1: 
  * **Action type**: Set to **Format value**
  * **Field**: Set to **ARTIST SORT**
  * **Format string**: Set to **$meta_sep(ARTIST,'|')**
* Action 2: 
  * **Action type**: Set to **Replace with regular expression**
  * **Regular expression**: Set to **([^[|]+)\s+([^[| ]+)(\s+\\[[^|]*])?**
  * **Replace matches with:**: Set to **$2, $1$3**
* Action 3:
  * **Action type**: Set to **Split field by separator**
  * **Field**: Set to **ARTIST SORT**
  * **Separator**: Set to **|**

The second action group, **Add terse fields**, creates the user-defined tags
that I use in the pathnames of classical music tracks from the associated 'sort'
tags, as mentioned earlier. It works by copying everything from the matching
'sort' tag into the 'terse' tag, up to but not including the first comma.

* Name of action group: Set to **&Add &terse fields**
* Action 1:
  * **Action type**: Set to **Format value**
  * **Field**: Set to **ALBUMARTISTTERSE**
  * **Format string**: Set to **$regexp(%album artist sort%,^(.\*)','.*,$1)**
* Action 2:
  * **Action type**: Set to **Format value**
  * **Field**: Set to **ARTISTTERSE**
  * **Format string**: Set to **$regexp(%artist sort%,^(.\*)','.*,$1)**
* Action 3:
  * **Action type**: Set to **Format value**
  * **Field**: Set to **COMPOSERTERSE**
  * **Format string**: Set to **$regexp(%composersort%,^(.\*)','.*,$1)**

<!-- vim: set tw=80: -->
