"""Windowed executable entry point and offline packaging diagnostics."""
import json
import os
from pathlib import Path
import sys
import traceback

os.environ.setdefault('MPLBACKEND', 'Agg')
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8')


def self_test():
    import main
    import cv2
    import mediapipe as mp
    import numpy as np
    import pygame
    import edge_tts
    from PIL import Image, ImageTk
    from app_paths import ASSET_DIR, SETTINGS, FROZEN
    app = main.AlarmUI()
    try:
        app.withdraw()
        app.update()
        image = Image.new('RGB', (640, 360), (30, 40, 50))
        photo = ImageTk.PhotoImage(image, master=app)
        assert photo.width() == 640
        dpi = app.last_dpi
    finally:
        app.close()
    with mp.solutions.pose.Pose() as pose:
        result = pose.process(np.zeros((480, 640, 3), dtype=np.uint8))
        assert result.pose_landmarks is None
    assert cv2.cvtColor(np.zeros((2, 2, 3), dtype=np.uint8), cv2.COLOR_BGR2RGB).shape == (2, 2, 3)
    pygame.mixer.init()
    try:
        sound = pygame.mixer.Sound(str(ASSET_DIR / 'alarm.wav'))
        assert sound.get_length() > 0
        for i in range(3):
            pygame.mixer.music.load(str(ASSET_DIR / f'roast_{i}.mp3'))
        pygame.mixer.music.unload()
    finally:
        pygame.mixer.quit()
    edge_tts.Communicate('早安', 'zh-TW-HsiaoChenNeural', rate='+50%', pitch='+10Hz')
    assert not (ASSET_DIR / 'api_key.txt').exists()
    if FROZEN:
        assert SETTINGS.parent != ASSET_DIR
    return dict(ok=True, frozen=FROZEN, dpi=dpi, checks=['GUI', 'Pillow', 'OpenCV', 'MediaPipe pose model',
        'WAV and MP3 decode', 'TTS configuration', 'persistent settings path', 'no bundled API key'],
        settings_path=str(SETTINGS))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        report = Path(sys.argv[2]).resolve()
        try:
            result = self_test()
        except Exception:
            result = dict(ok=False, error=traceback.format_exc())
        report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        raise SystemExit(0 if result['ok'] else 1)
    try:
        from main import main
        main()
    except Exception:
        from app_paths import STATE_DIR
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        log = STATE_DIR / 'startup-error.log'
        log.write_text(traceback.format_exc(), encoding='utf-8')
        from tkinter import messagebox
        messagebox.showerror('惡魔鬧鐘無法啟動', f'請查看錯誤記錄：\n{log}')
        raise SystemExit(1)
