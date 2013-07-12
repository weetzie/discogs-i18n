import os
import codecs
from fabric.api import local, task

i18n_root = '.'


def supported_locales():
    """
    Return a list of supported locales based on existing directories.
    """
    l = [d for d in os.listdir(i18n_root) if os.path.isdir(os.path.join(i18n_root, d)) and not d.startswith('.')]
    l.sort()
    return l

@task
def compile_messages():
    """
    Compiles .po messages to .mo files.
    Creates a translations.json file for each locale in static/dst/i18n/<locale>/.
    """
    cmd = 'pybabel compile --directory=. --locale={locale} --input-file={locale}/LC_MESSAGES/{domain}.po --use-fuzzy --statistics --domain={domain}'
    for locale in supported_locales():
        local(cmd.format(locale=locale, domain='messages'))
        local(cmd.format(locale=locale, domain='messages_js'))
        #local('mkdir -p static/dst/i18n/{locale}'.format(locale=locale))
        #try:
            #f = codecs.open(os.path.join('static', 'dst', 'i18n', locale, 'translations.json'), encoding='utf-8', mode='w')
            #f.write(i18n._get_translations_json(locale))
            #f.close()
        #except IOError, e:
            #print "IOError for locale %s." % locale
            #print str(e)
        #except AttributeError, e:
            #print "AttributeError for locale %s." % locale
            #print str(e)
            #locale_messages_js_path = os.path.join('i18n', locale, 'LC_MESSAGES', 'messages_js.mo')
            #if not os.path.exists(locale_messages_js_path):
                #print "%s does not exist." % locale_messages_js_path
    print "Compiled message catalogs."
