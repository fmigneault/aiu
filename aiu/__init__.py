from typing import AnyStr, List, Optional
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import __meta__  # noqa

AIU_PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
AIU_ROOT_DIR = os.path.dirname(AIU_PACKAGE_DIR)
AIU_CONFIG_DIR = os.path.join(AIU_ROOT_DIR, 'config')

STOPWORDS = None    # type: Optional[List[AnyStr]]
DEFAULT_STOPWORDS_CONFIG = os.path.join(AIU_CONFIG_DIR, 'stopwords.cfg')

AIU_SETUP_CONFIG = os.path.join(AIU_ROOT_DIR, "setup.cfg")

# logging
VERBOSE = int(logging.DEBUG/2)
logging.addLevelName(VERBOSE, "VERBOSE")
LOGGER = logging.getLogger(__meta__.__package__)   # see also "aiu.utils.get_logger"
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
    # if we want to do custom parsing or add more details before each log
    # logging.setLoggerClass(klass)
    logging.config.fileConfig(config)
