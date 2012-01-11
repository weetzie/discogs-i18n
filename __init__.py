"""
Internationalization (i18n) and Localization (l10n) module.
"""
import simplejson
import os

import utils
import dbobjects
from babel.support import Translations

__all__ = ["get_locales", "get_language", "get_translations", "get_translations_json"]


def get_locales(request):
    """
    Get locale from query string, user preferences, cookie, browser, or ip.
    Default to english if all else fails.
    """
    methods = [
        _get_locales_from_query_string,
        _get_locales_from_browser,
        _get_locales_from_ip,
        lambda x: ['en']
    ]
    locales = None
    for method in methods:
        locales = method(request)
        if locales:
            break
    return locales


def get_language(locales=['en']):
    """
    Get language from locales.
    Returns the first item in the locales list.
    Defaults to english.
    """
    language = 'en' # default language
    supported_locales = _get_supported_locales_from_directories()
    for locale in locales:
        if locale in supported_locales:
            language = locale
            break
    return language


def get_translations(locales=['en'], domain='messages'):
    """
    Return translations for given locale and domain.
    """
    return Translations.load(dirname='i18n', locales=locales, domain=domain)


def get_translations_json(locales=['en']):
    """
    Return json version of translations for given locales and messages_js domain.
    """
    translations = get_translations(locales=locales, domain='messages_js')
    return simplejson.dumps(translations._catalog, ensure_ascii=False, indent=False)


def _get_supported_locales_from_directories():
    """
    Return a list of supported locales based on existing directories.
    """
    return [d for d in os.listdir('i18n') if os.path.isdir(os.path.join('i18n', d))]


def _parse_accept_language(accept_language):
    """
    Parse the Accept-Language header.
    Return a list of language tags sorted by their "q" values.
    For example, "en-ca,en;q=0.8,en-us;q=0.6,de-de;q=0.4,de;q=0.2" should return ["en", "de"].
    If there is no Accept-Language header present, default to [].
    """
    if accept_language is None:
        return []
    languages = accept_language.split(",")
    languages_with_quality = []
    for language in languages:
        pieces = language.split(';')
        lang = pieces[0].split('-')[0].strip().lower()
        if len(pieces) == 1:
            quality = 1.0
        else:
            quality = float(pieces[1].split("=")[1].strip())
        if not lang in [l for (l, q) in languages_with_quality]:
            languages_with_quality.append((lang, quality))
    languages_with_quality.sort(lambda a, b: -cmp(a[1], b[1]))
    return [l for (l, q) in languages_with_quality]


def _get_locales_from_browser(request):
    """
    Return supported locales based on browser Accept-Language header.
    """
    accept_languages = _parse_accept_language(request.headers.get('Accept-Language', None))
    supported_locales = _get_supported_locales_from_directories()
    return [language for language in accept_languages if language in supported_locales]


def _get_locales_from_ip(request):
    """
    Return supported locales based on country code from ip country lookup.
    """
    country_to_language_map = {
        'us': 'en',
        'br': 'pt',
        # TODO: add more mappings
    }
    country_code = dbobjects.IP_Country.lookup(request.remote_addr)[0].strip().lower()
    if country_to_language_map.has_key(country_code):
        language = country_to_language_map[country_code]
        supported_locales = _get_supported_locales_from_directories()
        if language in supported_locales:
            return [language]
    return []


def _get_locales_from_query_string(request):
    """
    Return supported locales based on query string.
    """
    requested_language = request.args.get('language')
    supported_locales = _get_supported_locales_from_directories()
    if requested_language and requested_language in supported_locales:
        return [requested_language]
    return []



# TODO: Move this out to some fabric command line tool
# from apiclient.discovery import build
# def get_google_translations(language='fr'):
#     service = build('translate', 'v2',
#         developerKey='test')
#     l = service.translations().list(
#         format='text',
#         source='en',
#         target=language,
#         q=['flower', 'car']
#     ).execute()
#     return l
