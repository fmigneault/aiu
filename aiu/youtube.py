import json
import tempfile
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse
from tqdm import tqdm
from ytm import YouTubeMusic, YouTubeMusicDL  # noqa

from aiu import LOGGER
from aiu.parser import fetch_image
from aiu.typedefs import Duration

if TYPE_CHECKING:
    from typing import Optional, Tuple
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
        self.progress_bar = None

    def tqdm_album(self, album_id):
        album = self.api_album(album_id)
        total = album.get("total_tracks")
        if total:
            self.progress_bar = tqdm(total=total, unit="track", desc="Downloading Album: [{}]".format(album["name"]))
        return album

    def tqdm_download(self, *_, **__):
        result = self.base_download(*_, **__)
        if self.progress_bar:
            self.progress_bar.update(1)
        return result

    def __del__(self):
        if self.progress_bar:
            self.progress_bar.close()


def get_reference_id(link):
    # type: (str) -> Tuple[bool, bool, str]
    """
    Finds the appropriate reference ID from a YouTube Music/Video link.

    :param link: URL where to look for the reference ID to extract.
    :return: tuple of (album?, music?, ID)
    """
    if not link:
        raise ValueError("Invalid link is undefined: [{!s}]".format(link))
    # ignore top level domain (eg: country abbrev/.com)
    music_link = link.startswith("https://music.youtube.") or link.startswith("https://www.music.youtube.")
    video_link = link.startswith("https://youtube.") or link.startswith("https://www.youtube.")
    if not (music_link or video_link):
        raise ValueError("Invalid YouTube Music/Video link located at invalid host: [{!s}]".format(link))
    query = urlparse(link).query
    params = parse_qs(query)
    if music_link and not any(ref in params for ref in ["v", "list"]):
        raise ValueError("Invalid YouTube Music link does not provide a song or album reference: [{!s}]".format(link))
    elif video_link and "v" not in params:  # ignore list (video playlist)
        raise ValueError("Invalid YouTube Video link does not provide a video reference: [{!s}]".format(link))
    if music_link and "list" in params:  # process list first in case somehow both watch/list are present
        album = params["list"][0]
        LOGGER.debug("Found YouTube Music album ID: [%s]", album)
        return True, True, album
    elif music_link and "v" in params:
        song = params["v"][0]
        LOGGER.debug("Found YouTube Music song ID: [%s]", song)
        return False, True, song
    video = params["v"][0]
    LOGGER.debug("Found YouTube Video song ID: [%s]", video)
    return False, False, video


def update_metadata(meta, fetch_cover=False):
    # type: (JSON, bool) -> Tuple[Optional[str], JSON]
    """
    Update tracks metadata for formats and field names expected for later ID3 processing.
    """
    track = 1
    if "tracks" not in meta:  # missing or single
        LOGGER.debug("Single file metadata update detected.")
        track = None
        meta["tracks"] = [dict(meta)]  # avoid circular reference

    LOGGER.debug("Updating YouTube Music/Video metadata for Single/Album")
    album_cover = meta["thumbnail"]
    album_cover = album_cover.get("path", album_cover["url"])
    for song in meta["tracks"]:
        # find best possible song name
        if "name" in song:
            song["title"] = song["name"]
        elif "track" in song and isinstance(song["track"], str):
            song["title"] = song["track"]
        elif "alt_title" in song:
            song["title"] = song["alt_title"]
        # else: track could already be defined, but not guaranteed to be pretty (eg: video title)

        song["track"] = track
        if "duration" not in song and "length" in song:
            song["duration"] = str(Duration(int(song["length"] / 1000.0)))
        if "date" not in meta:
            if "upload_date" in song:
                year = song["upload_date"][:4]
                month = song["upload_date"][4:6]
                day = song["upload_date"][6:8]
                song["date"] = {"year": year, "month": month, "day": day}
                song["year"] = year
        else:
            song["date"] = meta["date"]
            song["year"] = meta["date"]["year"]
        if "album" not in song:
            song["album"] = meta["name"]
        if "artist" not in song and "artists" in meta:
            song["artist"] = meta["artists"][0]["name"]
        if fetch_cover or not album_cover.startswith("http"):
            song["cover"] = album_cover
        if track is not None:
            track += 1

    with tempfile.NamedTemporaryFile("w") as file:
        json.dump(meta, file, indent=4, ensure_ascii=False)
    return file.name, meta["tracks"]


def get_metadata(link):
    # type: (str) -> Tuple[Optional[str], JSON]
    is_album, is_music, ref_id = get_reference_id(link)
    if not is_music:
        raise ValueError("Cannot retrieve music metadata from YouTube Video link: [%s]", link)
    LOGGER.debug("Retrieving metadata from link: [%s]", link)
    api = YouTubeMusic()
    meta = api.album(ref_id)
    if meta:
        return update_metadata(meta, fetch_cover=False)
    return None, {}


def fetch_files(link, output_dir, with_cover=True, show_progress=True):
    # type: (str, str, bool, bool) -> Tuple[Optional[str], JSON]
    LOGGER.debug("Fetching files from link: [%s]", link)
    api = TqdmYouTubeMusicDL() if show_progress else YouTubeMusicDL()
    is_album, is_music, ref_id = get_reference_id(link)
    if is_album and is_music:
        meta = api.download_album(ref_id, output_dir)  # pre-applied ID3 tags
    else:  # any single music/video
        meta = api.download_song(ref_id, output_dir)
    if with_cover and ("thumbnail" in meta or "thumbnails" in meta):
        if "thumbnail" in meta:
            thumbnail = meta["thumbnail"]
        else:
            # pick squarest and largest thumbnail if many are available but not one was pre-selected
            #   closest to 0 with |w/h - 1| will be the squarest
            #   in case of equivalent ratios, pick by height to favor larger images
            covers = meta["thumbnails"]
            for img in covers:
                img["ratio"] = abs((float(img["width"]) / float(img["height"])) - 1)
            covers = list(sorted(covers, key=lambda img: img["ratio"]))
            covers = list(filter(lambda img: img["ratio"] == covers[0]["ratio"], covers))
            covers = list(sorted(covers, key=lambda img: img["height"]))
            thumbnail = covers[0]
        if isinstance(thumbnail, dict):
            url = thumbnail["url"]
            path = fetch_image(url)
            meta.setdefault("thumbnail", {})
            meta["thumbnail"]["path"] = path
        else:
            url = meta["thumbnail"]
            path = fetch_image(url)
            meta["thumbnail"] = {"url": url, "path": path}
    if meta:  # video could return empty
        return update_metadata(meta)
    return None, {}
