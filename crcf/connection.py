"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

import os
import signal
import pty
import re
import select
import time
from . import me, common
from .common import Common


class ConnError(BaseException):
    """the exception class for connection"""


class Connection(Common, common.LockAble):
    """
    common interface of a connection object.
    all specific connection types should implement this interface.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        username: str = None,
        password: str = None,
        timeout: int = 30,
        newline: str = "\n",
    ):
        common.LockAble.__init__(self)
        self.pty_fd = None
        self.child_pid = None
        self.host = host
        self.timeout = timeout
        self.username = username
        self.password = password
        self.newline = newline
        self.txt = ""
        if not self.connect():
            raise ConnError(BaseException(f"Failed to connect to {host}"))

    def connect(self):
        """the abstract method to connect to the host.

        this method should be implemented by child classes.
        """
        raise NotImplementedError("Should have implemented this")

    def reconnect(self):
        """reconnect to the host"""
        self.disconnect()
        self.connect()

    def disconnect(self):
        """disconnect from the host"""
        if self.child_pid:
            os.kill(self.child_pid, signal.SIGKILL)
            os.waitpid(self.child_pid, os.WNOHANG)
            self.child_pid = None
            self.pty_fd = None

    def _spawn(self, args):
        (pid, filedesc) = pty.fork()
        if pid == 0:  # child
            os.execvp(args[0], args)
            # cpid = os.fork()
            # if(cpid == 0):  # child's child
            #     os.execvp(args[0], args)
            # else:
            #     # the middle layer process monitors its parent
            #     # kill's the bottom layer child process if top layer parent is dead
            #     while os.getppid() != 1:
            #         time.sleep(1)
            #     os.kill(cpid, 9)
        else:
            self.child_pid = pid
            self.pty_fd = filedesc

    def read(self, timeout: int = None):
        """read text from the connection

        this method will block until there is text to read or timeout.

        Args:
            timeout (int): timeout in seconds. None means no timeout

        Returns:
            str: the text read or None if connection is broken or timeout
        """
        self.lock()
        txt = ""
        if timeout:
            result = select.select([self.pty_fd], [], [], timeout)
        else:
            result = select.select([self.pty_fd], [], [])
        if result[0]:
            try:
                txt = os.read(self.pty_fd, 4096).decode("utf-8")
            except OSError as _err:
                self.unlock()
                self.disconnect()
                return None
            self.txt += txt
        self.unlock()
        return txt

    def write(self, txt: str):
        """write text to the connection

        Args:
            txt (str): the text to write

        Returns:
            int: the number of bytes written or None if connection is broken
        """
        self.lock()
        try:
            ret = os.write(self.pty_fd, txt.encode("utf-8"))
        except OSError as _err:  # child process ended
            self.unlock()
            print("returning none in connection.write()")
            return None
        self.unlock()
        return ret

    def write_newline(self):
        """write a newline to the connection"""
        return self.write(self.newline)

    def waitfor(self, pattern, timeout=0):
        """
        wait for a specific pattern
        return:
            the text with the pattern if success
            None if timeout
        """
        dur = 0
        reg = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        txt = ""
        start = time.time()
        while True:
            _lines = self.read(1)
            if not _lines is None:
                txt += _lines
            else:
                return None  # child process ended
            match = reg.search(txt)
            if match:
                break
            dur = time.time() - start
            # print ("txt='%s'" % (txt))
            if timeout and dur > timeout:
                break
        return txt

    def _inshell(self, timeout=1):
        self.write("stty -echo")
        self.write_newline()
        self.write("echo CRCF")
        self.write_newline()
        if not self.waitfor("CRCF", timeout):
            return False
        return True

    def login(self):
        """login to the host"""
        if not self.connected():
            return False
        needpasswd = 0
        txt = self.waitfor(".+", self.timeout)

        if txt and txt.find("password:") >= 0:
            needpasswd = 1
        if needpasswd:
            self.write(self.password)
            self.write_newline()
            self.waitfor(".+", self.timeout)
        self.write("bash")
        self.write_newline()
        self.write("stty -echo")
        self.write_newline()
        self.write("PS1=" + self.UNIQIDENTIFIER)
        self.write_newline()
        self.waitfor(self.UNIQIDENTIFIER, self.timeout)
        self.write_newline()
        _t1 = self.waitfor(self.UNIQIDENTIFIER, self.timeout)
        if _t1 is None:
            return False
        #         print "t1: \n'%s'\n" % t1
        self.write('date "+%D"')
        self.write_newline()
        _t2 = self.waitfor(r"\d{2}/\d{2}/\d{2}", self.timeout)
        if _t2 is None:
            return False
        #         print "t2: \n'%s'\n" % t2
        self.write_newline()
        self.waitfor(self.UNIQIDENTIFIER, self.timeout)
        self.write_newline()
        self.waitfor(self.UNIQIDENTIFIER, self.timeout)
        return True

    def printlog(self):
        """print the log of the connection"""
        print(self.txt)

    def svcalive(self):
        """check if the service is alive"""
        raise NotImplementedError

    def connected(self):
        """return true if the connection is alive"""
        if not self.svcalive():
            return False
        if not me.check_pid(self.child_pid):
            os.waitpid(self.child_pid, os.WNOHANG)
            return False
        result = select.select([self.pty_fd], [self.pty_fd], [self.pty_fd])
        if not result[1] or result[2]:
            return False
        if result[0]:
            return True
        return True

    def __del__(self):
        if self.child_pid:
            os.kill(self.child_pid, signal.SIGKILL)
            os.waitpid(self.child_pid, os.WNOHANG)
