import argparse
import sys

from .audio_formats import CLI_FORMATS

LOG_LEVEL_CHOICES = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")


def parse_args() -> argparse.Namespace:
    deprecated_flags = {"--tracks", "--playlists"}
    used = deprecated_flags.intersection(sys.argv)

    if used:
        flags = ", ".join(sorted(used))
        raise SystemExit(
            f"{flags} is no longer supported.\nUse URIs as positional arguments:\n"
            "spotify-dl-cli spotify:track:... spotify:playlist:..."
        )

    parser = argparse.ArgumentParser()

    parser.add_argument("uris", nargs="*", help="Spotify URIs or URLs (track, album, or playlist)")

    parser.add_argument("--quality", choices=(*CLI_FORMATS, "highest"), default="ogg-vorbis-160")

    parser.add_argument(
        "--ignore-formats",
        nargs="+",
        choices=CLI_FORMATS,
        default=[],
        metavar="FORMAT",
        help="Formats to skip when using --quality highest (e.g. flac-flac-24bit mp4-flac-24bit)",
    )

    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory. Defaults to '{artist} - {album} ({year})' in the current directory.",
    )

    parser.add_argument(
        "--include-cover",
        action="store_true",
        help="Download the album cover art as cover.jpg into the output folder.",
    )

    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Open a text editor to paste multiple Spotify URLs/URIs, one per line.",
    )

    parser.add_argument("--log-level", default="INFO", choices=LOG_LEVEL_CHOICES, help="Log level")

    parser.add_argument(
        "--filename-template",
        default="{track.name}_{track.album.name}_{track.artist[0].name}",
    )

    args = parser.parse_args()

    if not args.uris and not args.bulk:
        parser.error("provide at least one URI/URL or use --bulk")

    if args.uris and args.bulk:
        parser.error("--bulk cannot be combined with positional URIs")

    if args.ignore_formats and args.quality != "highest":
        parser.error("--ignore-formats can only be used with --quality highest")

    return args
