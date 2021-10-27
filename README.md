bbcscrobbler
============

[![Build Status](https://travis-ci.org/hugovk/lastfm-tools.svg?branch=master)](https://travis-ci.org/hugovk/lastfm-tools)
[![Python: 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A script to scrobble BBC Radio music to your Last.fm profile by copying scrobbles from the BBC radio accounts at Last.fm.

Forget to stop the scrobbler running when stopping the radio and leaving the computer? Not to worry, bbcscrobbler.py
only scrobbles when iTunes or Winamp is playing BBC radio.

Basic use:

```
bbcscrobbler.py
```

Want to ignore iTunes/Winamp and scrobble via the web or from a real radio? Defaults to BBC 6 Music:

```
bbcscrobbler.py --ignore-media-player
```

Or ignore iTunes/Winamp and scrobble a named station ([bbcradio1](https://www.last.fm/user/bbcradio1), [bbc1xtra](https://www.last.fm/user/bbc1xtra), [bbcradio2](https://www.last.fm/user/bbcradio2) or [bbc6music](https://www.last.fm/user/bbc6music)):

```
bbcscrobbler.py bbc1xtra --ignore-media-player
```


Example output:

```
>bbcscrobbler.py
Tuned in to bbc6music
---------------------
Now playing: Annie Eve - Shuffle
Scrobbled:   Annie Eve - Shuffle
Now playing: Nightmares on Wax - Les Nuits
Scrobbled:   Nightmares on Wax - Les Nuits
Now playing: Black Rebel Motorcycle Club - Spread Your Love
Scrobbled:   Black Rebel Motorcycle Club - Spread Your Love
Now playing: Cate le Bon - Sisters
Scrobbled:   Cate le Bon - Sisters
Now playing: Grace Jones - I've Seen That Face Before (Libertango)
Scrobbled:   Grace Jones - I've Seen That Face Before (Libertango)
Now playing: Sly & Robbie - Boops (Here To Go)
Tuned in to bbcradio1
---------------------
Now playing: Klingande - Jubel
Tuned in to bbcradio2
---------------------
Now playing: Prince & The Revolution - Let's Go Crazy
Winamp:      Wrong station
Tuned in to bbc1xtra
---------------------
Now playing: Alicia Keys - It's On Again (feat. Kendrick Lamar)
Tuned in to bbc6music
---------------------
Now playing: Sly & Robbie - Boops (Here To Go)
Winamp:      paused
Winamp:      stopped
Tuned in to bbc6music
---------------------
Now playing: Joanna Gruesome - Anti-Parent Cowboy Killers
Scrobbled:   Joanna Gruesome - Anti-Parent Cowboy Killers
Winamp:      paused
```

Full usage:
```
usage: bbcscrobbler.py [-h] [-i] [--ignore-itunes] [--ignore-winamp]
                       [{bbc6music,bbcradio1,bbcradio2,bbc1xtra}]

BBC Radio scrobbler. On Mac: scrobbles BBC from iTunes if it's running, or the
station of your choice if --ignore-itunes. On Windows: scrobbles BBC from
Winamp if it's running, or the station of your choice if --ignore-winamp.

positional arguments:
  {bbc6music,bbcradio1,bbcradio2,bbc1xtra}
                        BBC station to scrobble (default: bbc6music)

optional arguments:
  -h, --help            show this help message and exit
  -i, --ignore-media-player
                        Shortcut for --ignore-itunes on Mac or --ignore-winamp
                        on Windows (default: False)
  --ignore-itunes       Mac only: Ignore whatever iTunes is doing and scrobble
                        the station. For example, use this if listening via
                        web or a real radio. (default: False)
  --ignore-winamp       Windows only: Ignore whatever Winamp is doing and
                        scrobble the station. For example, use this if
                        listening via web or a real radio. (default: False)
```
