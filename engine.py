from localization import tr
"""Validated, UI-independent activity workers. No Tk calls belong here."""
from dataclasses import dataclass, replace
import math
import random
import time
from keycodes import SUPPORTED_KEYS, MODIFIERS

def bounded(value, low, high, name):
    if type(value) not in (int,float) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(tr('ui.cd3ae9b9c721', v0=name, v1=low, v2=high))

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
        if type(self.natural) is not bool or type(self.word_pauses) is not bool or any(type(value) is not int for value in (self.delay_ms,self.min_ms,self.max_ms)):
            raise ValueError(tr('typing.invalid_types'))
        bounded(self.start_delay, 0, 60, tr('ui.956093d278da'))
        if self.delay_ms not in (-1, 30, 60, 100, 150, 250):
            raise ValueError(tr('ui.a4c13fb8286a'))
        bounded(self.min_ms, 10, 5000, tr('ui.4a278980a5ab'))
        bounded(self.max_ms, self.min_ms, 5000, tr('ui.0d4c03cfb2b7'))
        if self.newline not in ('space', 'ignore', 'shift_enter'):
            raise ValueError(tr('ui.f4cab0ffeb13'))
        return self

    def delay(self):
        value = random.uniform(self.min_ms, self.max_ms) if self.delay_ms == -1 else self.delay_ms
        return value / 1000 * (random.uniform(0.7, 1.3) if self.natural else 1)

    def transformed(self, text):
        return text.replace('\n', ' ' if self.newline == 'space' else '') if self.newline != 'shift_enter' else text

    def estimate(self, text, include_start=True):
        text = self.transformed(text)
        delay = (self.min_ms + self.max_ms) / 2000 if self.delay_ms == -1 else self.delay_ms / 1000
        pauses = sum((c == ' ' and i > 0 and (text[i - 1] != ' ') for i, c in enumerate(text))) if self.word_pauses else 0
        return (len(text) + pauses * 2) * delay + (self.start_delay if include_start and text else 0)

@dataclass(frozen=True)
class JigglerConfig:
    idle_threshold: float = 60
    interval: float = 30
    distance: float = 1
    movement: str = 'horizontal_return'
    duration_ms: float = 80
    key: str | None = None
    modifiers: tuple = ()

    def validate(self):
        bounded(self.idle_threshold, 5, 3600, tr('activity.idle'))
        bounded(self.interval, 5, 3600, tr('activity.interval'))
        bounded(self.distance, 1, 100, tr('activity.distance'))
        bounded(self.duration_ms, 50, 1000, tr('activity.duration'))
        if self.movement not in ('off','horizontal_return','vertical_return','square'):
            raise ValueError(tr('activity.invalid'))
        if self.key is not None and self.key not in SUPPORTED_KEYS:
            raise ValueError(tr('activity.invalid_key'))
        if not isinstance(self.modifiers,(list,tuple)) or any(m not in MODIFIERS for m in self.modifiers) or len(set(self.modifiers)) != len(self.modifiers):
            raise ValueError(tr('activity.invalid_key'))
        if (self.modifiers and self.key is None) or (self.movement == 'off' and self.key is None):
            raise ValueError(tr('activity.empty'))
        return replace(self,modifiers=tuple(self.modifiers))


class JigglerSchedule:

    def __init__(self, config):
        self.config = config.validate()
        self.last = None

    def due(self, now, idle, typing):
        return not typing and idle >= self.config.idle_threshold and (self.last is None or now - self.last >= self.config.interval)

    def record(self, now):
        self.last = now

def type_text(text, config, backend, stop, events):
    failure=None
    try:
        config.validate()
        deadline = time.monotonic() + config.start_delay
        while not stop.is_set() and time.monotonic() < deadline:
            events.put(('countdown', max(0, deadline - time.monotonic())))
            stop.wait(min(0.1, max(0, deadline - time.monotonic())))
        if not stop.is_set():
            if hasattr(backend,'begin_typing'):backend.begin_typing(text,config,stop)
            events.put(('typing', None))
        previous = ''
        for index, char in enumerate(text):
            if stop.is_set():
                break
            if char == '\n':
                if config.newline == 'space':
                    backend.write(' ')
                elif config.newline == 'shift_enter':
                    backend.newline()
            else:
                backend.write(char)
            events.put(('progress', index + 1))
            if char != '\n' or config.newline != 'ignore':
                delay = config.delay()
                stop.wait(delay * (3 if config.word_pauses and char == ' ' and (previous != ' ') else 1))
            previous = ' ' if char == '\n' and config.newline == 'space' else char
    except Exception as exc:
        failure=str(exc)
    finally:
        try:
            if hasattr(backend,'end_typing'):backend.end_typing()
        except Exception as exc:
            failure=f'{failure}; {exc}' if failure else str(exc)
    events.put(('error',failure) if failure else ('stopped' if stop.is_set() else 'finished',None))

def jiggle(config, backend, stop, typing_active, events):
    schedule = JigglerSchedule(config)
    count = 0
    try:
        while not stop.is_set():
            now = time.monotonic()
            idle = backend.idle_seconds()
            if schedule.due(now, idle, typing_active()):
                if backend.micro_activity(config, stop):
                    count += 1
                    events.put(('movement', count))
                schedule.record(time.monotonic())
            events.put(('idle', idle))
            stop.wait(0.5)
        events.put(('jiggler_stopped', None))
    except Exception as exc:
        events.put(('jiggler_error', str(exc)))
