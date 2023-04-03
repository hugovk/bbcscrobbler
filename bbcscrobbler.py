#!/usr/bin/env python3
# Authors: Amr Hassan <amr.hassan@gmail.com>
# and hugovk <https://github.com/hugovk>

import argparse
import atexit
import os
import re
import shlex
import subprocess
import time
import sys
from sys import platform as _platform

import pylast
from termcolor import colored  # pip3 install termcolor

import bbcrealtime  # https://github.com/hugovk/bbc-tools

API_KEY = "8fe0d07b4879e9cd6f8d78d86a8f447c"
API_SECRET = "debb11ad5da3be07d06fddd8fe95cc42"

SESSION_KEY_FILE = os.path.join(os.path.expanduser("~"), ".session_key")
ONE_HOUR_IN_SECONDS = 60 * 60

last_output = None
pending_newline = False
playing_station = None
WM_USER = 0x400

TICK = colored("\u2713", "green")


class Escape(Exception):
    pass


def osascript(args) -> str:
    try:
        return subprocess.getoutput(args).strip()
    except Exception as e:
        return f"Error: {repr(e)}"


def normalise_station(station: str):
    if "BBC Radio 1" in station:
        station = "bbcradio1"
    elif "BBC 1Xtra" in station or "BBC Radio 1Xtra" in station:
        station = "bbc1xtra"
    elif "BBC Radio 2" in station:
        station = "bbcradio2"
    elif (
        "BBC 6Music" in station
        or "BBC 6 Music" in station
        or "6music" in station
        or "BBC Radio 6 Music" in station
    ):
        station = "bbc6music"
    return station


def is_playing_bbc(now_playing: str, player_name: str) -> bool:
    global playing_station
    if "bbc" not in now_playing.lower():
        output(player_name + ":      Not BBC")
        return False
    else:
        station = normalise_station(now_playing)
        if "bbc" in station:
            playing_station = station
        else:
            output(player_name + ":      Wrong station", "warning")
            return False
        return True
    return False


def check_apple_music(ignore: bool) -> bool:
    """
    If not Mac, return True.
    If Mac, return True if Apple Music is now playing BBC Radio
    """
    if ignore or _platform != "darwin":
        return True

    else:
        # Is Music running?
        count = int(
            osascript(
                "osascript "
                "-e 'tell application \"System Events\"' "
                "-e 'count (every process whose name is \"Music\")' "
                "-e 'end tell'"
            )
        )
        if count == 0:
            output("Music:      not running", "warning")
        else:
            # Is Music playing?
            state = osascript(
                "osascript -e 'tell application \"Music\" to player state as string'"
            )

            if state != "playing":
                output("Music:      " + state, "warning")
            else:
                # Is Music playing BBC Radio?
                now_playing = osascript(
                    "osascript "
                    "-e 'tell application \"Music\"' "
                    "-e 'set thisTitle to name of current track' "
                    "-e 'set output to thisTitle' "
                    "-e 'end tell'"
                )
                return is_playing_bbc(now_playing, "Music")

    return False


def check_winamp(ignore: bool) -> bool:
    """
    If not Windows, return True.
    If Windows, return True if Winamp is now playing BBC Radio
    """
    if ignore or _platform != "win32":
        return True

    else:
        # Is Winamp playing?
        import win32api
        import win32gui

        handle = win32gui.FindWindow("Winamp v1.x", None)
        state = win32api.SendMessage(handle, WM_USER, 0, 104)

        if state == 0:
            output("Winamp:      stopped", "warning")
        elif state == 3:
            output("Winamp:      paused", "warning")
        elif state != 1:
            output("Winamp:      unknown state " + state, "warning")
        elif state == 1:  # playing
            # Is Winamp playing BBC Radio?
            now_playing = win32gui.GetWindowText(handle)
            return is_playing_bbc(now_playing, "Winamp")

        return False


