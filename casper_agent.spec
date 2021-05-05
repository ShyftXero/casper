# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['casper_agent.py'],
             pathex=['/home/shyft/Dropbox/code/casper'],
             binaries=[],
             datas=[('ops', 'ops'), ('/home/shyft/stuff/miniconda3/lib/python3.9/site-packages/pyppeteer-0.2.5.dist-info', 'pyppeteer-0.2.5.dist-info')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='casper_agent',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='casper_agent')
