# bbcscrobbler

[![Lint](https://github.com/hugovk/bbcscrobbler/actions/workflows/lint.yml/badge.svg)](https://github.com/hugovk/bbcscrobbler/actions/workflows/lint.yml)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: Black](https://img.shields.io/badge/code%20style-Black-000000.svg)](https://github.com/psf/black)

A script to scrobble BBC Radio music to your Last.fm profile by copying scrobbles from
the BBC radio accounts at Last.fm.

Forget to stop the scrobbler running when stopping the radio and leaving the computer?
Not to worry, bbcscrobbler.py only scrobbles when Apple Music or Winamp is playing BBC
radio.

Basic use:

```sh
uv run bbcscrobbler.py
# or
pip install -r requirements.txt
bbcscrobbler.py
```

Want to ignore Apple Music/Winamp and scrobble via the web or from a real radio?
Defaults to BBC 6 Music:

```sh
bbcscrobbler.py --ignore-media-player
```

Or ignore Apple Music/Winamp and scrobble a named station
([bbcradio1](https://www.last.fm/user/bbcradio1),
[bbc1xtra](https://www.last.fm/user/bbc1xtra),
[bbcradio2](https://www.last.fm/user/bbcradio2) or
[bbc6music](https://www.last.fm/user/bbc6music)):

```sh
bbcscrobbler.py bbc1xtra --ignore-media-player
```

Example output:

```console
> bbcscrobbler.py
Tuned in to bbc6music
---------------------
Annie Eve - Shuffle ✓
Nightmares on Wax - Les Nuits ✓
Black Rebel Motorcycle Club - Spread Your Love ✓
Cate le Bon - Sisters ✓
Grace Jones - I've Seen That Face Before (Libertango) ✓
Sly & Robbie - Boops (Here To Go)
Tuned in to bbcradio1
---------------------
Klingande - Jubel
Tuned in to bbcradio2
---------------------
Prince & The Revolution - Let's Go Crazy
Winamp:      Wrong station
Tuned in to bbc1xtra
---------------------
Alicia Keys - It's On Again (feat. Kendrick Lamar)
Tuned in to bbc6music
---------------------
Sly & Robbie - Boops (Here To Go)
Winamp:      paused
Winamp:      stopped
Tuned in to bbc6music
---------------------
Joanna Gruesome - Anti-Parent Cowboy Killers ✓
Winamp:      paused
```

Full usage:

```
usage: bbcscrobbler.py [-h] [-i] [--ignore-apple-music] [--ignore-winamp] [-s]
                       [{bbc6music,bbcradio1,bbcradio2,bbc1xtra}]

BBC Radio scrobbler. Scrobbles from Apple Music (macOS) or Winamp (Windows) if
it's running. Or the station of your choice with `--ignore-media-player`.

positional arguments:
  {bbc6music,bbcradio1,bbcradio2,bbc1xtra}
                        BBC station to scrobble (default: bbc6music)

options:
  -h, --help            show this help message and exit
  -i, --ignore-media-player
                        Ignore whatever Apple Music (macOS) and Winamp
                        (Windows) is doing and scrobble the station. For
                        example, use this if listening via web or a real radio.
                        (default: False)
  --ignore-apple-music  Deprecated, use --ignore-media-player instead.
                        (default: False)
  --ignore-winamp       Deprecated, use --ignore-media-player instead.
                        (default: False)
  -s, --say             Mac only: Announcertron 4000 (default: False)
```
