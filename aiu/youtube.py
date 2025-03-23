"""
Operations involving YouTube Music and YouTube Video links resolution to extract music, artist and album metadata.
"""
import json
import os
import re
import sys
import tempfile
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlparse

import urllib3  # noqa
import yt_dlp
from tqdm import tqdm
from ytm import utils as ytm_utils
from ytm.apis.YouTubeMusic import YouTubeMusic
from ytm.apis.YouTubeMusicDL.YouTubeMusicDL import BaseYouTubeMusicDL, YouTubeMusicDL
from ytm.parsers import artist as parse_artist
from ytm.types.ids.ArtistId import ArtistId

from aiu.config import LOGGER
from aiu.parser import fetch_image
from aiu.typedefs import Duration
from aiu.utils import FILENAME_ILLEGAL_CHARS, FILENAME_ILLEGAL_CHARS_REGEX, make_dirs_cleaned

if TYPE_CHECKING:
    from typing import (
        Dict,
        List,
        Optional,
        Tuple,
        Union,
    )

    from aiu.typedefs import JSON

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class YoutubeDLNoSanitizeFileName(yt_dlp.YoutubeDL):
    """
    Override the sanitize option to disable it.

    The default Youtube Downloader operation sanitizes additional characters of the target file name such as characters
    with accents, disallowed characters, or general ponctuation replacement (e.g.: ? -> ？). Because of this, there are
    often mismatches between its overly-sanitized name and the expected file-system-sanitized file name. Instead,
    perform the sanitization process ourselves such that only invalid characters for file-system path resolution are
    adjusted, which will match exactly with later operations retrieving the downloaded file using the same metadata.
    """

    def prepare_outtmpl(self, outtmpl, info_dict, sanitize=False):
        # type: (str, Dict[str, str], bool) -> str
        output, tmpl_info = super().prepare_outtmpl(outtmpl, info_dict, sanitize=False)  # force no sanitize
        for key in tmpl_info:
            tmpl_info[key] = re.sub(FILENAME_ILLEGAL_CHARS_REGEX, "_", tmpl_info[key])
        return output, tmpl_info


class BaseYoutubeDLP(BaseYouTubeMusicDL):
    """
    Base class of the YouTube Music downloader with drop-in replacement of :mod:`youtube_dl` by improved :mod:`yt_dlp`.
    """

    def __init__(self):
        super(BaseYoutubeDLP, self).__init__(youtube_downloader=YoutubeDLNoSanitizeFileName)

    def _get_file_path(self, info, template, directory=None):
        # type: (JSON, str, Optional[str]) -> str
        """
        Patch operations incorrectly handled when resolving downloaded music file path.

        When :meth:`BaseYouTubeMusicDL._download` is eventually called through :meth:`YouTubeMusicDL.base_download`,
        and specifically under Windows, a track with double quotes (") characters is downloaded with auto-replaced
        single quotes (') instead of the coded `illegal characters` replacement by underscores (_) as expected in
        :meth:`BaseYouTubeMusicDL._get_file_path` (same characters as in :meth:`CachedYoutubeMusicDL.cached_download`).
        Because of this, the file is not found and the download process fails the whole operation.
        Patch it transparently when this case is detected.

        Furthermore, the `template` argument that is passed contains directly the "sanitized" result instead of the
        template. Therefore, rebuild the "unsanitized" templated name with the expected format defined in the original
         :meth:`BaseYouTubeMusicDL._get_file_path` call to validate if any "technically allowed" characters under
         Windows got sanitized, causing a filename mismatch.
        """
        path = super(BaseYoutubeDLP, self)._get_file_path(info, template, directory)
        title = info.get("title", "")
        ext = os.path.splitext(path)[-1]
        templated_path = os.path.join(directory, f"{title}{ext}")
        if sys.platform == "win32" and title:
            if any(char in title for char in FILENAME_ILLEGAL_CHARS):
                for char in FILENAME_ILLEGAL_CHARS:
                    title = title.replace(char, "_")
                patched_path = os.path.join(directory, title + ext)
                if "'" in patched_path and not os.path.isfile(path) and os.path.isfile(patched_path):
                    # to avoid problems in parent code that could still be referencing the old "invalid" path
                    # move the patched file name to the expected sanitized location (don't return the patched path)
                    os.rename(patched_path, path)
                if templated_path != patched_path and os.path.isfile(templated_path):
                    os.rename(templated_path, patched_path)
                # alternate renaming case where illegal characters are removed instead of replaced by '_'
                if "_" in patched_path and not os.path.isfile(patched_path):
                    for trimmed_path in [
                        patched_path.replace("_", ""),
                        os.path.join(directory, os.path.split(patched_path)[-1].replace("_", ""))
                    ]:
                        if os.path.isfile(trimmed_path) and trimmed_path != patched_path:
                            # rename or delete if duplicated (e.g.: from following calls to AIU)
                            if os.path.isfile(patched_path):
                                os.remove(trimmed_path)
                            else:
                                os.rename(trimmed_path, patched_path)
        return path