def check_media_player(ignore_apple_music: bool, ignore_winamp: bool) -> bool:
    """
    If Mac, check Apple Music.
    If Windows, check Winamp.
    Else return True.
    """
    if _platform == "darwin":
        return check_apple_music(ignore_apple_music)
    elif _platform == "win32":
        return check_winamp(ignore_winamp)
    else:
        return True


def escape_ansi(line: str) -> str:
    """Remove ANSI colour codes and formatting"""
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", line)


def update_now_playing(network, track, say_it: bool) -> None:
    if not track:
        return
    network.update_now_playing(track.artist.name, track.title, duration=duration(track))
    text = f"{track.artist} - {colored(track.title, attrs=['bold'])}"
    output(text + " ", newline=False)

    if say_it:
        say(track)


def scrobble(network, track) -> None:
    global pending_newline
    if not track:
        return
    network.scrobble(
        track.artist.name, track.title, track.start, duration=duration(track)
    )
    pending_newline = False
    print(TICK)


def print_it(text: str, newline: bool = True) -> None:
    global pending_newline
    if pending_newline:
        pending_newline = False
        print("")  # Newline

    if newline:
        pending_newline = False
        print(text)
    else:
        pending_newline = True
        print(text, end="", flush=True)


def output(text: str, type: str = None, newline: bool = True) -> None:
    global last_output
    if last_output == text:
        return
    else:
        last_output = text

    if type == "error":
        print_it(colored(text, "red"), newline)
    elif type == "warning":
        print_it(colored(text, "yellow"), newline)
    else:
        print_it(text, newline)

    # Update terminal tab
    text = escape_ansi(text)
    # Windows:
    if _platform == "win32":
        if "&" in text:
            text = text.replace("&", "^&")  # escape ampersand
        os.system("title " + text)
    # Linux or Cygwin:
    elif _platform in ["linux", "linux2", "darwin", "cygwin"]:
        text = str(text).splitlines()[0]
        if _platform == "darwin":
            text = "\033];" + text + "\007"
        else:
            text = "\x1b]2;" + text + "\x07"
        sys.stdout.write(text)
        sys.stdout.flush()


def restore_terminal_title() -> None:
    # Windows:
    if _platform == "win32":
        pass  # TODO
    # Linux, macOS or Cygwin:
    elif _platform in ["linux", "linux2", "darwin", "cygwin"]:
        # import sys

        # TODO: This isn't working in macOS/iTerm2/Zsh
        # sys.stdout.write("\e]2;\a")
        pass  # TODO


def say(thing: str) -> None:
    """Mac only: Convert text to audible speech"""
    if _platform == "darwin":
        cmd = f"say {shlex.quote(str(thing))}"
        os.system(cmd)


def duration(track) -> int:
    """Return duration in seconds"""
    return track.end - track.start


def get_now_playing_from_bbcrealtime(network, playing_station: str):
    realtime = bbcrealtime.nowplaying(playing_station)
    if realtime:
        new_track = pylast.Track(realtime["artist"], realtime["title"], network)
        new_track.start = realtime["start"]
        new_track.end = realtime["end"]
    else:
        new_track = None

    return new_track


def get_now_playing_from_lastfm(pylast_station):
    #  Get last scrobbled track, because BBC stations don't
    # usually use "now playing", but set songs as scrobbled
    # soon as they're played.
    # (But get two because sometimes there is a "now playing".)
    try:
        pylast_track = pylast_station.get_recent_tracks(2)[0]
    except pylast.WSError:
        # Operation failed - Most likely the backend service failed. Please try again.
        return None

    start = int(pylast_track.timestamp)
    new_track = pylast_track.track
    new_track.start = start
    try:
        new_track.end = start + pylast_track.track.get_duration()
    except pylast.WSError:
        # pylast.WSError: Track not found
        # Pick something reasonable
        new_track.end = start + 180

    return new_track


def get_now_playing(network, pylast_station, playing_station, scrobble_source):
    if scrobble_source == "bbcrealtime":
        return get_now_playing_from_bbcrealtime(network, playing_station)
    else:
        return get_now_playing_from_lastfm(pylast_station)


