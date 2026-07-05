"""
Created on Aug 25, 2018

@author: fred

===============================================================================
"""

from .uxtarget import UxTarget


class HpuxTarget(UxTarget):
    """HpuxTarget is an implementation of UxTarget for HP-UX"""

    def panic(self, log=True):
        pass

    def panicreboot(self, wait=True, log=True):
        pass
