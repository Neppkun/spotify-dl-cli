import logging
import re
from datetime import timedelta
from pathlib import Path

from humanize import precisedelta
from unplayplay import PLAYPLAY_TOKEN, KeyEmu

from spotify_dl_cli.audio_formats import cli_to_format
from spotify_dl_cli.clt_extended_metadata.extended_metadata_client import (
    ExtendedMetadataClient,
)
from spotify_dl_cli.clt_extended_metadata.helpers import track_gid_to_uri
from spotify_dl_cli.clt_playlist.playlist_client import PlaylistClient
from spotify_dl_cli.clt_playplay.playplay_client import PlayplayClient
from spotify_dl_cli.clt_storage_resolve.storage_resolve_client import (
    StorageResolverClient,
)
from spotify_dl_cli.collect_track_uris import resolve_track_uris
from spotify_dl_cli.config import default_tokens_path
from spotify_dl_cli.http_client.http_client import HttpClient
from spotify_dl_cli.parse_args import parse_args
from spotify_dl_cli.resolve_exe_path import bundled_dll_path
from spotify_dl_cli.service_resolver import resolve_spotify_endpoints
from spotify_dl_cli.sp_auth.constants import CLIENT_ID
from spotify_dl_cli.sp_auth.pkce import SpotifyAuthPKCE
from spotify_dl_cli.sp_downloader.apply_metadata import _download_largest_cover
from spotify_dl_cli.sp_downloader.downloader import download_track
from spotify_dl_cli.token_manager import SpotifyTokenManager

logger = logging.getLogger(__name__)

_INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1F]')


def _slugify(value: str) -> str:
    value = _INVALID_CHARS_RE.sub("", value)
    return value.strip(" ._-")


def _album_dir_name(track) -> str:
    if track.album and track.album.artist:
        artist = track.album.artist[0].name
    elif track.artist:
        artist = track.artist[0].name
    else:
        artist = "Unknown Artist"

    album = track.album.name if track.album and track.album.name else "Unknown Album"

    year = track.album.date.year if track.album and track.album.date and track.album.date.year else None

    name = f"{artist} - {album}" if not year else f"{artist} - {album} ({year})"
    return _slugify(name)


def main() -> None:
    args = parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")

    fixed_output_dir = Path(args.output_dir) if args.output_dir else None

    # OAuth 2.0 + PKCE
    auth_pkce = SpotifyAuthPKCE(
        client_id=CLIENT_ID,
        scopes=("playlist-read-private playlist-modify-private playlist-modify-public user-read-email"),
        server_port=5588,
    )

    tokens_file = default_tokens_path()
    logger.debug("Using tokens file: %s", tokens_file)

    token_manager = SpotifyTokenManager(CLIENT_ID, tokens_file, auth_pkce)

    audio_format = None if args.quality == "highest" else cli_to_format(args.quality)
    ignore_formats = {cli_to_format(f) for f in args.ignore_formats} if args.ignore_formats else None

    exe_path = bundled_dll_path()
    logger.debug("Using sp_client dll: %s", exe_path)

    keygen = KeyEmu(exe_path)
    sp_endpoints = resolve_spotify_endpoints()

    if not sp_endpoints.spclient:
        raise RuntimeError("No spclient endpoints available")

    sp_client_base = sp_endpoints.spclient[0]
    logger.debug("Using spclient endpoint: %s", sp_client_base)

    access_token = token_manager.get_access_token()

    client = HttpClient(access_token)
    metadata = ExtendedMetadataClient(sp_client_base, client)
    resolver = StorageResolverClient(sp_client_base, client)
    playplay = PlayplayClient(sp_client_base, PLAYPLAY_TOKEN, client)
    playlist_client = PlaylistClient(sp_client_base, client)

    all_track_uris = resolve_track_uris(args.uris, playlist_client, metadata)

    if not all_track_uris:
        logger.error("No tracks resolved")
        raise SystemExit(1)

    tracks = metadata.fetch_tracks(all_track_uris)

    covers_saved: set[Path] = set()

    for uri, (track, audio_files) in tracks.items():
        duration_str = precisedelta(timedelta(milliseconds=track.duration))

        logger.info("Track    : %s", track.name)
        logger.info("Artist   : %s", ", ".join(a.name for a in track.artist))
        logger.info("Album    : %s", track.album.name)
        logger.info("Duration : %s", duration_str)

        if not track.file and track.alternative:
            # Looks like a hack, but works for now ...
            logger.debug("Track has no file, using alternative with GID: %s", track.alternative[0].gid)
            track, audio_files = metadata.fetch_track(track_gid_to_uri(track.alternative[0].gid))

        if fixed_output_dir is not None:
            output_dir = fixed_output_dir
        else:
            output_dir = Path(_album_dir_name(track))

        if not output_dir.exists():
            logger.debug("Creating output directory: %s", output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        if args.include_cover:
            cover_path = output_dir / "cover.jpg"
            if cover_path not in covers_saved and not cover_path.exists():
                cover_bytes = _download_largest_cover(track, client)
                if cover_bytes:
                    cover_path.write_bytes(cover_bytes)
                    logger.info("Saved cover art : %s", cover_path)
            covers_saved.add(cover_path)

        download_track(
            client,
            output_dir,
            track,
            audio_files,
            resolver,
            playplay,
            keygen,
            audio_format,
            args.filename_template,
            ignore_formats=ignore_formats,
        )


if __name__ == "__main__":
    main()