def main() -> None:
    global playing_station

    parser = argparse.ArgumentParser(
        description="BBC Radio scrobbler. "
        "On Mac: scrobbles BBC from Apple Music if it's running, "
        "or the station of your choice if --ignore-apple-music. "
        "On Windows: scrobbles BBC from Winamp if it's running, "
        "or the station of your choice if --ignore-winamp.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--ignore-media-player",
        action="store_true",
        help="Shortcut for --ignore-apple-music on Mac or --ignore-winamp on Windows",
    )
    parser.add_argument(
        "--ignore-apple-music",
        action="store_true",
        help="Mac only: Ignore whatever Apple Music is doing and scrobble the "
        "station. For example, use this if listening via web or a real "
        "radio.",
    )
    parser.add_argument(
        "--ignore-winamp",
        action="store_true",
        help="Windows only: Ignore whatever Winamp is doing and scrobble the "
        "station. For example, use this if listening via web or a real "
        "radio.",
    )
    parser.add_argument(
        "station",
        nargs="?",
        default="bbc6music",
        choices=("bbc6music", "bbcradio1", "bbcradio2", "bbc1xtra"),
        help="BBC station to scrobble",
    )
    parser.add_argument(
        "--source",
        nargs="?",
        default="lastfm",
        choices=("bbcrealtime", "lastfm"),
        help="Source to check now playing",
    )
    parser.add_argument(
        "-s", "--say", action="store_true", help="Mac only: Announcertron 4000"
    )
    args = parser.parse_args()

    atexit.register(restore_terminal_title)

    if args.ignore_media_player:
        if _platform == "darwin":
            args.ignore_apple_music = True
        elif _platform == "win32":
            args.ignore_winamp = True

    network = pylast.LastFMNetwork(API_KEY, API_SECRET)

    if not os.path.exists(SESSION_KEY_FILE):
        skg = pylast.SessionKeyGenerator(network)
        url = skg.get_web_auth_url()

        print("Please authorize the scrobbler to scrobble to your account: %s\n" % url)
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
    np_time = None
    scrobble_me_next = None
    playing_station = args.station

    try:
        while True:
            if not check_media_player(args.ignore_apple_music, args.ignore_winamp):
                last_station = None
                last_scrobbled = None
                playing_track = None
                np_time = None
                scrobble_me_next = None

            else:
                if last_station != playing_station:
                    last_station = playing_station
                    pylast_station = (
                        network.get_user(playing_station) if args.source else None
                    )

                    out = f"Tuned in to {playing_station}"
                    output(out + "\n" + "-" * len(out))
                    if args.say:
                        say(playing_station)

                try:
                    # Get now playing track
                    new_track = get_now_playing(
                        network, pylast_station, playing_station, args.source
                    )

                    if (
                        new_track
                        and (time.time() - new_track.end) > ONE_HOUR_IN_SECONDS
                    ):
                        print("Last track over an hour ago, don't scrobble")
                        raise Escape

                    # A new, different track
                    if new_track != playing_track:
                        if scrobble_me_next:
                            scrobble(network, scrobble_me_next)
                            scrobble_me_next = None
                            last_scrobbled = scrobble_me_next

                        playing_track = new_track
                        update_now_playing(network, playing_track, args.say)
                        np_time = int(time.time())

                    # Scrobblable if 30 seconds has gone by
                    else:
                        now = int(time.time())
                        if (
                            playing_track
                            and playing_track != last_scrobbled
                            and now - np_time >= 30
                        ):
                            scrobble_me_next = playing_track

                except Escape:
                    pass
                except (
                    KeyError,
                    pylast.NetworkError,
                    pylast.MalformedResponseError,
                ) as e:
                    output(f"Error: {repr(e)}", "error")

            time.sleep(15)

    except KeyboardInterrupt:
        if scrobble_me_next:
            scrobble(network, scrobble_me_next)
        print("exit")


if __name__ == "__main__":
    main()
