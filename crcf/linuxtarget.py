"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

from .uxtarget import UxTarget


class LinuxTarget(UxTarget):
    """LinuxTarget is an implementation of UxTarget for Linux"""

    def __init__(
        self, address, svc="ssh", username="root", password=None, conn=None, timeout=60
    ):
        UxTarget.__init__(self, address, svc, username, password, conn, timeout)
        self.newline = "\n"

    def panic(self, log=True):
        if log:
            self.log(f"panicing {self.address}")
        self.shell.conn.write("echo 0 >/proc/sys/kernel/panic")
        self.shell.conn.write_newline()
        self.shell.conn.write("echo 1 > /proc/sys/kernel/sysrq")
        self.shell.conn.write_newline()
        self.shell.conn.write("echo c > /proc/sysrq-trigger")
        self.shell.conn.write_newline()
        if log:
            self.log(f"{self.address} paniced.")

    def panicreboot(self, wait=True, log=True):
        if log:
            self.log(f"panic rebooting {self.address}")
        self.shell.conn.write("echo 1 >/proc/sys/kernel/panic")
        self.shell.conn.write_newline()
        self.shell.conn.write("echo 1 > /proc/sys/kernel/sysrq")
        self.shell.conn.write_newline()
        self.shell.conn.write("echo c > /proc/sysrq-trigger")
        self.shell.conn.write_newline()
        if wait:
            self.wait_alive()
            if log:
                self.log(f"{self.address} is back online.")
