#!/usr/bin/env python
# Author: Amr Hassan <amr.hassan@gmail.com>

import argparse
import os
import pylast
from sys import platform as _platform
import subprocess
import time

API_KEY = "8fe0d07b4879e9cd6f8d78d86a8f447c"
API_SECRET = "debb11ad5da3be07d06fddd8fe95cc42"

SESSION_KEY_FILE = os.path.join(os.path.expanduser("~"), ".session_key")
ONE_DAY_IN_SECONDS = 60*60*24

last_output = None


class escape (Exception):
    pass


def osascript(args):
    return subprocess.check_output(args).strip()


def check_itunes():
    """
    If not Mac, return True.
    If Mac, return True if iTunes is now playing BBC Radio
    """
    if args.ignore_itunes or _platform != "darwin":
        return True

    else:

        # Is iTunes running?
        count = int(osascript([
            "osascript",
            "-e", "tell application \"System Events\"",
            "-e", "count (every process whose name is \"iTunes\")",
            "-e", "end tell"]))
        if count == 0:
            output("iTunes:      not running")
        else:

            # Is iTunes playing?
            state = osascript([
                "osascript",
                "-e", "tell application \"iTunes\" to player state as string"
                ])

            if state != "playing":
                output("iTunes:      " + state)
            else:

                # Is iTunes playing BBC Radio?
                now_playing = osascript([
                    "osascript",
                    "-e", "tell application \"iTunes\"",
                    "-e", "set thisTitle to name of current track",
                    "-e", "set output to thisTitle",
                    "-e", "end tell"])
                if "BBC Radio" not in now_playing:
                    output("iTunes:      Not BBC")
                else:
                    if "BBC Radio 1" in now_playing:
                        args.station == "bbcradio1"
                    elif "BBC Radio 1Xtra" in now_playing:
                        args.station == "bbc1xtra"
                    elif "BBC Radio 2" in now_playing:
                        args.station == "bbcradio2"
                    elif "BBC Radio 6 Music" in now_playing:
                        args.station == "bbc6music"
                    else:
                        output("iTunes:      Wrong station")
                        return False
                    return True

    return False


def update_now_playing(track):
    network.update_now_playing(
        new_track.track.artist.name,
        new_track.track.title,
        duration=str(duration(new_track)))
    output("Now playing: %s" % new_track.track)


def scrobble(track):
    network.scrobble(
        track.track.artist.name,
        track.track.title,
        track.timestamp,
        duration=str(duration(track)))
    output("Scrobbled:   %s" % playing_track.track)
    playing_track_scrobbled = True
    return playing_track_scrobbled


def output(text):
    global last_output
    if last_output == text:
        return
    else:
        last_output = text
    print(text)
    # Windows:
    if _platform == "win32":
        if "&" in text:
            text.replace("&", "^&")  # escape ampersand
        os.system("title " + text)
    # Linux, OS X or Cygwin:
    elif _platform in ["linux", "linux2", "darwin", "cygwin"]:
        import sys
        sys.stdout.write("\x1b]2;" + text + "\x07")


def duration(track):
    return int(track.track.get_duration())/1000


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="BBC Radio scrobbler. "
        "On Mac: scrobbles BBC from iTunes if it's running, "
        "or the station of your choice if --ignore-itunes. "
        "On Windows, scrobbles your choice.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--ignore-itunes',  action='store_true',
        help='Mac only: Ignore whatever iTunes is doing and scrobble the '
        'station. For example, use this if listening via web or a real '
        'radio.')
    parser.add_argument(
        'station',  nargs='?', default='bbc6music',
        choices=('bbc6music', 'bbcradio1', 'bbcradio2', 'bbc1xtra'),
        help='BBC station to scrobble')
    args = parser.parse_args()

    network = pylast.LastFMNetwork(API_KEY, API_SECRET)

    if not os.path.exists(SESSION_KEY_FILE):
        skg = pylast.SessionKeyGenerator(network)
        url = skg.get_web_auth_url()

        print(
            "Please authorize the scrobbler "
            "to scrobble to your account: %s\n" % url)
        import webbrowser
        webbrowser.open(url)

        while True:
            try:
                session_key = skg.get_web_auth_session_key(url)
                fp = open(SESSION_KEY_FILE, "w")
                fp.write(session_key)
                fp.close()
                break
            except pylast.WSError:
                time.sleep(1)
    else:
        session_key = open(SESSION_KEY_FILE).read()

    network.session_key = session_key

    last_station = None
    last_scrobbled = None
    playing_track = None
    playing_track_scrobbled = False
    np_time = None
    while True:

        if not check_itunes():

            last_station = None
            last_scrobbled = None
            playing_track = None
            playing_track_scrobbled = False

        else:

            if last_station != args.station:
                last_station = args.station
                station = network.get_user(args.station)
                output("Tuned in to %s\n---------------------" % args.station)

            try:
                new_track = station.get_recent_tracks(1)[0]

                if (time.time() - int(new_track.timestamp)) > \
                        ONE_DAY_IN_SECONDS:
                    print "Last track over a day ago, don't scrobble"
                    raise escape

                # A new, different track
                if new_track != playing_track:

                    playing_track = new_track
                    playing_track_scrobbled = False
                    update_now_playing(playing_track)
                    np_time = int(time.time())

                # Scrobble it if 30 seconds has gone by
                else:
                    now = int(time.time())
                    if playing_track \
                        and now - np_time >= 30 \
                        and not playing_track_scrobbled \
                        and (time.time() - int(playing_track.timestamp)) \
                            >= duration(playing_track)/2:
                        playing_track_scrobbled = scrobble(playing_track)

            except escape:
                pass
            except Exception as e:
                print("Error: %s" % repr(e))

        time.sleep(15)


# End of file
