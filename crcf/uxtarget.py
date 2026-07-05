"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

import time
import os
from .target import Target
from . import me


class UxTarget(Target):
    """unix, linux like targets

    this kind of targets share similar commands so it makes sense for them to
    share a same parent class.
    """

    def __init__(
        self, address, svc="ssh", username="root", password=None, conn=None, timeout=60
    ):
        self.newline = "\n"
        Target.__init__(self, address, svc, username, password, conn, timeout)

    def gethostname(self):
        if self.hostname:
            return self.hostname
        cmdobj = self.shell.exe("hostname", wait=True, log=False)
        if cmdobj.succ():
            self.hostname = cmdobj.stdout.strip()
        else:
            self.hostname = self.address
        return self.hostname

    def reboot(self, wait=True, log=True):
        if log:
            self.log(f"rebooting {self.address}")
        self.shell.conn.write("reboot")
        self.shell.conn.write_newline()
        # for sh in self.shs:
        #     sh.disconnect()
        self.wait_down()
        if wait:
            self.wait_alive()

    def shutdown(self, wait=True, log=True):
        if log:
            self.log(f"shutting down {self.address}")
        self.shell.conn.write("shutdown -h now")
        self.shell.conn.write_newline()
        # for sh in self.shs:
        #     sh.disconnect()
        if wait:
            while self.alive():
                time.sleep(1)
            self.log(f"{self.address} has been shut down.")

    def _scp(self, src, tgt, log=True, timeout=0):
        """
        for uxtarget, use scp for upload and download
        """
        if log:
            self.log(f"copying {src} to {tgt}")

        if os.path.exists(
            self.password
        ):  # the password is an IdentityFile for ssh authentication
            args = (
                "scp",
                "-q",
                "-r",
                "-p",
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
                f"{src}",
                f"{tgt}",
            )
        else:
            args = (
                "scp",
                "-q",
                "-r",
                "-p",
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
                f"{src}",
                f"{tgt}",
            )
        cmd = " ".join(args)
        output, status = me.expect(cmd, [("password:", self.password)], False, timeout)
        if status != 0:
            self.log(f"error: scp returned {status}:\n{output}", 1)
            return False
        return True

    def upload(self, local_path, remote_path, log=True):
        flist = me.lspath(local_path)
        src_str = " ".join(flist)
        return self._scp(src_str, f"{self.username}@{self.address}:{remote_path}")

    def download(self, local_path, remote_path, log=True):
        cmdobj = self.exe(f"ls -d {remote_path}", wait=True, log=log)
        path_str = " ".join(
            [f"{self.username}@{self.address}:{path}" for path in cmdobj.getlist()]
        )
        return self._scp(path_str, local_path)

    def panic(self, log=True):
        raise NotImplementedError

    def panicreboot(self, wait=True, log=True):
        raise NotImplementedError
