import os
import logging

LOG = logging.getLogger(__name__)


def check_is_root():
    flag = os.geteuid() == 0
    if not flag:
        LOG.warning("current user not have root permission")
    return flag
