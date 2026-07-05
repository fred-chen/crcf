"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

from .connfactory import connect
from .target import Target, __execmd
from .linuxtarget import LinuxTarget
from .common import Common


def gettarget(
    host: str,
    username: str = None,
    password: str = None,
    svc: str = "ssh",
    timeout: int = 60,
) -> Target:
    """
    Factory function of target.

    Creating connection to the target address
    and issue simple command to detect target type then create target object respectively.

    Args:
        host (str): hostname or ip address.
        username (str, optional): user name to login. Defaults to None.
        password (str, optional): password of the user. Defaults to None.
        svc (str, optional): service to connect. Defaults to "ssh".
        timeout (int, optional): timeout. Defaults to 60.

    Returns:
        Target: a target object.
    """
    conn = connect(host, username, password, svc, timeout)
    if not conn:
        return None
    txt = __execmd(conn, "uname -s", timeout)
    target = None
    if txt and txt.find("Linux") >= 0:
        target = LinuxTarget(host, svc, username, password, conn, timeout)
    else:
        conn.printlog()
        Common().log("unsupported target type.")
    return target
