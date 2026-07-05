from crcf import gettarget

t = gettarget("pro.chenp.net")
shell = t.newshell()
command = shell.exe("echo Hello CRCF!")
if command.succ():
    print("Command succeeded")
else:
    print("Command failed with code %d: %s" % (command.get_exitcode(), command.get_cmdline()))