class CachedYoutubeMusicDL(YouTubeMusicDL):
    """
    Downloader that will bypass the actual download of the file if the information and files are already available.
    """
    _api = None  # type: YouTubeMusic  # only for annotation, replaced during YouTubeMusicDL.__init__ call

    def __init__(self, *_, force_download=False, **__):
        super(CachedYoutubeMusicDL, self).__init__()
        self._base = BaseYoutubeDLP()  # drop-in replacement of YouTube downloader
        self.base_download = self._base._download
        self.force_download = force_download

    def cached_download(self, song_id, metadata=None, directory=None, **__):
        if metadata and directory and not self.force_download:
            # basic name match against various metadata fields that can have similar information
            # some fields will sometime have minimalistic name that differ slightly from the others
            sanitized_name = metadata["title"]
            for char in FILENAME_ILLEGAL_CHARS:
                sanitized_name = sanitized_name.replace(char, "_")
            candidate_names = [metadata["title"], sanitized_name]
            if "track" in metadata:
                candidate_names.append(metadata["track"])

            # common suffixes
            for suffix in [
                "(Music Video)",
                "(Official Music Video)",
            ]:
                candidate_names.extend([f"{track_name} {suffix}" for track_name in candidate_names])

            # common artist prefixes
            extra_artist_names = []
            artist_name = metadata.get("artist", "")
            if artist_name:
                for name in candidate_names:
                    extra_artist_names.append(f"{artist_name} - {name}")
            album_artist_name = metadata.get("albumartist", "")
            if album_artist_name and album_artist_name != artist_name:
                for name in candidate_names:
                    extra_artist_names.append(f"{album_artist_name} - {name}")
            candidate_names.extend(extra_artist_names)

            # common track number prefixes
            track_num = metadata.get("tracknumber")
            if track_num and str(track_num).isnumeric():
                # add common formats in case if was already downloaded + corrected
                track_num = int(track_num)
                base_names = list(candidate_names)
                for name in base_names:
                    candidate_names.extend([
                        f"{track_num:02d} {name}",
                        f"{track_num:02d}. {name}",
                        f"{track_num} {name}",
                        f"{track_num}. {name}",
                    ])
            candidate_names.extend([name.replace("_", "") for name in list(candidate_names) if "_" in name])

            # attempt match
            for name in candidate_names:
                path = os.path.join(directory, f"{name}.mp3")
                if os.path.isfile(path):
                    result = self.fetch_metadata(song_id, metadata=metadata)
                    self.log("Found already downloaded file [%s] for [%s]. "
                             "Download skipped and fetched only metadata.", path, metadata["title"])
                    return result
        return self.base_download(song_id, metadata=metadata, directory=directory, **__)

    @staticmethod
    def fetch_metadata(song_id, metadata):
        """
        Obtain the song metadata.

        Essentially redo what :meth:`YouTubeMusicDL.BaseYouTubeMusicDL._download` does, but skipping
        all operations related to the actual download and the creation of base ID3 tags from retrieved metadata
        since the file already is available. Any out of date ID3 Tags will be updated by us anyway.
        """
        ytdl = yt_dlp.YoutubeDL(params={"quiet": True, "outtmpl": "", "postprocessors": [], "format": "bestaudio"})
        url = ytm_utils.url_yt("watch", params={"v": song_id})  # noqa  # pylint: disable=not-callable
        info = ytdl.extract_info(url=url, ie_key="Youtube", download=False)

        any_title = info.get("track", info.get("title"))
        metadata = ytm_utils.filter({  # noqa  # pylint: disable=not-callable
            "title":       any_title,
            "artist":      info.get("artist"),
            "album":       info.get("album"),
            "albumartist": info.get("artist"),
            "discnumber":  "1",
            "tracknumber": "1",
            "date":        str(info.get("release_year")),
            **metadata,
        })
        return metadata

    @staticmethod
    def log(msg, *_):
        LOGGER.debug(msg, *_)


