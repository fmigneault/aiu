from aiu import DEFAULT_STOPWORDS_CONFIG
from aiu.parser import (
    FORMAT_MODE_CSV,  
    FORMAT_MODE_TAB,  
    FORMAT_MODE_LIST,
    FORMAT_MODE_JSON, 
    FORMAT_MODE_YAML,
    load_config,
    parse_audio_config,
)
from aiu.typedefs import Duration, IntField, StrField, AudioConfig, AudioInfo
import aiu
import aiu.tags as t
import pytest  # noqa
import os

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "configs")


def test_parser_config_csv_basic():
    aiu.Config.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, "config-basic.csv"), "csv")
    assert isinstance(config, list)
    assert len(config) == 2
    assert config[0][t.TAG_TRACK] == 2
    assert config[0][t.TAG_TRACK].raw == "02"
    assert config[0][t.TAG_TITLE].raw == "test"
    assert config[0][t.TAG_ARTIST].raw == "test-artist"
    assert config[1][t.TAG_TRACK] == 1
    assert config[1][t.TAG_TRACK].raw == "1"
    assert config[1][t.TAG_TITLE].raw == "song"
    assert config[1][t.TAG_ARTIST].raw == "other artist"


def test_parser_config_csv_typing():
    """Validate config formats, fields, properties and key getters."""
    config = parse_audio_config(os.path.join(CONFIG_DIR, "config-basic.csv"), FORMAT_MODE_CSV)
    assert isinstance(config, list)
    assert isinstance(config, AudioConfig)
    assert len(config) == 2
    for c in config:
        assert isinstance(c, dict)
        assert isinstance(c, AudioInfo)
        assert isinstance(c[t.TAG_TRACK], IntField)
        assert isinstance(c.track, IntField)
        assert isinstance(c[t.TAG_TITLE], StrField)
        assert isinstance(c.title, StrField)
        assert isinstance(c[t.TAG_ARTIST], StrField)
        assert isinstance(c.artist, StrField)


@pytest.mark.skip("not implemented")
def test_parser_config_json_basic():
    raise NotImplementedError  # TODO


@pytest.mark.skip("not implemented")
def test_parser_config_yaml_basic():
    raise NotImplementedError  # TODO


def test_parser_config_tab_basic():
    aiu.Config.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, "config-tab-basic.txt"), FORMAT_MODE_TAB)
    assert isinstance(config, list)
    assert len(config) == 3
    assert config[0][t.TAG_TRACK].raw is None
    assert config[0][t.TAG_TITLE].raw == "some song"
    assert isinstance(config[0][t.TAG_DURATION], Duration)
    assert config[0][t.TAG_DURATION] == Duration(minutes=1, seconds=23)
    assert config[1][t.TAG_TRACK].raw is None
    assert config[1][t.TAG_TITLE].raw == "song"
    assert isinstance(config[1][t.TAG_DURATION], Duration)
    assert config[1][t.TAG_DURATION] == Duration(minutes=4, seconds=56)
    assert config[2][t.TAG_TRACK].raw is None
    assert config[2][t.TAG_TITLE].raw == "I Love Long Songs"
    assert isinstance(config[2][t.TAG_DURATION], Duration)
    assert config[2][t.TAG_DURATION] == Duration(hours=1, minutes=2, seconds=17)


def test_parser_config_tab_numbered():
    aiu.Config.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, "config-tab-number.txt"), FORMAT_MODE_TAB)
    assert isinstance(config, list)
    assert len(config) == 2
    assert config[0][t.TAG_TRACK].raw == "1"
    assert config[0][t.TAG_TITLE].raw == "song 1"
    assert isinstance(config[0][t.TAG_DURATION], Duration)
    assert config[0][t.TAG_DURATION] == Duration(minutes=3, seconds=59)
    assert config[1][t.TAG_TRACK].raw == "2"
    assert config[1][t.TAG_TITLE].raw == "song 2"
    assert isinstance(config[1][t.TAG_DURATION], Duration)
    assert config[1][t.TAG_DURATION] == Duration(minutes=4, seconds=50)


def test_parser_config_tab_crazy():
    aiu.Config.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, "config-tab-crazy.txt"), FORMAT_MODE_TAB)
    tests = [
        ("1", "blah"), ("2", "test"), ("3", "ok"), ("4", "what..."), ("5", "so fly"), ("6", "yep"),
        ("7", "am i a joke to you?"), ("8", "lol"), ("9", "why not"), ("10", "hahaha"), (None, "what is this?")
    ]
    assert isinstance(config, list)
    assert len(config) == len(tests)
    for i, test in enumerate(tests):
        assert config[i][t.TAG_TRACK].raw == test[0]
        assert config[i][t.TAG_TITLE].raw == test[1]


