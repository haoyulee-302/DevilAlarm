from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import wave

import main
from generate_alarm import generate_beep


class ScheduleTests(unittest.TestCase):
    def test_midnight_and_elapsed_time(self):
        self.assertEqual(main.next_alarm(0, 0, datetime(2026, 10, 17, 23, 59, 30)), datetime(2026, 10, 18))
        self.assertEqual(main.next_alarm(8, 0, datetime(2026, 10, 17, 8, 0, 30)), datetime(2026, 10, 18, 8))
        self.assertEqual(main.next_alarm(8, 1, datetime(2026, 10, 17, 8, 0, 30)), datetime(2026, 10, 17, 8, 1))

    def test_wave_generation(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as folder:
            path = Path(folder) / 'alarm.wav'
            generate_beep(path)
            with wave.open(str(path)) as sound:
                self.assertEqual(sound.getnframes(), 220500)
                self.assertEqual(sound.getnchannels(), 1)

    def test_posture_rejects_invisible_or_horizontal_body(self):
        names = ['LEFT_SHOULDER', 'RIGHT_SHOULDER', 'LEFT_HIP', 'RIGHT_HIP', 'LEFT_KNEE', 'RIGHT_KNEE']
        api = SimpleNamespace(PoseLandmark=SimpleNamespace(**{name: SimpleNamespace(value=i) for i, name in enumerate(names)}))
        points = [SimpleNamespace(x=.5, y=y, visibility=1) for y in (.2, .2, .5, .5, .8, .8)]
        self.assertTrue(main.check_standing_waving_posture(points, api)[0])
        points[0].visibility = .1
        self.assertFalse(main.check_standing_waving_posture(points, api)[0])
        for point in points:
            point.visibility, point.y = 1, .5
        self.assertFalse(main.check_standing_waving_posture(points, api)[0])


class UITests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.settings = patch.object(main, 'SETTINGS', Path(self.folder.name) / 'settings.json')
        self.settings.start()
        self.app = main.AlarmUI()
        self.app.voice.set(False)
        self.app.update()

    def tearDown(self):
        self.app.close()
        self.settings.stop()
        self.folder.cleanup()

    def test_delayed_tick_still_rings_and_cancel_rearms(self):
        self.app.arm()
        self.app.target = datetime.now() - timedelta(minutes=2)
        with patch.object(self.app, 'ring') as ring:
            self.app.tick()
            ring.assert_called_once()
        self.app.cancel()
        self.assertIsNone(self.app.target)
        self.app.arm()
        self.assertIsNotNone(self.app.target)
        self.assertNotIn('key', main.SETTINGS.read_text())

    def test_stale_voice_completion_does_not_affect_new_schedule(self):
        self.app.arm()
        old_session = self.app.session
        self.app.cancel()
        self.app.arm()
        self.app.events.put((old_session, 'voice', ['stale.mp3']))
        self.app.tick()
        self.assertEqual(self.app.voices, [])
        self.app.events.put((self.app.session, 'voice', ['new.mp3']))
        self.app.tick()
        self.assertEqual(self.app.voices, ['new.mp3'])

    def test_image_render_and_minimum_layout(self):
        self.app.geometry('1000x760')
        self.app.update()
        pixels = b'P6\n480 300\n255\n' + bytes([20, 30, 40]) * (480 * 300)
        self.app.frames.put((self.app.session, pixels, .5, '測試站姿'))
        self.app.tick()
        self.app.update()
        self.assertLessEqual(self.app.photo.width(), self.app.preview_label.winfo_width())
        self.assertAlmostEqual(self.app.photo.width() / self.app.photo.height(), 480 / 300, delta=.02)
        self.assertLessEqual(self.app.start_btn.winfo_rooty() + self.app.start_btn.winfo_height(), self.app.winfo_rooty() + self.app.winfo_height())

    def test_layout_scaling_is_reversible_and_fonts_are_native_pixels(self):
        self.app.display_scaling.apply(1.5)
        self.app.update()
        def pixel_size():
            return int(self.app.tk.splitlist(self.app.countdown.cget('font'))[1])
        self.assertEqual(pixel_size(), -56)
        self.app.display_scaling.apply(2)
        self.assertEqual(pixel_size(), -75)
        self.app.display_scaling.apply(1)
        self.assertEqual(pixel_size(), -37)


if __name__ == '__main__':
    unittest.main()

