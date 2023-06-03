import os
import sys
from loguru import logger

from chaoshen_toolbox.utils import common

# logger.debug("That's it, beautiful and simple logging!")
log_path = common.get_recommended_log_path()
LOG = logger
LOG.add(log_path, format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}")

LOG.info('load logger')
