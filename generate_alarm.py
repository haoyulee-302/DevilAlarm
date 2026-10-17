"""Generate the alarm without third-party dependencies."""
from array import array
from pathlib import Path
import math
import sys
import wave


def generate_beep(filename=None, duration=.5, freq=1000, sample_rate=44100):
    filename = filename or Path(__file__).resolve().with_name("alarm.wav")
    if duration <= 0 or sample_rate <= 0:
        raise ValueError("duration and sample_rate must be positive")
    samples = array("h", (
        int(18000 * math.sin(2 * math.pi * freq * i / sample_rate))
        if int(i / (duration * sample_rate)) % 2 == 0 else 0
        for i in range(5 * sample_rate)
    ))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(filename), "wb") as output:
        output.setparams((1, 2, sample_rate, 0, "NONE", "not compressed"))
        output.writeframes(samples.tobytes())


if __name__ == "__main__":
    generate_beep()
