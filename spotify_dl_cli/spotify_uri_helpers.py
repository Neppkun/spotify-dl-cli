def spotify_url_to_uri(url: str) -> str | None:
    """Convert a Spotify open.spotify.com URL to a spotify: URI. Returns None if not a Spotify URL."""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
    except Exception:
        return None

    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc not in ("open.spotify.com", "play.spotify.com"):
        return None

    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2:
        resource_type, resource_id = parts[0], parts[1]
        if resource_type and resource_id:
            return f"spotify:{resource_type}:{resource_id}"

    return None


def normalise_spotify_input(value: str) -> str:
    """Accept either a spotify: URI or an open.spotify.com URL and return a spotify: URI."""
    if value.startswith("spotify:"):
        return value
    converted = spotify_url_to_uri(value)
    if converted:
        return converted
    return value


def parse_spotify_uri(uri: str, expected_type: str | None = None) -> tuple[str, str]:
    if not isinstance(uri, str):
        raise TypeError(f"URI must be a string, got {type(uri).__name__}")

    parts = uri.split(":")

    if len(parts) != 3:
        raise ValueError(f"Malformed Spotify URI (expected format spotify:type:id): {uri}")

    scheme, resource_type, resource_id = parts

    if scheme != "spotify":
        raise ValueError(f"Invalid URI scheme '{scheme}', expected 'spotify'")

    if not resource_type:
        raise ValueError("Spotify URI resource type is empty")

    if not resource_id:
        raise ValueError("Spotify URI resource id is empty")

    if expected_type and resource_type != expected_type:
        raise ValueError(f"Invalid resource type '{resource_type}', expected '{expected_type}'")

    return resource_type, resource_id
