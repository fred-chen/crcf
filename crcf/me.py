"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

import os
import socket
import re
import time
import pty
import select
from shutil import copyfile
import subprocess
from typing import List, Tuple


def get_status_output(*args, **kwargs) -> Tuple[int, str, str]:
    """Run a command with arguments and return its exit status as well as its output.

    Returns:
        Tuple[int, str, str]: exit status, stdout, stderr
    """
    process = subprocess.Popen(
        *args, **kwargs, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout.decode("utf-8"), stderr.decode("utf-8")


def is_path_executable(path):
    """
    check whether a path is existed and executable. return boolean.
    """
    if os.access(path, os.F_OK | os.X_OK):
        return True

    return False


def is_command_existed(cmd):
    """
    invoke 'which' command to case_test whether an os command existed.
    suppose 'which' command should always present
    if command doesn't not exist return None
    if command exists return a string object containing the path of command
    """
    status, output, _err = get_status_output(f"which {cmd}")
    if status != 0:
        return None
    else:
        return output.strip()


def is_command_executable(cmd):
    """
    return true if cmd is executable for real uid/gid
    otherwise return false
    """
    cmdpath = is_command_existed(cmd)
    if cmdpath and is_path_executable(cmdpath):
        return True
    else:
        return False


def check_pid(pid):
    """Check For the existence of a unix pid."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def is_server_svc_alive(host="127.0.0.1", svc=22, timeout=None):
    """
    check whether the TCP service of a given host is being listened or not
    parameters: host - hostname or ip address
                svc - can be an integer port number or a string service name
    exceptions: None
    return:     True if server tcp port is up
                False if server tcp port is down
    dependency: Os independent
    """
    port_num = 0
    if isinstance(svc, str):
        if svc.isdigit():
            port_num = int(svc)
        else:
            port_num = socket.getservbyname(
                svc, "tcp"
            )  # could raise exception: socket.error: service/proto not found
    else:
        port_num = svc
    return _is_server_port_alive(host, port_num, timeout)


def _is_server_port_alive(host: str, port: int, timeout: int = None) -> bool:
    """
    check whether the TCP port of a given host is being listened or not

    Arguments:
        host (str):  hostname or ip address
        port (int):  must be an integer port number

    Exceptions: none

    Return:
        bool: True if server port is up, False if server port is down
    """
    sock = socket.socket()
    try:
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return True
    except socket.error as _msg:
        sock.close()
        return False


def expect(
    cmd: str,
    patterns: Tuple[Tuple[str, str]] = (),
    ignorecase: bool = False,
    timeout: int = 0,
):
    """create a pseudo pty and execute a command

    wait for a specific pattern then send a response if specified

    Args:
        cmd (str): command line to execute
        patters (Tuple[Tuple[pattern, resp]]): pattern is a regular expression,
        resp is a response string to send back to the pty if pattern is matched.

    Returns:
        Tuple[str, int]: (output, returncode) of command
    """
    dur = 0
    regs = []  # [(reg, resp), ...]
    for pattern in patterns:
        pat, resp = pattern
        regs.append(
            (
                re.compile(pat, re.IGNORECASE | re.DOTALL if ignorecase else re.DOTALL),
                resp,
            )
        )

    child_pid = 0
    pty_fd = 0
    args = cmd.split()
    (pid, filedes) = pty.fork()
    if pid == 0:
        os.execvp(args[0], args)
    else:
        child_pid = pid
        pty_fd = filedes
    txt = ""
    dur = 0
    start = time.time()
    while True:
        try:
            result = select.select([pty_fd], [], [], 1)
            if result[0]:
                line = os.read(pty_fd, 4096).decode("utf-8")
                txt += line
                for reg in regs:
                    pattern, resp = reg
                    match = pattern.search(line)
                    if match:
                        if resp:
                            os.write(pty_fd, (resp + "\n").encode("utf-8"))
        except OSError as _err:  # child process ended
            break
        dur = time.time() - start
        if timeout and dur >= timeout:
            os.kill(child_pid, 9)  # timeout, no reason to keep running the command
            break
    pid, rtcode = os.waitpid(child_pid, 0)
    return (txt, rtcode)


def lspath(path) -> List[str]:
    """expand a wildcard filenames

    Args:
        path (str): a path with wildcard

    Returns:
        List[str]: a list of absolute paths of filenames
    """
    status, output, _err = get_status_output(f"ls -d {path}")
    if status != 0:
        return None
    return output.split()


def exe(cmd: str) -> Tuple[int, str, str]:
    """ run a local command.

    Args:
        cmd (str): command to execute

    Return:
        Tuple[int, str, str]: (rtcode, stdout, stderr)
    """
    with subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as proc:
        rtcode = proc.wait()
        stdout = proc.stdout.read().strip()
        stderr = proc.stderr.read().strip()
        return (rtcode, stdout, stderr)


def getlist(cmd: str, splitter="\r\n") -> list:
    """return a list of strings from stdout of a command

    Args:
        cmd (str): command to execute
        splitter (str, optional): the substr used to split the stdout. Defaults to '\r\n'.

    Returns:
        list: a list of strings
    """
    _rt, stdout, _stderr = exe(cmd)
    return stdout.strip().split(splitter) if stdout.stdout.strip() else []


def getint(cmd: str) -> int:
    """return an integer from stdout of a command

    Args:
        cmd (str): command to execute

    Returns:
        int: an integer
    """
    _rt, stdout, _stderr = exe(cmd)
    try:
        result = int(stdout.strip())
    except ValueError:
        result = None
    return result


def getfloat(cmd: str) -> float:
    """return a float from stdout of a command

    Args:
        cmd (str): command to execute

    Returns:
        float: a float
    """
    _rt, stdout, _stderr = exe(cmd)
    try:
        result = float(stdout.strip())
    except ValueError:
        result = None
    return result


def succ(cmd: str) -> bool:
    """return true if the command is executed successfully

    Args:
        cmd (str): command to execute

    Returns:
        bool: true if the command is executed successfully
    """
    rtcode, _stdout, _stderr = exe(cmd)
    return rtcode == 0


def fail(cmd: str) -> bool:
    """return true if the command is executed unsuccessfully

    Args:
        cmd (str): command to execute

    Returns:
        bool: true if the command is executed unsuccessfully
    """
    return not succ(cmd)


def copy(src: str, dst: str) -> bool:
    """copy a file

    Args:
        src (str): source file
        dst (str): destination file

    Returns:
        bool: true if the file is copied successfully
    """
    return copyfile(src, dst)
