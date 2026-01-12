#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pylast>=7",
#     "termcolor",
# ]
# ///
# Authors: Amr Hassan <amr.hassan@gmail.com>
# and hugovk <https://github.com/hugovk>

from __future__ import annotations

import argparse
import atexit
import os
import re
import shlex
import subprocess
import sys
import time
from functools import cache, partial
from pathlib import Path
from sys import platform as _platform

import pylast  # pip install pylast>=7
from termcolor import colored  # pip install termcolor

API_KEY = "8fe0d07b4879e9cd6f8d78d86a8f447c"
API_SECRET = "debb11ad5da3be07d06fddd8fe95cc42"

SESSION_KEY_FILE = os.path.join(os.path.expanduser("~"), ".session_key.bbcscrobbler")
ONE_HOUR_IN_SECONDS = 60 * 60

last_output = None
pending_newline = False
playing_station = None
WM_USER = 0x400

ANSI_ESCAPE = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
TICK = colored("\u2713", "green")
bold = partial(colored, attrs=["bold"])


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


def apple_music_playing() -> bool:
    """
    Return True if Apple Music is now playing BBC Radio
    """
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
        output("Music:      " + bold("not running"), "warning")
        return False

    # Is Music playing?
    state = osascript(
        "osascript -e 'tell application \"Music\" to player state as string'"
    )
    if state != "playing":
        output("Music:      " + bold(state), "warning")
        return False

    # Is Music playing BBC Radio?
    now_playing = osascript(
        "osascript "
        "-e 'tell application \"Music\"' "
        "-e 'set thisTitle to name of current track' "
        "-e 'set output to thisTitle' "
        "-e 'end tell'"
    )
    return is_playing_bbc(now_playing, "Music")


def winamp_playing() -> bool:
    """
    If not Windows, return True.
    If Windows, return True if Winamp is now playing BBC Radio
    """
    # Is Winamp playing?
    import win32api
    import win32gui

    handle = win32gui.FindWindow("Winamp v1.x", None)
    state = win32api.SendMessage(handle, WM_USER, 0, 104)

    if state == 0:
        output(f"Winamp:      {bold('stopped')}", "warning")
        return False
    elif state == 3:
        output(f"Winamp:      {bold('paused')}", "warning")
        return False
    elif state != 1:
        output(f"Winamp:      {bold(f'unknown state {state}')}", "warning")
        return False
    else:
        # Is Winamp playing BBC Radio?
        now_playing = win32gui.GetWindowText(handle)
        return is_playing_bbc(now_playing, "Winamp")


def bbc_playing(ignore: bool) -> bool:
    """
    If ignore=True, return True.
    If macOS, check Apple Music.
    If Windows, check Winamp.
    Else return True.
    """
    if ignore:
        return True
    elif _platform == "darwin":
        return apple_music_playing()
    elif _platform == "win32":
        return winamp_playing()
    else:
        return True


@cache
def escape_ansi(line: str) -> str:
    """Remove ANSI colour codes and formatting"""
    return ANSI_ESCAPE.sub("", line)


def update_now_playing(
    network: pylast.LastFMNetwork, track: pylast.Track | None, say_it: bool
) -> None:
    if not track:
        return
    network.update_now_playing(track.artist.name, track.title, duration=duration(track))
    text = f"{track.artist} - {bold(track.title)}"
    output(text + " ", newline=False)

    if say_it:
        say(track)


