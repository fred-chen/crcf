"""
Created on Aug 25, 2018

@author: fred

===============================================================================

DESCRIPTION
----------------
The CRCF package is a framework for running commands on remote servers. It
leverages multi-threading capability of Python to run hundreds of commands on
multiple servers simultaneously and asychronously. It also provides a simple way
to capture the output and errors of the commands and log them to user screen.

CRCF is the Concurrent Remote Control Framework, trimmed from an older test
framework project. It focuses on concurrent remote device control ability and
optimized logging.

CRCF exposes a set of simple API to the users, which are 1 function and 3
classes::

    def gettarget():
        # This function is used to create a Target object. Which is kind # of
        the entry point of the CRCF framework.

    class Target:
        # A Target object represents a server node, or any other devices.

    class Shell:
        # A Shell object represents a shell session on a server node.

    class Command:
        # A Command object represents a command to be run on a server node.

![image](../doc/design.png)

CRCF intends to be a simple and easy to use framework. The main idea behind CRCF
is to simulate a common use case: a user logs into a bunch of server nodes,
opens many many terminals for each of those nodes, runs commands, maybe reboot
some of them, then logs out. CRCF provides an automatic way to do this. The user
can create as many Target objects as they want, then use the Target object to
create as many Shell objects, each of the Shell objects represents a terminal
to that target. Then use the Shell objects to run Commands. The commands will be
sent to the server nodes and executed by the server nodes, then return the exit
status, output and errors of the commands. The user can then use the output and
errors to determine if the commands were successful or not.

Example
----------------
    # create a target object
    target = gettarget("10.1.0.96", "root", "password")

    # create a shell object associated on the target
    shell  = target.newshell()

    # run a command on the target
    command = shell.exe("banner Hello CRCF!")

    # check the result of a command
    if command.succ():
        print("Command succeeded")
    if command.fail():
        print("Command failed")
    if command.get_exitcode() != 0:
        print("Command failed with exit code: %d" % command.get_exitcode())
    if command.get_output() != "":
        print("Command output: %s" % command.get_output())
    if command.get_error() != "":
        print("Command error: %s" % command.get_error())

    # you can directly get desired type of output from the command object if
    # the output of the command is predictable. for example, if the command
    # is "ls -l", you can get the output as a list of files and directories
    command = shell.exe("ls -l /tmp")
    if command.succ():
        files: list = command.getlist()

    # as for integers
    command = shell.exe("bc <<< '220 * 284'")
    if command.succ():
        result: int = command.getint() # result == 62480

    # and floats
    command = shell.exe("bc -l <<< '284 / 220'")
    if command.succ():
        result: float = command.getfloat() # result == 1.29090909090909090909

    # you can run a command asynchronously
    command = shell.exe("banner Hello CRCF!", wait=False) # return immediately

    # do something else here ...

    # then check the result of the command
    command.wait()  # wait for the command to finish, this is not really necessary
                    # because the .succ() .fail() .get_exitcode() will wait
                    # for the command to finish.
    if command.succ():
        print("Command succeeded")

    # you can reboot the target then wait for it to be back online
    target.reboot()

    # you also can reboot the target without waiting for it to be back online
    target.reboot(wait=False) # return immediately

    # do something else here ...

    # then wait for the target to be back online
    target.wait_online() # wait for the target to be back online

    # you can upload a file to the target
    target.upload("local_file", "remote_file")

    # you can download a file from the target
    target.download("local_file", "remote_file")

    # connect to multiple targets is easy
    target1 = gettarget("10.1.0.91", "root", "password")
    target2 = gettarget("10.1.0.92", "root", "password")
    target3 = gettarget("10.1.0.93", "root", "password")

    # get 10 shells from each of the targets, 30 shells in total
    shells = []
    for target in [target1, target2, target3]:
        for i in range(10):
            shell = target.newshell() shells.append(shell)

    # run a command on all 30 shells (to 3 targets) asynchronously
    commands = []
    for shell in shells:
        command = shell.exe("banner Hello CRCF!", wait=False) # return immediately
        commands.append(command)

    # do something else here ...

    # wait for all 30 commands to finish and check the result
    for command in commands:
        if command.fail():
            print("Command failed with code %d: %s" %
                command.get_exitcode(), command.get_cmdline())

All command execution will be logged via the standard logging module. Users can
configure the logging level, handlers and output targets through
``logging.getLogger("crcf")``.

CRCF is designed to be extensible. It provides a set of base classes to define
some common operations and attributes. For example, the Target class defines a
generic target, which can be a server node, a switch, a router, or any other
device types, its subclasses implement specific types of targets, such as
LinuxTarget, AixTarget, SunOsTarget, etc. The Connection class defines a generic
connection, which can be a telnet connection, an ssh connection, or any other
kinds of connections, its subclasses implement specific types of connections, such
as TelnetConnection, SshConnection, etc. In case any new kinds of targets or
connection types are needed, the user can easily create new subclasses to extend
CRCF.
"""

__pdoc__ = {
    "aixtarget": False,
    "command": False,
    "common": False,
    "connection": False,
    "connfactory": False,
    "hpuxtarget": False,
    "linuxtarget": False,
    "me": False,
    "rshconnection": False,
    "shell": False,
    "sshconnection": False,
    "sunostarget": False,
    "target": False,
    "targetfactory": False,
    "telnetconnection": False,
    "uxtarget": False,
}

from .target import Target
from .targetfactory import gettarget
from .shell import Shell
from .command import Command

__all__ = ["Target", "gettarget", "Shell", "Command"]
