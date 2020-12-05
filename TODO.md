# TODOs

Various things that remain to be done but planned.

Reference: https://readthedocs.org/projects/eyed3/downloads/pdf/latest/


1. apply album cover, working command as follows: 
	```
	eyeD3 --force-update --remove-all-images --add-image "cover.jpg:FRONT_COVER" <directory>
	```
	
	maybe use `<CONDA_ENV>/Lib/site-packages/eyed3/plugins/art.py` 
	or basic CLI `<CONDA_ENV>/Lib/site-packages/eyed3/plugins/classic.py`
	
2. remove random comments using following command: 
	```
    eyeD3 --user-text-frame "comment:" <directory>
	```

3. override Album types based on detected from album-name (`[Singles]`, `[EP]`, etc.) or via explicit arg:
    (as per `<CONDA_ENV>/Lib/site-packages/eyed3/plugins/fixup.py`)

    - ``lp``: A traditional "album" of songs from a single artist.
      No extra info is written to the tag since this is the default.
    - ``ep``: A short collection of songs from a single artist. The string 'ep'
      is written to the tag's ``%(TXXX_ALBUM_TYPE)s`` field.
    - ``various``: A collection of songs from different artists. The string
      'various' is written to the tag's ``%(TXXX_ALBUM_TYPE)s`` field.
    - ``live``: A collection of live recordings from a single artist. The string
      'live' is written to the tag's ``%(TXXX_ALBUM_TYPE)s`` field.
    - ``compilation``: A collection of songs from various recordings by a single
      artist. The string 'compilation' is written to the tag's
      ``%(TXXX_ALBUM_TYPE)s`` field. Compilation dates, unlike other types, may
      differ.
    - ``demo``: A demo recording by a single artist. The string 'demo' is
      written to the tag's ``%(TXXX_ALBUM_TYPE)s`` field.
    - ``single``: A track that should no be associated with an album (even if
      it has album metadata). The string 'single' is written to the tag's
      ``%(TXXX_ALBUM_TYPE)s`` field.

4. apply total tracks number from number of songs listed in info file. 
	if album type is singles, ignore (reset) this value to be "none" (in case previously written)
	ie: 
	```
	eyeD3 -D <TOTAL> <directory>
	```
	
5. apply artist, contrib-artist, album name, genre and year to ID3 Tags + (any other fields?)
	```
	eyeD3 --album <ALBUM> --album-artist <ALBUM ARTIST> --artist <ARTIST> --year <YEAR> --genre <GENRE>
	```

6. add `--detail` arg that retrieves ID3 tag listing information by calling (default is to list tags info)
    ```
    eyeD3 <directory>
    ```
    
    `--detail` should be allowed by itself for simple listing, or combined with others for listing of processing results