def test_parser_config_tab_time_and_beautify():
    aiu.Config.STOPWORDS = []    # ignore
    config_raw = parse_audio_config(os.path.join(CONFIG_DIR, "config-tab-time.txt"), FORMAT_MODE_TAB)
    aiu.Config.STOPWORDS = None  # reset for reload
    aiu.Config.STOPWORDS = load_config(aiu.Config.STOPWORDS, DEFAULT_STOPWORDS_CONFIG, is_map=False)
    config_clean = parse_audio_config(os.path.join(CONFIG_DIR, "config-tab-time.txt"), FORMAT_MODE_TAB)
    assert isinstance(config_raw, list)
    assert len(config_raw) == 8
    for conf_raw, conf_clean, result in zip(config_raw, config_clean, [
        {t.TAG_TRACK: 1, "title_raw": "Nothing to say",
         "title_clean": "Nothing to Say",
         t.TAG_DURATION: Duration(minutes=1, seconds=23)},
        {t.TAG_TRACK: 2, "title_raw": "A random song",
         "title_clean": "A Random Song",
         t.TAG_DURATION: Duration(minutes=4, seconds=56)},
        {t.TAG_TRACK: 3, "title_raw": "I Love Long Songs",
         "title_clean": "I Love Long Songs",
         t.TAG_DURATION: Duration(hours=1, minutes=2, seconds=17)},
        {t.TAG_TRACK: 4, "title_raw": "Got 1 number in here",
         "title_clean": "Got 1 Number in Here",
         t.TAG_DURATION: Duration(minutes=3, seconds=29)},
        {t.TAG_TRACK: 5, "title_raw": "Have 2 here: 6, and there 11",
         "title_clean": "Have 2 Here: 6, and There 11",
         t.TAG_DURATION: Duration(minutes=3, seconds=29)},
        {t.TAG_TRACK: 6, "title_raw": "Have fun with this: 1:23",
         "title_clean": "Have Fun with This: 1:23",
         t.TAG_DURATION: Duration(minutes=2, seconds=54)},
        {t.TAG_TRACK: 7, "title_raw": "At 4:20 is when it happens",
         "title_clean": "At 4:20 Is When It Happens",
         t.TAG_DURATION: Duration(hours=3, minutes=20, seconds=54)},
        {t.TAG_TRACK: 8, "title_raw": "Some absolutely crazy long song",
         "title_clean": "Some Absolutely Crazy Long Song",
         t.TAG_DURATION: Duration(hours=104, minutes=56, seconds=20)},
    ]):
        assert conf_clean[t.TAG_TITLE] == result["title_clean"]
        assert conf_raw[t.TAG_TITLE] == result["title_raw"]
        assert conf_raw[t.TAG_TRACK] == result[t.TAG_TRACK]
        assert conf_raw[t.TAG_DURATION] == result[t.TAG_DURATION]


def test_parser_config_list_both():
    aiu.Config.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, "config-list-both.lst"), FORMAT_MODE_LIST)
    assert isinstance(config, list)
    assert len(config) == 3
    assert config[0][t.TAG_TRACK].raw == "1"
    assert config[0][t.TAG_TITLE].raw == "song 1"
    assert isinstance(config[0][t.TAG_DURATION], Duration)
    assert config[0][t.TAG_DURATION] == Duration(minutes=3, seconds=59)
    assert config[1][t.TAG_TRACK].raw == "2"
    assert config[1][t.TAG_TITLE].raw == "song 2"
    assert isinstance(config[1][t.TAG_DURATION], Duration)
    assert config[2][t.TAG_DURATION] == Duration(minutes=4, seconds=50)
    assert config[2][t.TAG_TRACK].raw == "3"
    assert config[2][t.TAG_TITLE].raw == "song 3"
    assert isinstance(config[2][t.TAG_DURATION], Duration)
    assert config[2][t.TAG_DURATION] == Duration(minutes=1, seconds=23)


def test_parser_config_list_track():
    aiu.Config.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, "config-list-track.lst"), FORMAT_MODE_LIST)
    assert isinstance(config, list)
    assert len(config) == 3
    assert config[0][t.TAG_TRACK].raw == "1"
    assert config[0][t.TAG_TITLE].raw == "song 1"
    assert t.TAG_DURATION not in config[0]
    assert config[0].get(t.TAG_DURATION) is None
    assert config[1][t.TAG_TRACK].raw == "2"
    assert config[1][t.TAG_TITLE].raw == "song 2"
    assert t.TAG_DURATION not in config[1]
    assert config[1].get(t.TAG_DURATION) is None
    assert config[2][t.TAG_TRACK].raw == "3"
    assert config[2][t.TAG_TITLE].raw == "song 3"
    assert t.TAG_DURATION not in config[2]
    assert config[2].get(t.TAG_DURATION) is None


def test_parser_config_list_duration():
    aiu.Config.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, "config-list-duration.lst"), FORMAT_MODE_LIST)
    assert isinstance(config, list)
    assert len(config) == 3
    assert t.TAG_TRACK not in config[0]
    assert config[0].get(t.TAG_TRACK) is None
    assert config[0][t.TAG_TITLE].raw == "song 1"
    assert isinstance(config[0][t.TAG_DURATION], Duration)
    assert config[0][t.TAG_DURATION] == Duration(minutes=3, seconds=59)
    assert config[1].get(t.TAG_TRACK) is None
    assert config[1][t.TAG_TITLE].raw == "song 2"
    assert isinstance(config[1][t.TAG_DURATION], Duration)
    assert config[1][t.TAG_DURATION] == Duration(minutes=4, seconds=50)
    assert config[2].get(t.TAG_TRACK) is None
    assert config[2][t.TAG_TITLE].raw == "song 3"
    assert isinstance(config[2][t.TAG_DURATION], Duration)
    assert config[2][t.TAG_DURATION] == Duration(minutes=1, seconds=23)


@pytest.mark.skip("not implemented")
def test_parser_config_any_format():
    raise NotImplementedError  # TODO
