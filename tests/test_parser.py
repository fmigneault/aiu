from aiu.parser import parse_audio_config
from datetime import time
import os
CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'configs')


def test_parser_config_csv_basic():
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-basic.csv'))
    assert isinstance(config, list)
    assert len(config) == 2
    assert config[0]['track'] == 2
    assert config[0]['title'] == 'test'
    assert config[0]['artist'] == 'test'
    assert config[1]['track'] == 1
    assert config[1]['title'] == 'song'
    assert config[1]['artist'] == 'other artist'


def test_parser_config_json_basic():
    raise NotImplemented


def test_parser_config_yaml_basic():
    raise NotImplemented


def test_parser_config_tab_basic():
    config = parse_audio_config(os.path.join(CONFIG_DIR, 'config-tab-basic.txt'))
    assert isinstance(config, list)
    assert len(config) == 2
    assert config[0]['track'] is None
    assert config[0]['title'] == 'test'
    assert config[0]['artist'] == 'some artist'
    assert isinstance(config[0]['duration'], time)
    assert config[0]['duration'] == time(minute=1, second=23)
    assert config[1]['track'] is None
    assert config[1]['title'] == 'song'
    assert config[1]['artist'] == 'test-artist'
    assert isinstance(config[1]['duration'], time)
    assert config[1]['duration'] == time(minute=4, second=56)
    assert config[1]['track'] is None
    assert config[1]['title'] == 'medley'
    assert config[1]['artist'] == 'I Love Long Songs'
    assert isinstance(config[1]['duration'], time)
    assert config[1]['duration'] == time(hour=1, minute=2, second=17)


def test_parser_config_tab_numbered():
    raise NotImplemented


def test_parser_config_tab_crazy():
    raise NotImplemented
