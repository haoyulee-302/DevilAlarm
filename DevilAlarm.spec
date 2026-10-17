# Build with: .venv-alarm\Scripts\python.exe -m PyInstaller --noconfirm DevilAlarm.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata

root = Path(SPECPATH)
assets = [(str(root / name), '.') for name in ('alarm.wav', 'roast_0.mp3', 'roast_1.mp3', 'roast_2.mp3', 'app.ico')]
assets += collect_data_files('mediapipe')
assets += copy_metadata('edge-tts')
analysis = Analysis(
    [str(root / 'launcher.py')],
    pathex=[str(root)],
    binaries=collect_dynamic_libs('mediapipe'),
    datas=assets,
    hiddenimports=['PIL._tkinter_finder', 'matplotlib.backends.backend_agg'],
    hookspath=[],
    hooksconfig={'matplotlib': {'backends': ['Agg']}},
    runtime_hooks=[],
    excludes=['jax', 'jaxlib', 'tensorflow', 'torch', 'IPython', 'pytest',
              'mediapipe.tasks.python.genai.converter'],
    noarchive=False,
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, analysis.binaries, analysis.datas, [],
    name='DevilAlarm', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
    disable_windowed_traceback=False, icon=str(root / 'app.ico'),
)
