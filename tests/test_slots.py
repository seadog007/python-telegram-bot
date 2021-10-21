#!/usr/bin/env python
#
# A library that provides a Python interface to the Telegram Bot API
# Copyright (C) 2015-2021
# Leandro Toledo de Souza <devs@python-telegram-bot.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
import importlib
import importlib.util
import os
from glob import iglob

import inspect
from pathlib import Path

included = {  # These modules/classes intentionally have __dict__.
    'CallbackContext',
    'BasePersistence',
    'Dispatcher',
}


def test_class_has_slots_and_no_dict():
    request_init = str(Path("telegram/request/__init__.py"))
    tg_paths = [path for path in iglob("telegram/**/*.py", recursive=True) if path != request_init]

    for path in tg_paths:
        # windows uses backslashes:
        if os.name == 'nt':
            split_path = path.split('\\')
        else:
            split_path = path.split('/')
        mod_name = f"telegram{'.ext.' if split_path[1] == 'ext' else '.'}{split_path[-1][:-3]}"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # Exec module to get classes in it.

        for name, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__ or any(  # exclude 'imported' modules
                x in name for x in {'__class__', '__init__', 'Queue', 'Webhook'}
            ):
                continue

            assert '__slots__' in cls.__dict__, f"class '{name}' in {path} doesn't have __slots__"
            # if the class slots is a string, then mro_slots() iterates through that string (bad).
            assert not isinstance(cls.__slots__, str), f"{name!r}s slots shouldn't be strings"

            # specify if a certain module/class/base class should have dict-
            if any(i in included for i in {cls.__module__, name, cls.__base__.__name__}):
                assert '__dict__' in get_slots(cls), f"class {name!r} ({path}) has no __dict__"
                continue

            assert '__dict__' not in get_slots(cls), f"class '{name}' in {path} has __dict__"


def get_slots(_class):
    slots = [attr for cls in _class.__mro__ if hasattr(cls, '__slots__') for attr in cls.__slots__]
    return slots
