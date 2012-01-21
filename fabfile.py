import os
import codecs

import i18n
from fabric.api import local, task
import babel.localedata
import babel.messages.pofile
import apiclient.discovery

if not os.environ.has_key('APP_ENV'):
    os.environ['APP_ENV'] = 'dev'

import locals as _locals


@task
def list_supported_locales():
    """
    List supported locales.
    These are the locales that currently exist.
    """
    supported_locales = i18n._get_supported_locales()
    for locale in supported_locales:
        print locale
    print "%d supported locales." % len(supported_locales)
    print "List all locales with: fab list_locales"
    print "Add locales with: fab add_locale:<locale>"
    print "Remove locales with: fab remove_locale:<locale>"


@task
def list_locales():
    """
    List all locales from babel.
    """
    locales = babel.localedata.list()
    for locale in locales:
        print locale
    print "%d locales." % len(locales)
    print "List supported locales with: fab list_supported_locales"
    print "Add locales with: fab add_locale:<locale>"
    print "Remove locales with: fab remove_locale:<locale>"


@task
def add_locale(locale=None):
    """
    Adds a new locale.
    Creates directory structure for:
        i18n/<locale>/LC_MESSAGES
        static/js/i18n/<locale>
    Creates the initial messages.po and messages_js.po files from the .pot files.
    Prints error message if locale alreay exists or is invalid.
    """
    supported_locales = i18n._get_supported_locales()
    if locale is None:
        print "USAGE: Add locales with: fab add_locale:<locale>"
    elif locale in supported_locales:
        print "ERROR: Locale %s is already a supported locale." % locale
    elif locale not in babel.localedata.list():
        print "ERROR: Invalid locale %s. Use `pybabel --list-locales` for a list of locales." % locale
    else:
        local('mkdir %s' % os.path.join('i18n', locale))
        local('mkdir %s' % os.path.join('static/js/i18n', locale))
        cmd = 'pybabel init --input-file=i18n/{domain}.pot --output-dir=i18n --locale={locale} --domain={domain}'
        local(cmd.format(domain='messages', locale=locale))
        local(cmd.format(domain='messages_js', locale=locale))
        print "Created locale %s with initial template files." % locale


@task
def remove_locale(locale=None):
    """
    Removes locale.
    Removes directory structure for:
        i18n/<locale>/LC_MESSAGES
        static/js/i18n/<locale>
    """
    if locale is None:
        print "USAGE: Remove locales with: fab remove_locale:<locale>"
    else:
        local('rm -rf %s' % os.path.join('i18n', locale))
        local('rm -rf %s' % os.path.join('static/js/i18n', locale))
        print "Removed locale %s." % locale


@task
def eutc_messages():
    """
    Extract, Update, Translate, and Compile messages.
    """
    local('fab i18n.extract_messages && fab i18n.update_messages && fab i18n.translate_messages && fab i18n.compile_messages')


@task
def extract_messages():
    """
    Extracts messages from python, jinja templates, and javascript to .pot files.
    """
    cmd = 'pybabel extract --mapping=config/{config} --charset=utf-8 --no-wrap --msgid-bugs-address=language@discogs.com --copyright-holder=Discogs --project=Discogs --version=0.1 --output=i18n/{domain}.pot .'
    local(cmd.format(config='babel.cfg', domain='messages'))
    local(cmd.format(config='babel_js.cfg', domain='messages_js'))
    print "Extracted messages into template files. Next run: fab update_messages"


@task
def update_messages():
    """
    Updates existing .po files with new entries in .pot files from extract_messages.
    """
    # manage English language files manually; en should be empty; en_GB should just have string we want to translate for the UK.
    supported_locales = [locale for locale in i18n._get_supported_locales() if not locale.startswith('en')]
    cmd = 'pybabel update --input-file=i18n/{domain}.pot --output-dir=i18n --locale={locale} --domain={domain} --ignore-obsolete'
    for locale in supported_locales:
        local(cmd.format(domain='messages', locale=locale))
        local(cmd.format(domain='messages_js', locale=locale))
    print "Updated message catalogs. Next run: fab translate_messages"


@task
def translate_messages():
    """
    Translate new messages using Google Translate API.
    This will find empty msgstr strings in .po files and use Google Translate API to populate them.
    """
    def _add_missing_translations(domain, locale):
        fileobj = open(os.path.join('i18n', locale, 'LC_MESSAGES', '{domain}.po'.format(domain=domain)), 'r')
        catalog = babel.messages.pofile.read_po(fileobj, locale=locale, domain=domain, ignore_obsolete=True)
        fileobj.close()
        msgids_to_translate = [msgid for msgid, message in catalog._messages.items() if message.string == '']

        # google translate
        # translations_json = service.translations().list(
        #     format='text',
        #     source='en',
        #     target=locale,
        #     q=msgids_to_translate,
        #     ).execute()
        # print translations_json # {'translations': [{'translatedText': 'fleurs'}, {'translatedText': 'voiture'}]}

        # mock google translate
        translations_json = {'translations': []}
        for count in range(0, len(msgids_to_translate)):
            translations_json['translations'].append({'translatedText': 'foo%s' % count})

        for index, msgid in enumerate(msgids_to_translate):
            catalog[msgid].string = translations_json['translations'][index]['translatedText']
        fileobj = open(os.path.join('i18n', locale, 'LC_MESSAGES', '{domain}.po'.format(domain=domain)), 'w')
        babel.messages.pofile.write_po(fileobj, catalog, ignore_obsolete=True, include_previous=True)
        fileobj.close()
        return len(msgids_to_translate)

    translation_count = 0
    service = apiclient.discovery.build('translate', 'v2', developerKey=_locals.google_translate_server_api_key)
    supported_locales = i18n._get_supported_locales()
    for locale in supported_locales:
        translation_count += _add_missing_translations(domain='messages', locale=locale)
        translation_count += _add_missing_translations(domain='messages_js', locale=locale)
    print "Translated %d new strings." % translation_count


@task
def compile_messages():
    """
    Compiles .po messages to .mo files.
    Creates a translations.json file for each locale in static/js/i18n/<locale>/.
    """
    supported_locales = i18n._get_supported_locales()
    cmd = 'pybabel compile --directory=i18n --locale={locale} --input-file=i18n/{locale}/LC_MESSAGES/{domain}.po --use-fuzzy --statistics --domain={domain}'
    for locale in supported_locales:
        local(cmd.format(locale=locale, domain='messages'))
        local(cmd.format(locale=locale, domain='messages_js'))
        try:
            f = codecs.open(os.path.join('static', 'js', 'i18n', locale, 'translations.json'), encoding='utf-8', mode='w')
            f.write(i18n._get_translations_json(locale))
            f.close()
        except IOError, e:
            print "IOError for locale %s." % locale
            print str(e)
        except AttributeError, e:
            print "AttributeError for locale %s." % locale
            print str(e)
            locale_messages_js_path = os.path.join('i18n', locale, 'LC_MESSAGES', 'messages_js.mo')
            if not os.path.exists(locale_messages_js_path):
                print "%s does not exist." % locale_messages_js_path
    print "Compiled message catalogs."

