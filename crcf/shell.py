"""
Created on Aug 25, 2018

@author: fred

===============================================================================

DESCRIPTION:
----------------
    This module provides a shell object to run commands on a target. A shell
    object is created by calling the target.newshell() method. It represents a
    connected pseudo terminal (pty) on the target.

    The shell object is a thread, which runs in the background. It has a queue
    to receive commands to be run. The commands are run in the order they are
    received.

    A target object can have multiple shell objects associated on it. With
    asynchroneous remote execution, a shell object can run multiple commands
    simultaneously.

    "shell.exe()"
    --------------
    The most important method of shell objects is "shell.exe()", which sends a
    command string to the target by writing the command string through the
    connection object it associates to. The exe function returns a "Command"
    object to the caller after the command line is successfully sent. By default
    "shell.exe(wait=True)" will wait for the command to be executed and returned
    from the remote target, but it can be configured to return immediately by
    calling "shell.exe(wait=False)". This is called an "Asynchronous Remote
    Execution". The exe funtion returns immediately to the caller with an
    Command object while the command is still being executed on the remote
    target. Then the caller can check the result later by checking the Command
    object. Command object contains the command line, the output, the error, the
    exit code, and the duration of the command.

"""

from queue import Queue
import threading
import random
import re
import datetime
import time
import uuid
from .common import Common
from .connfactory import connect
from .command import Command


