"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

import os

from . import connection
from .me import is_server_svc_alive, is_command_executable


class SshConnection(connection.Connection):
    """ssh connection class is a child class of connection.Connection.
    It implements the connection interface with ssh command.
    """

    def __init__(self, host, username=None, password=None, timeout=30, newline="\n"):
        if not is_command_executable("ssh"):
            self.log("ssh is NOT there.")
            return None
        connection.Connection.__init__(self, host, username, password, timeout, newline)

    def connect(self):
        if self.password and os.path.exists(
            self.password
        ):  # the password is an IdentityFile for ssh authentication
            args = (
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                f"IdentityFile={self.password}",
                "-o",
                "ServerAliveInterval=60",
                "-o",
                "ServerAliveCountMax=3",
                "-o",
                "TCPKeepAlive=yes",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-l",
                self.username,
                self.host,
            )
        else:
            args = (
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ServerAliveInterval=60",
                "-o",
                "ServerAliveCountMax=3",
                "-o",
                "TCPKeepAlive=yes",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-l",
                self.username,
                self.host,
            )
        try:
            self._spawn(args)
        except OSError as msg:
            self.log(str(msg))
            return False
        return self.login()

    def svcalive(self):
        return is_server_svc_alive(host=self.host, svc=22, timeout=10)
