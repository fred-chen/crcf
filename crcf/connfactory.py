"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

from .sshconnection import SshConnection
from .telnetconnection import TelnetConnection
from .rshconnection import RshConnection
from .common import Common
from .me import is_server_svc_alive
from .connection import Connection
from . import connection
from getpass import getuser

svclist = {
    "ssh": 22,  # ssh
    "shell": 514,  # rsh
    "telnet": 23  # telnet
    #           'exec':512,  # rexec
    #           'login':513, # rlogin
}


def connect(
    host="127.0.0.1", username=None, password=None, svc="ssh", timeout=30, newline="\n"
) -> Connection:
    """connect() is a factory method of connection objects.

    connect() detects available connection method ( ssh/rsh/telnet ) and create
    connection object respectively.

    connect() will return a connection object ( a child-class object which
    implements connection interface ) svc can be any one of: shell(rsh-remote
    shell), ssh or telnet.
    """
    username = username or getuser()
    conn = None
    if svc is not None:
        conn = createconn(host, svc, username, password, timeout, newline)
    if svc is None and conn is None:
        for key in svclist:
            if key == svc:
                continue
            conn = createconn(host, key, username, password, timeout, newline)
            if conn:
                break
    return conn


def createconn(
    host: str, svc: str, username: str, password: str, timeout: int, newline: bytes
) -> Connection:
    """a factory method to create connection object

    Args:
        host (str): the hostname or ip address of the server
        svc (str): the service name or port number to connect to the server
        username (str): username to login the server
        password (str): the password of the user
        timeout (int): the timeout to wait for the connection
        newline (char): the newline character to send to the server

    Returns:
        Connection: the connection object or None if failed to connect
    """
    Common().log(f"connecting {host} with {svc}")
    conn = None
    alive = is_server_svc_alive(host, svc, timeout)
    if alive:
        try:
            if svc == "shell":
                conn = RshConnection(host, username, password, timeout, newline)
            elif svc == "ssh":
                conn = SshConnection(host, username, password, timeout, newline)
            elif svc == "telnet":
                conn = TelnetConnection(host, username, password, timeout, newline)
            else:
                return None
        except connection.ConnError as err:
            conn = None
            Common().log(f"couldn't connect {host} with {svc}. ({err})")
    else:
        Common().log(f"couldn't connect {host} with {svc}. (service is not available.)")
        conn = None

    return conn
