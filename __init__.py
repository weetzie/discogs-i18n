from babel.support import Translations
import simplejson

def _get_locales():
    """
    TODO: needs real implementation and default language.
    """
    locales = ['en', 'de', 'ja']
    from random import randrange
    i = randrange(len(locales))
    return list(set([locales[i], 'en']))

def get_translations(locales=[], domain='messages'):
    return Translations.load(dirname='i18n', locales=locales or _get_locales(), domain=domain)

def get_translations_json(locales=[]):
    translations = get_translations(locales, domain='messages_js')
    keys = translations._catalog.keys()
    keys.sort()
    translations_dict = {}
    for k in keys:
        v = translations._catalog[k]
        if type(k) is tuple:
            if k[0] not in translations_dict:
                translations_dict[k[0]] = []
            translations_dict[k[0]].append(v)
        else:
            translations_dict[k] = v
    return simplejson.dumps(translations_dict, ensure_ascii=False, indent=False)