from aiu.parser import parse_audio_config, FORMAT_MODE_CSV, FORMAT_MODE_TAB, FORMAT_MODE_JSON, FORMAT_MODE_YAML
from aiu.typedefs import Duration, IntField, StrField, AudioConfig, AudioInfo
import aiu
# noinspection PyPackageRequirements
import pytest
import os
CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'configs')


def test_parser_config_csv_basic():
    aiu.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-basic.csv'), 'csv')
    assert isinstance(config, list)
    assert len(config) == 2
    assert config[0]['track'] == 2
    assert config[0]['track'].raw == '02'
    assert config[0]['title'].raw == 'test'
    assert config[0]['artist'].raw == 'test-artist'
    assert config[1]['track'] == 1
    assert config[1]['track'].raw == '1'
    assert config[1]['title'].raw == 'song'
    assert config[1]['artist'].raw == 'other artist'


def test_parser_config_csv_typing():
    """Validate config formats, fields, properties and key getters."""
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-basic.csv'), FORMAT_MODE_CSV)
    assert isinstance(config, list)
    assert isinstance(config, AudioConfig)
    assert len(config) == 2
    for c in config:
        assert isinstance(c, dict)
        assert isinstance(c, AudioInfo)
        assert isinstance(c['track'], IntField)
        assert isinstance(c.track, IntField)
        assert isinstance(c['title'], StrField)
        assert isinstance(c.title, StrField)
        assert isinstance(c['artist'], StrField)
        assert isinstance(c.artist, StrField)


@pytest.mark.skip("not implemented")
def test_parser_config_json_basic():
    raise NotImplemented  # TODO


@pytest.mark.skip("not implemented")
def test_parser_config_yaml_basic():
    raise NotImplemented  # TODO


def test_parser_config_tab_basic():
    aiu.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-tab-basic.txt'), FORMAT_MODE_TAB)
    assert isinstance(config, list)
    assert len(config) == 3
    # noinspection PyComparisonWithNone
    assert config[0]['track'].raw == None   # noqa
    assert config[0]['title'].raw == 'some song'
    assert isinstance(config[0]['duration'], Duration)
    assert config[0]['duration'] == Duration(minutes=1, seconds=23)
    # noinspection PyComparisonWithNone
    assert config[1]['track'].raw == None   # noqa
    assert config[1]['title'].raw == 'song'
    assert isinstance(config[1]['duration'], Duration)
    assert config[1]['duration'] == Duration(minutes=4, seconds=56)
    # noinspection PyComparisonWithNone
    assert config[2]['track'].raw == None   # noqa
    assert config[2]['title'].raw == 'I Love Long Songs'
    assert isinstance(config[2]['duration'], Duration)
    assert config[2]['duration'] == Duration(hours=1, minutes=2, seconds=17)


def test_parser_config_tab_numbered():
    aiu.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-tab-number.txt'), FORMAT_MODE_TAB)
    assert isinstance(config, list)
    assert len(config) == 2
    assert config[0]['track'].raw == '1'
    assert config[0]['title'].raw == 'song 1'
    assert isinstance(config[0]['duration'], Duration)
    assert config[0]['duration'] == Duration(minutes=3, seconds=59)
    assert config[1]['track'].raw == '2'
    assert config[1]['title'].raw == 'song 2'
    assert isinstance(config[1]['duration'], Duration)
    assert config[1]['duration'] == Duration(minutes=4, seconds=50)


def test_parser_config_tab_crazy():
    aiu.STOPWORDS = []  # ignore
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-tab-crazy.txt'), FORMAT_MODE_TAB)
    tests = [
        ('1', 'blah'), ('2', 'test'), ('3', 'ok'), ('4', 'what...'), ('5', 'so fly'), ('6', 'yep'),
        ('7', 'am i a joke to you?'), ('8', 'lol'), ('9', 'why not'), ('10', 'hahaha'), (None, 'what is this?')
    ]
    assert isinstance(config, list)
    assert len(config) == len(tests)
    for i, t in enumerate(tests):
        assert config[i]['track'].raw == t[0]
        assert config[i]['title'].raw == t[1]


def test_parser_config_tab_time_and_beautify():
    aiu.STOPWORDS = []    # ignore
    config_raw = parse_audio_config(os.path.join(CONFIG_DIR, 'config-tab-time.txt'), FORMAT_MODE_TAB)
    aiu.STOPWORDS = None  # reset
    config_clean = parse_audio_config(os.path.join(CONFIG_DIR, 'config-tab-time.txt'), FORMAT_MODE_TAB)
    assert isinstance(config_raw, list)
    assert len(config_raw) == 8
    for conf_raw, conf_clean, result in zip(config_raw, config_clean, [
        {'track': 1, 'title_raw': 'Nothing to say', 'title_clean': 'Nothing to Say',
         'duration': Duration(minutes=1, seconds=23)},
        {'track': 2, 'title_raw': 'A random song', 'title_clean': 'A Random Song',
         'duration': Duration(minutes=4, seconds=56)},
        {'track': 3, 'title_raw': 'I Love Long Songs', 'title_clean': 'I Love Long Songs',
         'duration': Duration(hours=1, minutes=2, seconds=17)},
        {'track': 4, 'title_raw': 'Got 1 number in here', 'title_clean': 'Got 1 Number in Here',
         'duration': Duration(minutes=3, seconds=29)},
        {'track': 5, 'title_raw': 'Have 2 here: 6, and there 11', 'title_clean': 'Have 2 Here: 6, and There 11',
         'duration': Duration(minutes=3, seconds=29)},
        {'track': 6, 'title_raw': 'Have fun with this: 1:23', 'title_clean': 'Have Fun with This: 1:23',
         'duration': Duration(minutes=2, seconds=54)},
        {'track': 7, 'title_raw': 'At 4:20 is when it happens', 'title_clean': 'At 4:20 Is When It Happens',
         'duration': Duration(hours=3, minutes=20, seconds=54)},
        {'track': 8, 'title_raw': 'Some absolutely crazy long song', 'title_clean': 'Some Absolutely Crazy Long Song',
         'duration': Duration(hours=104, minutes=56, seconds=20)},
    ]):
        assert conf_clean['title'] == result['title_clean']
        assert conf_raw['title'] == result['title_raw']
        assert conf_raw['track'] == result['track']
        assert conf_raw['duration'] == result['duration']


@pytest.mark.skip("not implemented")
def test_parser_config_any_format():
    pass
