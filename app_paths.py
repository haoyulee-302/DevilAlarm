"""Keep bundled assets separate from persistent user preferences."""
import os
from pathlib import Path
import sys

ASSET_DIR = Path(__file__).resolve().parent
FROZEN = bool(getattr(sys, 'frozen', False))
STATE_DIR = (Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'DevilAlarm') if FROZEN else ASSET_DIR
SETTINGS = STATE_DIR / 'settings.json'
