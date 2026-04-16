# spotify-dl-cli

`spotify-dl-cli` is a proof-of-concept command-line project exploring reverse engineering techniques on a proprietary desktop client.

The project demonstrates how native routines embedded in a protected Windows application can be analyzed and executed through CPU emulation to understand parts of a media delivery workflow.

> [!CAUTION]
High risk of being banned: use a different account


> [!WARNING]
This project is **not functional out of the box**. Some required components cannot be included due to legal restrictions. It is provided **for exploration and educational purposes only**.

**Key generator has been migrated to another repository** \
https://github.com/cycyrild/another-unplayplay

## Latest improvements
Changes
* Bypass of Spotify Plaplay custom cipher
* Removed full cipher derivation pipeline (derivedKey -> state -> generate_keystream)
* Direct capture of native AES decryption key

Benefits
* Significantly faster decryption
* Eliminates 16-byte keystream generation loop
* Generated AES keys remain valid across Playplay DRM changes (unless CDN encryption is modified)

**NOTE:** Playplay 5 uses a virtual machine driven by MSVC C++ exceptions. A minimal Python SEH dispatcher was implemented to emulate `_CxxThrowException`.


<sub>Discord: cyril13600</sub>
![](image.png)

## Usage

```
spotify-dl-cli <URI> [URI ...] [OPTIONS]
```

### Positional arguments

| Argument | Description |
|----------|-------------|
| `uris` | One or more Spotify URIs to download. Supports tracks, playlists, and albums. |

**Supported URI types:**
- `spotify:track:<id>` — single track
- `spotify:playlist:<id>` — all tracks in a playlist
- `spotify:album:<id>` — all tracks in an album

**Example:**
```
spotify-dl-cli spotify:track:4iV5W9uYEdYUVa79Axb7Rh spotify:album:1DFixLWuPkv3KT3TnV35m3
```

---

### `--quality`

Selects the audio format/quality to download.

| Value | Description |
|-------|-------------|
| `ogg-vorbis-96` | OGG Vorbis 96 kbps |
| `ogg-vorbis-160` | OGG Vorbis 160 kbps *(default)* |
| `ogg-vorbis-320` | OGG Vorbis 320 kbps |
| `flac-flac` | FLAC lossless |
| `flac-flac-24bit` | FLAC lossless 24-bit |
| `mp4-flac` | MP4 container, FLAC audio |
| `mp4-flac-24bit` | MP4 container, FLAC 24-bit audio |
| `highest` | Automatically pick the best available format |

When `highest` is used, the priority order is:
`flac-flac-24bit` > `mp4-flac-24bit` > `flac-flac` > `mp4-flac` > `ogg-vorbis-320` > `ogg-vorbis-160` > `ogg-vorbis-96`

If a track doesn't have the requested format available, it is skipped.

```
spotify-dl-cli spotify:track:... --quality ogg-vorbis-320
spotify-dl-cli spotify:track:... --quality highest
```

---

### `--ignore-formats`

Excludes one or more formats from consideration when using `--quality highest`. Accepts one or more format names (same values as `--quality`, excluding `highest`). Cannot be used without `--quality highest`.

```
spotify-dl-cli spotify:album:... --quality highest --ignore-formats flac-flac-24bit mp4-flac-24bit
```

---

### `--output-dir`

Sets the output directory for downloaded files. If omitted, files are saved into a per-album subfolder named `{Artist} - {Album} ({Year})` in the current working directory.

```
spotify-dl-cli spotify:track:... --output-dir ./my-music
```

---

### `--include-cover`

Downloads the album cover art as `cover.jpg` into the output folder. If `cover.jpg` already exists, it is not re-downloaded.

```
spotify-dl-cli spotify:album:... --include-cover
```

---

### `--filename-template`

Controls the output filename (without extension) for each downloaded track. Expressions in `{...}` are resolved against the track's metadata.

**Default:** `{track.name}_{track.album.name}_{track.artist[0].name}`

**Available fields (all prefixed with `track.`):**

| Expression | Description |
|------------|-------------|
| `{track.name}` | Track title |
| `{track.album.name}` | Album name |
| `{track.artist[0].name}` | First artist name |
| `{track.album.artist[0].name}` | First album artist name |
| `{track.disc_number}` | Disc number |
| `{track.number}` | Track number |
| `{track.album.date.year}` | Release year |

Characters that are invalid in filenames are stripped automatically.

```
spotify-dl-cli spotify:album:... --filename-template "{track.number}_{track.name}"
```

---

### `--log-level`

Sets the verbosity of log output. Default: `INFO`.

| Value | Description |
|-------|-------------|
| `DEBUG` | Verbose: file IDs, keys, internal state |
| `INFO` | Standard progress output *(default)* |
| `WARNING` | Only warnings and errors |
| `ERROR` | Only errors |
| `CRITICAL` | Only critical failures |

```
spotify-dl-cli spotify:track:... --log-level DEBUG
```

---

## How it works (very, very quickly ...)

Instead of reproducing Spotify’s Playplay cipher, the emulator executes the native Playplay routine and **captures the final AES key directly in memory**.

Process:

1. Run Playplay VM initialization
2. Call `vm_object_transform` with `content_id` + `obfuscated_key`
3. Hook the AES key generation point
4. Capture the **runtime-generated AES-CTR key**
5. Decrypt audio directly using native AES-CTR

## Legal Notice

This project is provided for educational, interoperability, and security research purposes only.

You are solely responsible for how you use this software and for complying with all applicable laws, regulations, and contracts in your jurisdiction. This includes copyright and anti-circumvention laws, and Spotify's terms and policies.

You must not use this project to infringe copyright, violate platform terms, bypass access controls unlawfully, or facilitate unauthorized copying/ripping/distribution of content.

This project is not affiliated with, endorsed by, or sponsored by Spotify. "Spotify" and related marks are the property of their respective owners.

If you are a rights holder and believe material in this repository infringes your rights, please contact the maintainers for prompt review/removal.

This software is provided "AS IS", without warranty of any kind, express or implied. The maintainers disclaim liability for misuse or damages arising from use of this project.

> This notice is not legal advice.
