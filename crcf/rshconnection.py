"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

from . import connection, me


class RshConnection(connection.Connection):
    """RshConnection is a child-class of Connection.

    It implements the connection interface with rsh command.
    """

    def __init__(self, host, username, password, timeout, newline):
        if not me.is_command_executable("rsh"):
            self.log("rsh is NOT there.")
            return None
        connection.Connection.__init__(self, host, username, password, timeout, newline)

    def connect(self):
        raise NotImplementedError()
