# vim:set syntax=python:
# -*- mode: python -*-

import os
import sys

exe_name = "net_flow_vizu_dia.exe"

a = Analysis([os.path.join(HOMEPATH,"support/_mountzlib.py"),
                os.path.join(CONFIGDIR,"support/useUnicode.py"),
                "../net_flow_vizu_dia.py"],
              pathex=[".."])
pyz = PYZ(a.pure)

exe = EXE(pyz,
          a.scripts + [('OO','','OPTION')],
          a.binaries,
          a.zipfiles,

          name=exe_name,
          debug=False,
          strip=False,
          upx=True,
          console=True)
