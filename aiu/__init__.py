from typing import AnyStr, Dict, List, Optional, TYPE_CHECKING
import logging
import os
import sys
import yaml

sys.path.insert(0, os.path.dirname(__file__))

import __meta__  # noqa

AIU_PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
AIU_ROOT_DIR = os.path.dirname(AIU_PACKAGE_DIR)
AIU_CONFIG_DIR = os.path.join(AIU_ROOT_DIR, "config")

if TYPE_CHECKING:
    StopwordsType = Optional[List[AnyStr]]
    ExceptionsType = Optional[Dict[AnyStr, AnyStr]]


class Config:
    STOPWORDS = None    # type: StopwordsType
    EXCEPTIONS = None   # type: ExceptionsType


DEFAULT_STOPWORDS_CONFIG = os.path.join(AIU_CONFIG_DIR, "stopwords.cfg")
DEFAULT_EXCEPTIONS_CONFIG = os.path.join(AIU_CONFIG_DIR, "exceptions.cfg")
AIU_SETUP_CONFIG = os.path.join(AIU_ROOT_DIR, "setup.cfg")


class YamlEnabledLogger(logging.Logger):
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
VERBOSE = logging.DEBUG // 2
logging.addLevelName(VERBOSE, "VERBOSE")
logging.setLoggerClass(YamlEnabledLogger)
LOGGER = logging.getLogger(__meta__.__package__)
if not getattr(LOGGER, "__AIU_CONFIGURED__", False):
    if os.path.isfile(AIU_SETUP_CONFIG):
        import logging.config
        import configparser
        # remove %% escape for logging format
        config = configparser.RawConfigParser()
        config.read(AIU_SETUP_CONFIG)
        for section in config:
            if section == "formatter_generic":
                config.set("formatter_generic", "format", config["formatter_generic"]["format"].replace("%%", "%"))
                break
        logging.config.fileConfig(config)

    setattr(LOGGER, "__AIU_CONFIGURED__", True)
