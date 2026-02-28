#!/bin/bash
cd "$(dirname "$0")"

python -c "
import sys, os, builtins, gettext
sys.path.insert(0, '.')

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio
settings = Gio.Settings.new('com.zeroneai.app')
lang = settings.get_string('app-language')

if lang and lang != 'system':
    rel_locale = os.path.join('.', 'po', 'locale')
    try:
        t = gettext.translation('zeroneai', localedir=rel_locale, languages=[lang])
        t.install()
        builtins._ = t.gettext
    except Exception:
        builtins._ = lambda x: x
else:
    builtins._ = lambda x: x

from src.main import main
main('1.0.0')
"
