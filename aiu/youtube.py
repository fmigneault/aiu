import io
import json
import os
import requests
import tempfile
from typing import Tuple, TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

from PIL import Image
from ytm import YouTubeMusic, YouTubeMusicDL  # noqa

from aiu import LOGGER
from aiu.typedefs import Duration

if TYPE_CHECKING:
    from aiu.typedefs import JSON


def get_album_id(link):
    # type: (str) -> str
    if not link or "music.youtube.com" not in link:
        raise ValueError("Invalid Youtube Music link located at invalid host: [%s]", link)
    if "list=" not in link:
        raise ValueError("Invalid Youtube Music link missing list reference: [%s]", link)
    query = urlparse(link).query
    album = parse_qs(query)["list"][0]
    LOGGER.debug("Found album ID: [%s]", album)
    return album


def update_metadata(meta):
    # type: (JSON) -> Tuple[str, JSON]
    LOGGER.debug("Updating YouTube Music album metadata")
    album_cover = meta["thumbnail"]
    album_cover = album_cover.get("path", album_cover["url"])
    for track, song in enumerate(meta["tracks"], start=1):
        song["title"] = song["name"]
        song["track"] = track
        song["duration"] = str(Duration(int(song["length"] / 1000.0)))
        song["cover"] = album_cover
        song["date"] = meta["date"]
        song["year"] = meta["date"]["year"]
        song["album"] = meta["name"]
        song["artist"] = meta["artists"][0]["name"]
    with tempfile.NamedTemporaryFile("w") as file:
        json.dump(meta, file, indent=4, ensure_ascii=False)
    return file.name, meta["tracks"]


def get_metadata(link):
    # type: (str) -> Tuple[str, JSON]
    album = get_album_id(link)
    LOGGER.debug("Retrieving metadata from link: [%s]", link)
    api = YouTubeMusic()
    meta = api.album(album)
    return update_metadata(meta)


def fetch_files(link, output_dir, with_cover=True):
    # type: (str, str, bool) -> Tuple[str, JSON]
    album = get_album_id(link)
    LOGGER.debug("Fetching files from link: [%s]", link)
    api = YouTubeMusicDL()
    meta = api.download_album(album, output_dir)  # pre-applied ID3 tags
    if with_cover:
        url = meta["thumbnail"]["url"]
        path = os.path.join(output_dir, "cover.png")
        resp = requests.get(url)
        buffer = io.BytesIO(resp.content)
        image = Image.open(buffer)
        image.save(path, format="PNG")
        meta["thumbnail"]["path"] = path
    return update_metadata(meta)
