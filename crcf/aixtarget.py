"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

from .uxtarget import UxTarget


class AixTarget(UxTarget):
    """AixTarget is a class for AIX target"""

    def panic(self, log=True):
        pass

    def panicreboot(self, wait=True, log=True):
        pass
