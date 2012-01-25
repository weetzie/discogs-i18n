"""
Internationalization (i18n) and Localization (l10n) module.
"""
import simplejson
import os

import utils
import dbobjects
import babel.support
import babel.localedata


__all__ = ["get_locales", "get_language", "get_translations"]


def get_locales(request):
    """
    Get locale from query string, user preferences, cookie, browser, or ip.
    Default to english if all else fails.
    """
    methods = [
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
    supported_locales = _get_supported_locales()
    for locale in locales:
        if locale in supported_locales:
            language = locale
            break
    return language


def get_translations(locales=['en'], domain='messages'):
    """
    Return translations for given locale and domain.
    """
    return babel.support.Translations.load(dirname='i18n', locales=locales, domain=domain)


def _get_translations_json(locales=['en']):
    """
    Return json version of translations for given locales and messages_js domain.
    """
    translations = get_translations(locales=locales, domain='messages_js')
    return simplejson.dumps(translations._catalog, ensure_ascii=False, indent=False)


def _get_supported_locales():
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
    supported_locales = _get_supported_locales()
    return [language for language in accept_languages if language in supported_locales]


def _get_locales_from_ip(request):
    """
    Return supported locales based on country code from ip country lookup.
    """
    def _get_country_to_locales_map():
        country_to_locales_map = {}
        for locale in babel.localedata.list():
            if not '_' in locale:
                continue
            language, country = locale.split('_', 1)
            if '_' in country:
                part1, part2 = country.split('_')
                if len(part1) == 2:
                    country = part1
                elif len(part2) == 2:
                    country = part2
                else:
                    raise ValueError("Unexpected value for country ({country}) with language ({language}) in locale ({locale}))".format(
                        country=country, language=language, locale=locale))
            if not country_to_locales_map.has_key(country.lower()):
                country_to_locales_map[country.lower()] = []
            if not language in country_to_locales_map[country.lower()]:
                country_to_locales_map[country.lower()].append(language)
            country_to_locales_map[country.lower()].append(locale)
        for country, locales in country_to_locales_map.items():
            locales = list(set(locales))
            locales.sort()
            country_to_locales_map[country] = locales
        return country_to_locales_map

    country_to_locales_map = _get_country_to_locales_map()
    supported_locales = _get_supported_locales()
    country_code = dbobjects.IP_Country.lookup(request.remote_addr)[0].strip().lower()
    if country_to_locales_map.has_key(country_code):
        return [locale for locale in country_to_locales_map[country_code] if locale in supported_locales]
    return []

