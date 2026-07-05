"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

from . import connection, me


class TelnetConnection(connection.Connection):
    """telnet connection class is a child class of connection.Connection.

    It implements the connection interface with telnet command.
    """

    def __init__(self, host, username, password, timeout, newline):
        if not me.is_command_executable("telnet"):
            self.log("telnet is NOT there.")
            return None
        connection.Connection.__init__(self, host, username, password, timeout, newline)

    def connect(self):
        raise NotImplementedError()
