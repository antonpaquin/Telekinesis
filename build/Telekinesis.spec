# -*- mode: python -*-

block_cipher = None


a = Analysis(['/home/anton/Programming/Telekinesis/src/run.py'],
             pathex=[
                '/home/anton/Programming/Telekinesis/env/lib/python3.6/site-packages',
             ],
             binaries=[],
             datas=[
                ('../src/telekinesis/swaggerfile.json', 'telekinesis'),
                ('../src/telekinesis/Gatekeeper/gatekeeper.sql', 'telekinesis/Gatekeeper'),
                ('../src/telekinesis/models/script.sql', 'telekinesis/models'),
                ('../src/telekinesis/models/create_db.sql', 'telekinesis/models'),
             ],
             hiddenimports=[
                'packaging.version', 
                'packaging.specifiers', 
                'packaging.requirements',
                'appdirs',
                'gunicorn.glogging',
                'gunicorn.workers.sync',
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='run',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
