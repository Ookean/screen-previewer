"""Translations.

Every language is one JSON file in previewer/locales (en.json, de.json, ...) that maps
a key to the text. To add a language, add a file with the same keys and a "_name" entry
(the language's own name, shown in the Settings menu). No code changes are needed.

Use t("window.move") to get a text in the current language. A key that is missing in
the current language falls back to English, and one that is missing everywhere is
returned as is, so a gap never crashes the UI.
"""
import json
import locale
import os
import sys

from .config import resource_path

DEFAULT_LANGUAGE = "en"
SYSTEM = "system"   # the saved preference meaning "follow the operating system"

_strings = {}
_fallback = {}
_language = DEFAULT_LANGUAGE


def _locales_dir():
    return resource_path("previewer/locales")


def _load(code):
    try:
        with open(os.path.join(_locales_dir(), f"{code}.json"), encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def available_languages():
    """[(code, name)] for every locale file, English first."""
    languages = []
    try:
        filenames = sorted(os.listdir(_locales_dir()))
    except OSError:
        filenames = []
    for filename in filenames:
        if filename.endswith(".json"):
            code = filename[:-len(".json")]
            languages.append((code, _load(code).get("_name", code)))
    languages.sort(key=lambda item: (item[0] != DEFAULT_LANGUAGE, item[0]))
    return languages or [(DEFAULT_LANGUAGE, "English")]


def system_language():
    """The user's interface language as a short code, e.g. 'de' (may not be one we have)."""
    code = None
    if sys.platform == "win32":
        try:
            import ctypes
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            code = locale.windows_locale.get(langid)   # e.g. 0x0807 -> 'de_CH'
        except Exception:
            code = None
    if not code:
        code = locale.getlocale()[0] or os.environ.get("LANG") or ""
    return code.replace("-", "_").split(".")[0].split("_")[0].lower()


def resolve(preference):
    """Turn a saved preference ('system' or a language code) into a language we have a file for."""
    wanted = system_language() if preference == SYSTEM else preference
    codes = [code for code, _name in available_languages()]
    return wanted if wanted in codes else DEFAULT_LANGUAGE


def set_language(preference=SYSTEM):
    """Switch the current language. Returns the language that is now active."""
    global _strings, _fallback, _language
    _language = resolve(preference)
    _fallback = _load(DEFAULT_LANGUAGE)
    _strings = _fallback if _language == DEFAULT_LANGUAGE else _load(_language)
    return _language


def current_language():
    return _language


def t(key, **values):
    """The text for `key` in the current language; {placeholders} are filled from `values`."""
    text = _strings.get(key) or _fallback.get(key) or key
    if not values:
        return text
    try:
        return text.format(**values)
    except (KeyError, IndexError, ValueError):
        return text
