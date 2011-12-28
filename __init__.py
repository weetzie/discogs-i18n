from babel.support import Translations

def _get_locales():
    """
    TODO: needs real implementation and default language.
    """
    locales = ['en', 'de', 'ja']
    from random import randrange
    i = randrange(len(locales))
    return [locales[i], 'en']

def get_translations():
    return Translations.load(dirname='i18n', locales=_get_locales())