def scrobble(network: pylast.LastFMNetwork, track: pylast.Track | None) -> None:
    global pending_newline
    if not track:
        return
    network.scrobble(
        track.artist.name,
        track.title,
        track.start,
        duration=duration(track),
        chosen_by_user=False,
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


def output(text: str, level: str = None, newline: bool = True) -> None:
    global last_output
    if last_output == text:
        return
    else:
        last_output = text

    if level == "error":
        print_it(colored(text, "red"), newline)
    elif level == "warning":
        print_it(colored(text, "yellow"), newline)
    else:
        print_it(text, newline)

    # Update terminal tab
    text = text.splitlines()[0]  # Keep only first line, no underlines
    text = " ".join(text.split())  # Remove duplicate whitespace
    text = escape_ansi(text)  # Remove colour codes

    # Windows:
    if _platform == "win32":
        if "&" in text:
            text = text.replace("&", "^&")  # escape ampersand
        os.system("title " + text)
    # Linux or Cygwin:
    elif _platform in ["linux", "linux2", "darwin", "cygwin"]:
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


def duration(track: pylast.Track) -> int:
    """Return duration in seconds"""
    return track.end - track.start


def get_now_playing(pylast_station: pylast.User) -> pylast.Track | None:
    #  Get last scrobbled track, because BBC stations don't
    # usually use "now playing", but set songs as scrobbled
    # soon as they're played.
    # (But get two because sometimes there is a "now playing".)
    try:
        pylast_track = pylast_station.get_recent_tracks(2)[0]
    except (
        IndexError,
        pylast.MalformedResponseError,
        pylast.NetworkError,
        pylast.PyLastError,
        pylast.WSError,
    ):
        # NetworkError: [Errno 8] nodename nor servname provided, or not known
        # Malformed response from Last.fm. Underlying error:
        #   Connection to the API failed with HTTP code 500
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


def main() -> None:
    global playing_station

    parser = argparse.ArgumentParser(
        description="BBC Radio scrobbler. "
        "Scrobbles from Apple Music (macOS) or Winamp (Windows) if it's running. "
        "Or the station of your choice with `--ignore-media-player`.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i",
        "--ignore-media-player",
        action="store_true",
        help="Ignore whatever Apple Music (macOS) and Winamp (Windows) "
        "is doing and scrobble the station. "
        "For example, use this if listening via web or a real radio.",
    )
    parser.add_argument(
        "--ignore-apple-music",
        action="store_true",
        help="Deprecated, use --ignore-media-player instead.",
        deprecated=True,
    )
    parser.add_argument(
        "--ignore-winamp",
        action="store_true",
        help="Deprecated, use --ignore-media-player instead.",
        deprecated=True,
    )
    parser.add_argument(
        "station",
        nargs="?",
        default="bbc6music",
        choices=("bbc6music", "bbcradio1", "bbcradio2", "bbc1xtra"),
        help="BBC station to scrobble",
    )
    parser.add_argument(
        "-s", "--say", action="store_true", help="Mac only: Announcertron 4000"
    )
    args = parser.parse_args()

    atexit.register(restore_terminal_title)

    if args.ignore_apple_music or args.ignore_winamp:
        args.ignore_media_player = True
        del args.ignore_apple_music
        del args.ignore_winamp

    network = pylast.LastFMNetwork(API_KEY, API_SECRET)

    if not os.path.exists(SESSION_KEY_FILE):
        skg = pylast.SessionKeyGenerator(network)
        url = skg.get_web_auth_url()

        print(f"Please authorize the scrobbler to scrobble to your account: {url}\n")
        import webbrowser

        webbrowser.open(url)

        while True:
            try:
                session_key = skg.get_web_auth_session_key(url)
                Path(SESSION_KEY_FILE).write_text(session_key)
                break
            except pylast.WSError:
                time.sleep(1)
    else:
        session_key = Path(SESSION_KEY_FILE).read_text()

    network.session_key = session_key

    last_station = None
    last_scrobbled = None
    playing_track = None
    np_time = None
    scrobble_me_next = None
    playing_station = args.station

    try:
        while True:
            if not bbc_playing(args.ignore_media_player):
                last_station = None
                last_scrobbled = None
                playing_track = None
                np_time = None
                scrobble_me_next = None

            else:
                if last_station != playing_station:
                    last_station = playing_station
                    pylast_station = network.get_user(playing_station)

                    out = f"Tuned in to {bold(playing_station)}"
                    output(out + "\n" + "-" * len(escape_ansi(out)))
                    if args.say:
                        say(playing_station)

                try:
                    # Get now playing track
                    new_track = get_now_playing(pylast_station)

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
                            and np_time
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
                    pylast.WSError,
                ) as e:
                    output(f"Error: {e}", "error")

            time.sleep(15)

    except KeyboardInterrupt:
        if scrobble_me_next:
            scrobble(network, scrobble_me_next)
        print("exit")


if __name__ == "__main__":
    main()
