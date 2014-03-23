#! /usr/bin/python
# Author: Amr Hassan <amr.hassan@gmail.com>

# Enable (uncomment) one of these radio stations
STATION = "bbc6music"
#STATION = "bbcradio1"
#STATION = "bbcradio2"
#STATION = "bbc1xtra"


# Do not edit anything below this line

import os
import pylast
from sys import platform as _platform
import time

API_KEY = "8fe0d07b4879e9cd6f8d78d86a8f447c"
API_SECRET = "debb11ad5da3be07d06fddd8fe95cc42"

SESSION_KEY_FILE = "/Users/hugo/Dropbox/bin/data/.session_key"

network = pylast.LastFMNetwork(API_KEY, API_SECRET)
station = network.get_user(STATION)

ONE_DAY_IN_SECONDS = 60*60*24


class escape (Exception):
    pass


def scrobble(track):
    network.scrobble(
        track.track.artist.name,
        track.track.title,
        track.timestamp,
        duration=str(duration(track)))
    output("Scrobbled: %s" % playing_track.track)
    playing_track_scrobbled = True
    return playing_track_scrobbled


def output(text):
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

output("Tuned in to %s\n---------------------" % STATION)

playing_track = None
playing_track_scrobbled = False
while True:

    try:
        new_track = station.get_recent_tracks(1)[0]

        if (time.time() - int(new_track.timestamp)) > ONE_DAY_IN_SECONDS:
            print "Last track over a day ago, don't scrobble"
            raise escape

        if new_track != playing_track:

            if playing_track and not playing_track_scrobbled:
                playing_track_scrobbled = scrobble(playing_track)

            network.update_now_playing(
                new_track.track.artist.name,
                new_track.track.title, duration=str(duration(new_track)))
            output("Now playing: %s" % new_track.track)

            playing_track = new_track
            playing_track_scrobbled = False

        if playing_track \
                and not playing_track_scrobbled \
                and (time.time() - int(playing_track.timestamp)) \
                >= duration(playing_track)/2:
            playing_track_scrobbled = scrobble(playing_track)

    except escape:
        pass
    except Exception as e:
        print ("Error: %s" % repr(e))

    time.sleep(30)

# End of file