class TqdmYouTubeMusicDL(CachedYoutubeMusicDL):
    """
    Setup hooks around methods that process the `download album` operation to display progress per track downloaded.
    """

    def __init__(self, *_, **__):
        super(TqdmYouTubeMusicDL, self).__init__(*_, **__)
        self.api_album = self._api.album
        self._api.album = self.tqdm_album
        self._base._download = self.tqdm_download
        self.progress_bar = None  # type: Optional[tqdm]
        self._log_after = []

    def tqdm_album(self, album_id):
        album = self.api_album(album_id)
        total = album.get("total_tracks")
        if total:
            self.progress_bar = tqdm(
                # second line to leave space for download progress of each songs by 'yt_dlp.YoutubeDL'
                position=1, total=total, unit="track",
                desc=f"Downloading Album: [{album['name']}]"
            )
            self.progress_bar.display()
        return album

    def tqdm_download(self, *_, **__):
        result = self.cached_download(*_, **__)
        if self.progress_bar:
            self.progress_bar.update(1)
            # don't wait until class __del__ is called to avoid intermediate log entries before final output
            if self.progress_bar.last_print_n == self.progress_bar.total:
                self.progress_bar.close()
        return result

    def __del__(self):
        if self.progress_bar:
            self.progress_bar.close()
        for _log in self._log_after:
            super(TqdmYouTubeMusicDL, self).log(_log[0], *_log[1])

    # delay logs until end otherwise they break (duplicate) the progress bar display
    def log(self, msg, *_):
        self._log_after.append((msg, _))


def get_reference_id(link):
    # type: (str) -> Tuple[bool, bool, Union[str, List[str]]]
    """
    Finds the appropriate reference ID from a YouTube Music/Video link.

    :param link: URL where to look for the reference ID to extract.
    :return: tuple of (album?, music?, ID)
    """
    if not link:
        raise ValueError(f"Invalid link is undefined: [{link!s}]")
    # ignore top level domain (eg: country abbrev/.com)
    music_link = link.startswith("https://music.youtube.") or link.startswith("https://www.music.youtube.")
    video_link = link.startswith("https://youtube.") or link.startswith("https://www.youtube.")
    if not (music_link or video_link):
        raise ValueError(f"Invalid YouTube Music/Video link located at invalid host: [{link!s}]")
    query = urlparse(link).query
    params = parse_qs(query)
    # format: <youtube-link>/watch?v=<ID>
    if music_link and not any(ref in params for ref in ["v", "list"]):
        raise ValueError(f"Invalid YouTube Music link does not provide a song or album reference: [{link!s}]")
    if video_link and "v" not in params:  # ignore list (video playlist)
        raise ValueError(f"Invalid YouTube Video link does not provide a video reference: [{link!s}]")
    # format: <youtube-link>/playlist?list=<ID>
    # note: "list=<ID>" can also be in "watch?v=<ID>" format
    if music_link and "list" in params:  # process list first in case somehow both watch/list are present
        album = params["list"][0]
        LOGGER.debug("Found YouTube Music album ID: [%s]", album)
        return True, True, album
    if music_link and "v" in params:
        song = params["v"][0]
        LOGGER.debug("Found YouTube Music song ID: [%s]", song)
        return False, True, song
    video = params["v"][0]
    LOGGER.debug("Found YouTube Video song ID: [%s]", video)
    return False, False, video


