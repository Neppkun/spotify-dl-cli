import logging
from collections.abc import Iterable

from spotify_dl_cli.clt_extended_metadata.extended_metadata_client import ExtendedMetadataClient
from spotify_dl_cli.clt_playlist.playlist_client import PlaylistClient
from spotify_dl_cli.spotify_uri_helpers import normalise_spotify_input, parse_spotify_uri

logger = logging.getLogger(__name__)


def resolve_track_uris(
    uris: Iterable[str],
    playlist_client: PlaylistClient,
    metadata_client: ExtendedMetadataClient,
) -> set[str]:
    all_track_uris: set[str] = set()

    for raw in uris:
        uri = normalise_spotify_input(raw)
        try:
            resource_type, _ = parse_spotify_uri(uri)
        except (TypeError, ValueError) as e:
            logger.error("Invalid URI: %s (%s)", raw, e)
            continue

        if resource_type == "track":
            all_track_uris.add(uri)

        elif resource_type == "playlist":
            logger.info("Fetching playlist: %s", uri)
            playlist_uris = playlist_client.fetch_all_track_uris(uri)
            logger.info("Found %d tracks", len(playlist_uris))
            all_track_uris.update(playlist_uris)

        elif resource_type == "album":
            logger.info("Fetching album: %s", uri)
            album_track_uris = metadata_client.fetch_album_track_uris(uri)
            logger.info("Found %d tracks", len(album_track_uris))
            all_track_uris.update(album_track_uris)

        else:
            logger.warning("Unsupported Spotify resource type: %s", resource_type)

    return all_track_uris
