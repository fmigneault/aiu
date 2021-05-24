import json
import tempfile
from typing import Tuple, TYPE_CHECKING
from urllib.parse import parse_qs, urlparse
from tqdm import tqdm
from ytm import YouTubeMusic, YouTubeMusicDL  # noqa

from aiu import LOGGER
from aiu.parser import fetch_image
from aiu.typedefs import Duration

if TYPE_CHECKING:
    from aiu.typedefs import JSON


class TqdmYouTubeMusicDL(YouTubeMusicDL):
    """
    Setup hooks around methods that process the `download album` operation to display progress per track downloaded.
    """
    def __init__(self, *_, **__):
        super(TqdmYouTubeMusicDL, self).__init__(*_, **__)
        self.api_album = self._api.album
        self._api.album = self.tqdm_album
        self.base_download = self._base._download
        self._base._download = self.tqdm_download
        self.pbar = None

    def tqdm_album(self, album_id):
        album = self.api_album(album_id)
        total = album.get("total_tracks")
        if total:
            self.pbar = tqdm(total=total, unit="track", desc="Downloading Album: [{}]".format(album["name"]))
        return album

    def tqdm_download(self, *_, **__):
        result = self.base_download(*_, **__)
        self.pbar.update(1)
        return result

    def download_album(self, *_, **__):
        result = super(TqdmYouTubeMusicDL, self).download_album(*_, **__)
        if self.pbar:
            self.pbar.close()
        return result


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


def update_metadata(meta, fetch_cover=False):
    # type: (JSON, bool) -> Tuple[str, JSON]
    LOGGER.debug("Updating YouTube Music album metadata")
    album_cover = meta["thumbnail"]
    album_cover = album_cover.get("path", album_cover["url"])
    for track, song in enumerate(meta["tracks"], start=1):
        song["title"] = song["name"]
        song["track"] = track
        song["duration"] = str(Duration(int(song["length"] / 1000.0)))
        song["date"] = meta["date"]
        song["year"] = meta["date"]["year"]
        song["album"] = meta["name"]
        song["artist"] = meta["artists"][0]["name"]
        if fetch_cover or not album_cover.startswith("http"):
            song["cover"] = album_cover
    with tempfile.NamedTemporaryFile("w") as file:
        json.dump(meta, file, indent=4, ensure_ascii=False)
    return file.name, meta["tracks"]


def get_metadata(link):
    # type: (str) -> Tuple[str, JSON]
    album = get_album_id(link)
    LOGGER.debug("Retrieving metadata from link: [%s]", link)
    api = YouTubeMusic()
    meta = api.album(album)
    return update_metadata(meta, fetch_cover=False)


def fetch_files(link, output_dir, with_cover=True, show_progress=True):
    # type: (str, str, bool, bool) -> Tuple[str, JSON]
    album = get_album_id(link)
    LOGGER.debug("Fetching files from link: [%s]", link)
    api = TqdmYouTubeMusicDL() if show_progress else YouTubeMusicDL()
    meta = api.download_album(album, output_dir)  # pre-applied ID3 tags
    if with_cover:
        url = meta["thumbnail"]["url"]
        path = fetch_image(url)
        meta["thumbnail"]["path"] = path
    return update_metadata(meta)