def get_artist_albums(link, throw=True):
    # type: (str, bool) -> List[Dict[str, str]]
    """
    Obtains all album IDs produced by a given artist ID extracted from appropriate YouTube Music link.
    """
    try:
        parts = link.split("/channel/")
        if len(parts) != 2:
            raise ValueError(f"Not a valid channel link: [{link}]")
        artist = ArtistId(parts[1])  # raise TypeError if invalid
    except (TypeError, ValueError):
        if throw:
            raise
        return []

    # do what 'api.artist()' does but manually to handle exceptions more gracefully
    api = YouTubeMusic()
    meta = api._base.browse_artist(artist)  # pylint: disable=no-member
    data = parse_artist(meta)
    album_info = data.get("albums", {})
    if not album_info:
        name = data.get("name")
        LOGGER.warning("Artist [%s] does not have any albums listed under: [%s]", name, link)
        return []
    albums = album_info.get("items", [])

    # get the playlist ID instead of Album ID to form the corresponding download/listing YouTube Music links
    album_meta = [
        {
            "name": info["name"],
            "link": f"{parts[0]}/playlist?list={info['shuffle']['playlist_id']}",
            "id": info["shuffle"]["playlist_id"],
        }
        for info in albums
    ]
    # duplicate album names is allowed (usually duplicate uploads, contents equivalent)
    # remove them since only unique output directories can be created
    album_found = []
    album_names = set()
    for album_info in album_meta:
        if album_info["name"] in album_names:
            continue
        album_names.add(album_info["name"])
        album_found.append(album_info)
    return album_found


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
        if "album" not in song and "name" in meta:
            song["album"] = meta["name"]
        if "artist" not in song and "artists" in meta and "name" in meta["artists"][0]:
            song["artist"] = meta["artists"][0]["name"]
        if fetch_cover or not album_cover.startswith("http"):
            song["cover"] = album_cover
        if track is not None:
            track += 1

    with tempfile.NamedTemporaryFile("w", encoding="utf-8") as file:
        json.dump(meta, file, indent=4, ensure_ascii=False)
    return file.name, meta["tracks"]


def get_metadata(link):
    # type: (str) -> Tuple[Optional[str], JSON]
    _, is_music, ref_id = get_reference_id(link)
    if not is_music:
        raise ValueError(f"Cannot retrieve music metadata from YouTube Video link: [{link}]")
    LOGGER.debug("Retrieving metadata from link: [%s]", link)
    api = YouTubeMusic()
    meta = api.album(ref_id)
    if meta:
        return update_metadata(meta, fetch_cover=False)
    return None, {}


def fetch_files(link, output_dir, with_cover=True, progress_display=True, force_download=False):
    # type: (str, str, bool, bool, bool) -> Tuple[Optional[str], JSON]
    LOGGER.debug("Fetching files from link: [%s]", link)
    if progress_display:
        api = TqdmYouTubeMusicDL(force_download=force_download)
    else:
        api = CachedYoutubeMusicDL(force_download=force_download)
    is_album, is_music, ref_id = get_reference_id(link)
    make_dirs_cleaned(output_dir)
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
            covers = list(sorted(covers, key=lambda _img: _img["ratio"]))
            covers = list(filter(lambda _img: _img["ratio"] == covers[0]["ratio"], covers))
            covers = list(sorted(covers, key=lambda _img: _img["height"]))
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
