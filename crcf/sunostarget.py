"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

from .uxtarget import UxTarget


class SunOSTarget(UxTarget):
    """this class an Target implementation for SunOS"""

    def panic(self, log=True):
        pass

    def panicreboot(self, wait=True, log=True):
        pass
