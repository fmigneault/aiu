"""
Configurations for the application.
"""

import logging
import os
import sys
from typing import Dict, List, Optional

import yaml

from aiu import __meta__

AIU_PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
AIU_ROOT_DIR = os.path.dirname(AIU_PACKAGE_DIR)
AIU_CONFIG_DIR = os.path.join(AIU_ROOT_DIR, "config")

StopwordsType = Optional[List[str]]
ExceptionsType = Optional[Dict[str, str]]


class Config:
    """
    Application configuration options.
    """

    EXCEPTIONS_RENAME = None    # type: ExceptionsType
    STOPWORDS_RENAME = None     # type: StopwordsType
    STOPWORDS_MATCH = None      # type: StopwordsType


DEFAULT_STOPWORDS_CONFIG = os.path.join(AIU_CONFIG_DIR, "stopwords.cfg")
DEFAULT_EXCEPTIONS_CONFIG = os.path.join(AIU_CONFIG_DIR, "exceptions.cfg")
DEFAULT_STOPWORDS_MATCH = os.path.join(AIU_CONFIG_DIR, "ignore.cfg")
AIU_LOGGING_CONFIG = os.path.join(AIU_ROOT_DIR, "logging.ini")


class YamlEnabledLogger(logging.Logger):
    """
    Logger that supports YAML output formatting.
    """

    def to_yaml(self, data, indent=2):
        # type: (dict, int) -> None
        handlers = self.handlers + self.parent.handlers + (self.root.handlers if hasattr(self, "root") else [])
        stdout_h = [
            h for h in handlers
            if hasattr(h, "stream") and hasattr(h.stream, "write") and h.level != logging.NOTSET
        ] or [logging.StreamHandler(sys.stdout)]
        for h in stdout_h:
            yaml.safe_dump(data, h.stream, indent=indent, default_flow_style=False)


# logging
TRACE = logging.DEBUG // 2
logging.addLevelName(TRACE, "TRACE")
logging.setLoggerClass(YamlEnabledLogger)
LOGGER = logging.getLogger(__meta__.__package__)
if not getattr(LOGGER, "__AIU_CONFIGURED__", False):
    def log_trace(msg, *args, **kwargs):
        if LOGGER.isEnabledFor(TRACE):
            LOGGER._log(TRACE, msg, args, **kwargs)  # noqa  # pylint: disable=protected-access

    LOGGER.trace = log_trace
    if os.path.isfile(AIU_LOGGING_CONFIG):
        # pylint: disable=import-outside-toplevel,ungrouped-imports
        import configparser
        import logging.config
        # remove %% escape for logging format
        config = configparser.RawConfigParser()
        config.read(AIU_LOGGING_CONFIG)
        for section in config:
            if section == "formatter_generic":
                config.set("formatter_generic", "format", config["formatter_generic"]["format"].replace("%%", "%"))
                break
        logging.config.fileConfig(config)

    setattr(LOGGER, "__AIU_CONFIGURED__", True)