class Shell(Common, threading.Thread):
    """Shell object represents a connected pseudo terminal (pty) on the target.

    User can create a shell object by calling the target.newshell() method. With
    a shell object, user can run commands on the target by calling shell.exe()
    method. The exe() method returns a Command object to the caller. The Command
    object contains the command line, the output, the error, the exit code, and
    the duration of the command.
    """

    def __init__(self, target, conn=None, timeout=300):
        threading.Thread.__init__(self)
        self.queuq = Queue()
        self.target = target
        self.conn = conn
        self.timeout = timeout
        self.shell_id = str(uuid.uuid4()).split("-", maxsplit=1)[0]
        self.__connect()
        self.setDaemon(True)
        self.start()

    def __connect(self):
        """connect to the target and set up the shell."""
        # Always create a fresh connection for each shell.
        # SSH connections cannot be reused after running commands on them
        # (e.g. the test command in gettarget() leaves the SSH process in
        # an inconsistent state), so we must always establish a new one.
        self.conn = connect(
            self.target.address,
            self.target.username,
            self.target.password,
            self.target.svc,
            self.target.timeout,
            self.target.newline,
        )
        self.__setshell()
        return self.conn

    def __setshell(self):
        self.conn.write("set +H")
        self.conn.write_newline()
        self.conn.write(
            'trap ctrl_c INT && function ctrl_c() { echo "Trapped CTRL-C"; }'
        )
        self.conn.write_newline()

    def __reconnect(self):
        self.__disconnect()
        return self.__connect()

    def __disconnect(self):
        if self.conn:
            self.conn.disconnect()
        self.conn = None

    def exe(
        self, cmdline, wait=True, log=True, longrun_report=1800, wait_report=30
    ) -> Command:
        """
        put a command into q, wait (not not to wait) for it to be executed by
        the shelll thread.

        Args:
            cmdline (str): the command line to be run in shell.

            wait (bool, optional): if not wait, return immediately, else wait
            until the command is finished. Defaults to True.

            log (bool, optional): print result when finish. Defaults to True.

            longrun_report (int, optional): time to report progress if no one is
            watching, but a command is talking every long. Defaults to 1800
            seconds.

            wait_report (int, optional): time to report progress when someone is
            watching (calling command.wait()). Defaults to 30 seconds.

        Returns:
            Command object: the command object
        """
        cmdobj = Command(cmdline, log, longrun_report, wait_report)
        cmdobj.shell = self
        self.queuq.put(cmdobj)
        if wait:
            cmdobj.wait()
        return cmdobj

    def gettarget(self):
        """return the target object of the shell."""
        return self.target

    def run(self):
        """the thread loop to fetch and run commands in the queue.

        this is a private method. don't call it.
        """
        while True:
            cmdobj = self.queuq.get()
            filename = f"CRCF_{threading.current_thread().ident}_{random.randrange(1000000000)}"
            cmdobj.reserve = filename
            start = datetime.datetime.now()
            for i in range(1, 6):
                broken = False
                if self._sendcmd(cmdobj) is None:
                    broken = True
                start = datetime.datetime.now()
                cmdobj.start = start
                if self._getresults(cmdobj) is None:  # connection broken
                    broken = True
                if broken:
                    dur = 0
                    alive = False
                    timeout = (
                        self.timeout if self.timeout else 900
                    )  # default timeout is 15 minutes
                    self.log(
                        f"connection broken. resending command '{cmdobj.cmdline}'."
                        + f"timeout {timeout} secs, attempt {i} ...",
                        2,
                    )
                    while True:
                        if self.target.alive():
                            alive = True
                            break
                        time.sleep(1)
                        dur += 1
                        if dur > timeout:
                            break
                    if alive:
                        self.__reconnect()
                    continue
                else:
                    break
            diff = datetime.datetime.now() - start
            cmdobj.dur = diff.total_seconds() * 1000
            cmdobj.setdone()

    def _sendcmd(self, cmdobj: Command):
        cmdline = cmdobj.cmdline.replace('"', r"\"")
        cmd = f"FN=/tmp/{cmdobj.reserve};"
        # we use 'tee' because we also want to capture the terminal screen of
        # the command, so we can monitor the long running commands
        cmd += (
            'eval "%s" > >(tee ${FN}.out) 2> >(tee ${FN}.err >&2);' % (cmdline)
            + 'echo $?>${FN}.exit; stdbuf -o0 echo -ne " ";'
        )
        # cmd += f'eval "{cmdline}" > $FN.out 2>$FN.err; echo $?>$FN.exit;
        # stdbuf -o0 echo -ne " ";' wait for output files to be generated
        cmd += "while [ ! -e ${FN}.out ]; do continue; done; sync ${FN}.out;"
        cmd += "echo ==${FN}START==;"
        cmd += "cat ${FN}.out;echo ==OUTEND==;"
        cmd += "cat ${FN}.err;echo ==ERREND==;"
        cmd += "cat ${FN}.exit;echo ==EXITEND==;"
        cmd += "echo ==${FN}END==;"
        cmd += "rm -f ${FN}.out ${FN}.err ${FN}.exit"
        if (not self.conn) or self.conn.write(cmd) is None:
            return None
        return self.conn.write_newline()

    def _getresults(self, cmdobj: Command):
        txt = None
        reg_screen = re.compile(
            f"==/tmp/{cmdobj.reserve}START==(.+)==OUTEND=="
            + f"(.+)==ERREND==(.+)==EXITEND==.+==/tmp/{cmdobj.reserve}END==",
            re.DOTALL,
        )
        cmdobj.screentext = ""
        if self.conn:
            while True:
                txt = self.conn.waitfor(f"==/tmp/{cmdobj.reserve}END==", 1)
                if txt is None:  # connection broken
                    cmdobj.stdout = None
                    cmdobj.stderr = None
                    cmdobj.exit = None
                    return txt
                cmdobj.screentext += txt.replace(self.UNIQIDENTIFIER, "")
                match = reg_screen.search(cmdobj.screentext)
                if match:  # command finished
                    break
                dur = datetime.datetime.now() - cmdobj.start
                if int(dur.total_seconds()) == 1:  # report command running for one time
                    self.log(f"running '{cmdobj.cmdline}'")
                if cmdobj.longrun_report:
                    if (
                        dur.total_seconds() >= cmdobj.longrun_report
                        and int(dur.total_seconds()) % cmdobj.longrun_report == 0
                    ):
                        self.log(
                            f"command has been running for {dur.total_seconds()} seconds."
                            + f"{cmdobj}\n\n"
                        )
        else:  # connection broken
            cmdobj.stdout = None
            cmdobj.stderr = None
            cmdobj.exit = None
            return txt
        match = reg_screen.search(cmdobj.screentext)
        cmdobj.stdout = match.group(1)
        cmdobj.stderr = match.group(2)
        cmdobj.exit = match.group(3)
        # print("screen:\n%s" % cmdobj.screentext)  # for debug
        return txt

    def interrupt(self, send="\x03"):
        """terminate the current command with 'ctrl-c' ('\x03')

        Args:
            send (str, optional): the control character to terminate the current
            forground process. Defaults to '\x03'.
        """
        self.conn.write(send)

    def log(self, msg, level=3):
        Common.log(self, f"[{self.target}({self.shell_id})]: {msg}", level)
