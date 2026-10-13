"""Validated, UI-independent activity workers. No Tk calls belong here."""
from dataclasses import dataclass
import math
import random
import time


def bounded(value, low, high, name):
    if not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f'{name}: {low}–{high} aralığında bir sayı girin.')


@dataclass(frozen=True)
class TypingConfig:
    delay_ms: int = 100
    start_delay: float = 3
    min_ms: int = 10
    max_ms: int = 5000
    natural: bool = False
    word_pauses: bool = False
    newline: str = 'space'

    def validate(self):
        bounded(self.start_delay, 0, 60, 'Başlangıç süresi')
        if self.delay_ms not in (-1, 30, 60, 100, 150, 250, 1):
            raise ValueError('Geçersiz hız.')
        bounded(self.min_ms, 10, 5000, 'En kısa bekleme')
        bounded(self.max_ms, self.min_ms, 5000, 'En uzun bekleme')
        if self.newline not in ('space', 'ignore', 'shift_enter'):
            raise ValueError('Geçersiz satır davranışı.')
        return self

    def delay(self):
        value = random.uniform(self.min_ms, self.max_ms) if self.delay_ms == -1 else self.delay_ms
        return value / 1000 * (random.uniform(.7, 1.3) if self.natural else 1)

    def transformed(self, text):
        return text.replace('\n', ' ' if self.newline == 'space' else '') if self.newline != 'shift_enter' else text

    def estimate(self, text, include_start=True):
        text = self.transformed(text)
        delay = (self.min_ms + self.max_ms) / 2000 if self.delay_ms == -1 else self.delay_ms / 1000
        pauses = sum(c == ' ' and i > 0 and text[i-1] != ' ' for i, c in enumerate(text)) if self.word_pauses else 0
        return (len(text) + pauses * 2) * delay + (self.start_delay if include_start and text else 0)


@dataclass(frozen=True)
class JigglerConfig:
    idle_threshold: float = 60
    interval: float = 30
    f18: bool = False

    def validate(self):
        bounded(self.idle_threshold, 5, 3600, 'Boşta kalma süresi')
        bounded(self.interval, 5, 3600, 'Hareket aralığı')
        return self


class JigglerSchedule:
    def __init__(self, config): self.config = config.validate(); self.last = None
    def due(self, now, idle, typing):
        return not typing and idle >= self.config.idle_threshold and (self.last is None or now - self.last >= self.config.interval)
    def record(self, now): self.last = now


def type_text(text, config, backend, stop, events):
    try:
        config.validate()
        deadline = time.monotonic() + config.start_delay
        while not stop.is_set() and time.monotonic() < deadline:
            events.put(('countdown', max(0, deadline - time.monotonic())))
            stop.wait(min(.1, max(0, deadline - time.monotonic())))
        if not stop.is_set(): events.put(('typing', None))
        previous = ''
        for index, char in enumerate(text):
            if stop.is_set(): break
            if char == '\n':
                if config.newline == 'space': backend.write(' ')
                elif config.newline == 'shift_enter': backend.newline()
            else: backend.write(char)
            events.put(('progress', index + 1))
            if char != '\n' or config.newline != 'ignore':
                delay = config.delay()
                stop.wait(delay * (3 if config.word_pauses and char == ' ' and previous != ' ' else 1))
            previous = ' ' if char == '\n' and config.newline == 'space' else char
        events.put(('stopped' if stop.is_set() else 'finished', None))
    except Exception as exc: events.put(('error', str(exc)))


def jiggle(config, backend, stop, typing_active, events):
    schedule = JigglerSchedule(config)
    count = 0
    try:
        while not stop.is_set():
            now = time.monotonic()
            idle = backend.idle_seconds()
            if schedule.due(now, idle, typing_active()):
                if backend.micro_activity(config.f18, stop):
                    count += 1; events.put(('movement', count))
                schedule.record(time.monotonic())
            events.put(('idle', idle))
            stop.wait(.5)
        events.put(('jiggler_stopped', None))
    except Exception as exc: events.put(('jiggler_error', str(exc)))
