from typing import AnyStr, List
import os

AIU_PACKAGE_DIR = os.path.abspath(os.path.dirname(__file__))
AIU_CONFIG_DIR = os.path.join(os.path.dirname(AIU_PACKAGE_DIR), 'config')

STOPWORDS = None    # type: List[AnyStr]
DEFAULT_STOPWORDS_CONFIG = os.path.join(AIU_CONFIG_DIR, 'stopwords.cfg')
