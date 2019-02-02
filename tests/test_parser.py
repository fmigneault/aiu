from aiu.parser import parse_audio_config
from aiu.typedefs import Duration
import os
CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'configs')


def test_parser_config_csv_basic():
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-basic.csv'), 'csv')
    assert isinstance(config, list)
    assert len(config) == 2
    assert config[0]['track'] == 2
    assert config[0]['title'] == 'test'
    assert config[0]['artist'] == 'test'
    assert config[1]['track'] == 1
    assert config[1]['title'] == 'song'
    assert config[1]['artist'] == 'other artist'


def test_parser_config_json_basic():
    raise NotImplemented  # TODO


def test_parser_config_yaml_basic():
    raise NotImplemented  # TODO


def test_parser_config_tab_basic():
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-tab-basic.txt'))
    assert isinstance(config, list)
    assert len(config) == 2
    assert config[0]['track'] is None
    assert config[0]['title'] == 'test'
    assert config[0]['artist'] == 'some artist'
    assert isinstance(config[0]['duration'], Duration)
    assert config[0]['duration'] == Duration(minutes=1, seconds=23)
    assert config[1]['track'] is None
    assert config[1]['title'] == 'song'
    assert config[1]['artist'] == 'test-artist'
    assert isinstance(config[1]['duration'], Duration)
    assert config[1]['duration'] == Duration(minutes=4, seconds=56)
    assert config[1]['track'] is None
    assert config[1]['title'] == 'medley'
    assert config[1]['artist'] == 'I Love Long Songs'
    assert isinstance(config[1]['duration'], Duration)
    assert config[1]['duration'] == Duration(hours=1, minutes=2, seconds=17)


def test_parser_config_tab_numbered():
    raise NotImplemented  # TODO


def test_parser_config_tab_crazy():
    raise NotImplemented  # TODO


def test_parser_config_tab_time():
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-tab-time.txt'))
    assert isinstance(config, list)
    assert len(config) == 8
    for i, case in enumerate([{
        {'track': 1, 'title': 'Nothing to Say', 'artist': 'Easy Test',
         'duration': Duration(minutes=1, seconds=23)},
        {'track': 2, 'title': 'A Random Song', 'artist': 'Bad Signer',
         'duration': Duration(minutes=4, seconds=56)},
        {'track': 3, 'title': 'Medley', 'artist': 'I Love Long Songs',
         'duration': Duration(hours=1, minutes=2, seconds=17)},
        {'track': 4, 'title': 'Got 1 Number in Here', 'artist': 'Tricky Be Good',
         'duration': Duration(minutes=3, seconds=29)},
        {'track': 5, 'title': 'Have 2 Here: 6, and There 11', 'artist': 'Slightly Worst',
         'duration': Duration(minutes=3, seconds=29)},
        {'track': 6, 'title': 'Have Fun with this: 1:23', 'artist': 'Some A-Hole',
         'duration': Duration(minutes=2, seconds=54)},
        {'track': 7, 'title': 'At 4:20 is when it happens', 'artist': 'Watch the World Burn',
         'duration': Duration(hours=3, minutes=20, seconds=54)},
        {'track': 8, 'title': 'Some Absolutely Crazy Long Song', 'artist': 'Never Gonna Stop',
         'duration': Duration(hours=104, minutes=56, seconds=20)},
    }]):
        assert config[i]['track'] == case['track']
        assert config[i]['title'] == case['title']
        assert config[i]['artist'] == case['artist']
        assert config[i]['duration'] == case['duration']
