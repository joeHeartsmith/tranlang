#!/usr/bin/env python3

# TranLang - CGI-based Language Translation for Static Web Content
#
#            Renders statically-generated HTML content, and dynamically
#            translates content to a user's preferred language.  The
#            language can be detected by the 'HTTP_ACCEPT_LANGUAGE' HTTP
#            header sent by the client's browser, or set manually via
#            the 'lang=' parameter in the URL query string.  If supplied
#            with appropriate API keys, the software will attempt to
#            translate using DeepL, and then by using Google.  To eliminate
#            page generation latency and API service charges, TranLang will
#            cache pages that have been translated and only re-translate
#            them if they have been updated.  When viewing web content with
#            TranLang, users will be presented with a collapsible toolbar
#            at the top of the page to give them control over which language
#            is presented.
#
#            Robots tool   - Generate robots.txt for all translation combinations
#                            so web crawlers can index pre-translated content.
#
#  Version 0.9 (28 December 2021)
#

import json, os, requests, sys
from html.parser import HTMLParser
from urllib.parse import parse_qs

### Configuration
deepl_api_auth_key = 'INVALID_API_KEY'                             # API key for DeepL Free/Pro
google_api_auth_key = 'INVALID_API_KEY'                            # API key for Google Cloud Translate
pathprefix = '/var/www/html/quickstart/public/'                    # Physical location on-disk for HTML content
docroot = 'index.html'                                             # Default homepage to display when no content is requested
pagearg = 'page'                                                   # URL Query String Parameter name to specify which page to supply
link_keyword = 'posts'                                             # Keyword common to all hyperlinks which will need to be re-written
codeblock_flag = 'XXXPAGECODEFLAGXXX'                              # Keyword to identify non-translatable HTML code blocks
scrub_comments = False                                             # Option to remove comments from generated HTML content
cachedir = 'tranlang-cache'                                        # Directory to store cache files in
cachename_prefix = 'tr-cache_'                                     # String to prepend to cached filenames
default_sourcelang = 'en'                                          # Default language to assume for source content not needing translation
###

# List of available languages from DeepL.  Updated from https://www.deepl.com/docs-api/translating-text/
lang_list_deepl = ['BG','CS','DA','DE','EL','ES','ET','FI','FR','HU','IT','JA',
                   'LT','LV','NL','PL','PT-PT','PT-BR','PT','RO','RU','SK','SL',
                   'SV','ZH']
# List of available languages from Google.  Updated from https://cloud.google.com/translate/docs/languages
lang_list_google = ['af','sq','am','ar','hy','az','eu','be','bn','bs','bg','ca',
                    'ceb','zh-CN','zh-TW','co','hr','cs','da','nl','eo','et','fi',
                    'fr','fy','gl','ka','de','el','gu','ht','ha','haw','he','iw',
                    'hi','hmn','hu','is','ig','id','ga','it','ja','jv','kn','kk',
                    'km','rw','ko','ku','ky','lo','lv','lt','lb','mk','mg','ms',
                    'ml','mt','mi','mr','mn','my','ne','no','ny','or','ps','fa',
                    'pl','pt','pa','ro','ru','sm','gd','sr','st','sn','sd','si',
                    'sk','sl','so','es','su','sw','sv','tl','tg','ta','tt','te',
                    'th','tr','tk','uk','ur','ug','uz','vi','cy','xh','yi','yo','zu']

# Aggregated sorted list of all possible languages
lang_list_aggr = []
for langs in lang_list_deepl + lang_list_google:
    if langs.lower() not in lang_list_aggr:
        lang_list_aggr.append(langs.lower())
lang_list_aggr.sort()


##### SERVICE SETUP

### Discover user's browser language preference.  Use the first preferred language that
#   appears in the translation services for which the webmaster has an API key.  Fall
#   back to English/no translation if no languages are available.
#
#   TODO: This doesn't really work with Firefox, as it just sends a bunch of 'en-US'
#         to the server.  Works with Chrome.
translation_engine = 'None'

accept_lang = default_sourcelang
try:
    accept_lang_qs = os.environ.get('HTTP_ACCEPT_LANGUAGE')
    stop = False
    for langs in accept_lang_qs.split(','):
        if stop == False:
            if 'INVALID' not in deepl_api_auth_key:
                if langs.rstrip(';q=.0123456789').upper() in lang_list_deepl:
                    accept_lang = langs.rstrip(';q=.0123456789')
                    translation_engine = 'DeepL'
                    stop = True
                if langs.rstrip(';q=.0123456789').upper()[0:1] in lang_list_deepl and stop == False:
                    accept_lang = langs.rstrip(';q=.0123456789')[0:2]
                    translation_engine = 'DeepL'
                    stop = True
            if 'INVALID' not in google_api_auth_key:
                if langs.rstrip(';q=.0123456789').lower() in lang_list_google:
                    accept_lang = langs.rstrip(';q=.0123456789')
                    translation_engine = 'Google'
                    stop = True
                if langs.rstrip(';q=.0123456789').lower()[0:2] in lang_list_google and stop == False:
                    accept_lang = langs.rstrip(';q=.0123456789')[0:2]
                    translation_engine = 'Google'
                    stop = True
        else:
            stop = True
except:
    accept_lang = default_sourcelang  # Should catch none or 'Accept-Language: *'

### Fetch the requested page.  Try to prevent directory traversals,
#   and just fetch the default document if unavailable.
#
#   TODO: Improve protection against directory traversal attacks
try:
    qs = parse_qs(qs=os.environ.get('QUERY_STRING'), keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None)
    qs_page = qs['page'][0].replace('..','.')
except:
    qs_page = docroot
content = str(pathprefix + qs_page).replace('//','/')

### Fetch the override language as specified in the URL Query String.
#   The URL QS 'lang=' value will take precedence over the 'Accept-Language'.
try:
    qs = parse_qs(qs=os.environ.get('QUERY_STRING'), keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None)
    qs_lang = qs['lang'][0]
    qs_spec = True

    if qs_lang.lower() in lang_list_google and 'INVALID' not in google_api_auth_key:
        translation_engine = 'Google'
    if qs_lang.upper() in lang_list_deepl and 'INVALID' not in deepl_api_auth_key:
        translation_engine = 'DeepL'
except:
    qs_lang = default_sourcelang
    qs_spec = False
target_lang = qs_lang

### Fetch the preference to automatically hide the TranLang toolbar.
try:
    qs_hide_toolbar = parse_qs(qs=os.environ.get('QUERY_STRING'), keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None)
    if qs_hide_toolbar['hide_toolbar'][0] == '1':
        hide_toolbar = True
    else:
        hide_toolbar = False
except:
    hide_toolbar = False

### Get the name of this file for use in re-writing hyperlinks
try:
    thisscript = str(os.environ.get('SCRIPT_NAME'))
except:
    thisscript = 'tranlang.cgi'

################################################################################

##### HELPER FUNCTIONS

### translateText
#   Supply a string of text, and 2-letter language code, and get a translated string back.
#   Will try to use DeepL first, then Google.  If no services are available, the original
#   text is returned instead.
def translateText(source_string, target_lang):
    hdr = {'User-Agent': 'tranlang-CGI'}

    if target_lang.upper() in lang_list_deepl and 'INVALID' not in deepl_api_auth_key:
        translation_engine = 'DeepL'
    elif target_lang.lower() in lang_list_google and 'INVALID' not in google_api_auth_key:
        translation_engine = 'Google'
    else:
        target_lang = default_sourcelang

    if translation_engine == 'Google':
        auth_key = google_api_auth_key
        translate_api_url = 'https://www.googleapis.com/language/translate/v2?key=' + auth_key
    elif translation_engine == 'DeepL':
        auth_key = deepl_api_auth_key
        translate_api_url = 'https://api-free.deepl.com/v2/translate?auth_key=' + auth_key

    if translation_engine == 'Google':
        request = requests.post(translate_api_url + '&source=en&target=' + target_lang.lower() + '&q=' + source_string, data=None, headers=hdr)
        result = json.loads(request.content)['data']['translations'][0]['translatedText']
    elif translation_engine == 'DeepL':
        rest_data = {'auth_key': auth_key, 'text': source_string, 'target_lang': target_lang.upper()}
        request = requests.post('https://api-free.deepl.com/v2/translate', data=rest_data, headers=hdr)
        result = json.loads(request.content)["translations"][0]["text"]
    else:
        result = source_string
    return result


### docparser
#   Python http.parser docparser object.  Reads through HTML pages to find translatable
#   text.  Avoids HTML <code> blocks, and also re-writes hyperlinks to keep the user
#   within the TranLang environment.
class docparser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if str('body') in tag.lower():
            print('<{}'.format(tag), end='', file=outfile)
            for attr in attrs:
                print(' {}="{}" '.format(attr[0], attr[1]), end='', file=outfile)
            print('>', file=outfile)
            if hide_toolbar == False and body_exists == True:
                render_toolbar(outfile)
        elif str('html') in tag.lower():
            if hide_toolbar == False and body_exists == True:
                print('<html lang="{}">'.format(target_lang.lower()), end='', file=outfile)
            else:
                print('<html lang="{}">'.format(target_lang.lower()), end='', file=outfile)
                if hide_toolbar == False:
                    render_toolbar(outfile)
        else:
            print('<{}'.format(tag), end='', file=outfile)
            for attr in attrs:
                stop = False
                if tag == str('a'):
                    if attr[0] == str('href'):
                        if link_keyword in attr[1] or attr[1] == "/":
                            if qs_spec == True:
                                print(' {}="{}" '.format(attr[0], thisscript + '?' + pagearg + '=' + attr[1] + docroot + '&lang=' + target_lang + '&hide_toolbar=' + str(int(hide_toolbar))), end='', file=outfile)
                            else:
                                print(' {}="{}" '.format(attr[0], thisscript + '?' + pagearg + '=' + attr[1] + docroot), end='', file=outfile)
                            stop = True
                if stop != True:
                        print(' {}="{}" '.format(attr[0], attr[1]), end='', file=outfile)
            print('>', end='', file=outfile)

    def handle_endtag(self, tag):
        print('</{}>'.format(tag), end='', file=outfile)

    def handle_startendtag(self, tag, attrs):
        print('<{}'.format(tag), end='', file=outfile)
        for attr in attrs:
            print(' {}="{}"'.format(attr[0], attr[1]), end='', file=outfile)
        print(' />', end='', file=outfile)

    def handle_data(self, data):
        if len(data.strip()) > 0 and codeblock_flag not in data:
            notranslate = False
            if target_lang.upper() not in lang_list_deepl:
                if target_lang.lower() not in lang_list_google:
                    notranslate = True

            if accept_lang.upper() != default_sourcelang.upper() and qs_spec == False:
                result = translateText(data, accept_lang)
            elif target_lang.upper() == default_sourcelang.upper() or notranslate == True:
                result = data
            else:
                result = translateText(data, target_lang)
            print('{}'.format(result), end='', file=outfile)
        else:
            print('{}'.format(data).replace(codeblock_flag, ''), end='', file=outfile)

    def handle_decl(self, data):
        print('<!{}>'.format(data), end='', file=outfile)

    def handle_pi(self, data):
        print('<?{}>'.format(data), end='', file=outfile)

    def handle_comment(self, data):
        if scrub_comments == True:
            print('<!--COMMENT SCRUBBED-->', file=outfile)
        else:
            print('<!--{}-->'.format(data), end='', file=outfile)
    def unknown_decl(self, data):
        print('<!{}>'.format(data), end='', file=outfile)

parser = docparser(convert_charrefs=True)

### render_toolbar
#   Draws TranLang toolbar at the top of the page.
#
def render_toolbar(dest):
    try:
        request_page_qs = parse_qs(qs=os.environ.get('QUERY_STRING'), keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None)
        request_page = request_page_qs['page'][0]
    except:
        request_page = ''
    try:
        request_uri = os.environ.get('REQUEST_URI')
        if 'hide_toolbar'.lower() not in request_uri.lower():
            uri_with_hide = request_uri + '&hide_toolbar=1'
        else:
            uri_with_hide = request_uri.replace('hide_toolbar=0', 'hide_toolbar=1')
    except:
        uri_with_hide = docroot

    if qs_spec == True:
        display_lang = target_lang
    else:
        display_lang = accept_lang

    print('', file=dest)
    print('<!--Start tranlang Toolbar-->', file=dest)
    print('<div style="width: 100%; max-height: 10%;">', file=dest)
    print(' <p style="color:#333333; font-style:italic"> TranLang: [' + display_lang + '] &#8594', file=dest)
    print('  <select name="sample" onchange="location = this.value;">', file=dest)
    print('   <option value=""></option>', file=dest)
    print('   <option value="' + thisscript + '?' + pagearg + '=' + request_page + '&lang=' + default_sourcelang + '">' + default_sourcelang + '</option>', file=dest)
    for langs in lang_list_aggr:
        print('   <option value="' + thisscript + '?' + pagearg + '=' + request_page + '&lang=' + langs + '">' + langs + '</option>', file=dest)
    print(' </select>', file=dest)
    print(' <a style="text-decoration: none" href="' + uri_with_hide  + '"> [ &#10005 ]</a>', file=dest)
    print(' </p>', file=dest)
    print('</div>', file=dest)

    print('<!--End tranlang Toolbar-->', file=dest)
    print('', file=dest)

################################################################################

### Page reading
#   Determine whether the page has already been translated, and fetch the latest version
#   of the requested content.  Read into memory.

outfile = sys.stdout
if hide_toolbar == True:
    toolbar_loaded = 'notool'
else:
    toolbar_loaded = 'wtool'
cachefile = cachedir + '/' + cachename_prefix + qs_page.replace('/','_')[1:] + '_' + target_lang.lower() + toolbar_loaded
if qs_spec == False:
    cachefile = cachedir + '/' + cachename_prefix + qs_page.replace('/','_')[1:] + '_' + accept_lang.lower() + toolbar_loaded

cache_stale = False
try:
    cachefile_age = os.path.getmtime(cachefile)
    cache_available = True
except:
    cache_available = False

try:
    content_age = os.path.getmtime(content)
    content_available = True
    f = open(content, 'r')
except:
    content = pathprefix + docroot
    content_available = False
    f = open(content, 'r')

if cache_available == True and content_available == True:
    if content_age >= cachefile_age:
        cache_stale = True

l = f.read()
f.close()

body_exists = False
for lines in l:
    if '<body' in str(l):
        body_exists = True

### Page rendering
#   Renders a new HTML page for the user.  Digs out HTML <code> blocks, delivers HTTP headers to
#   client, draws a toolbar at the top of the page, and supplies translated text.

# Identify HTML <code> blocks
page_render = l.replace('<code>', '<code> ' + codeblock_flag)

# Deliver HTTP headers to client
print('Content-Type: text/html')
print('Content-Language: ' + target_lang.lower())
print('Server: tranlang.cgi')
print()

# Start HTML document
print('<!--Page Dynamically Translated to \'' + target_lang.lower() + '\' language/locality by tranlang.cgi-->')
if 'INVALID' not in deepl_api_auth_key:
    print('<!--Loaded API: DeepL Free/Pro-->')
if 'INVALID' not in google_api_auth_key:
    print('<!--Loaded API: Google Cloud Translate-->')
print()

# Check if cache file is available and if it's not stale, and render + deliver content
if cache_available == False or cache_stale == True:
    outfile = open(cachefile, 'w')
    parser.feed(page_render)
    outfile.close()
else:
    outfile = sys.stdout

f = open(cachefile, 'r')
l = f.read()
f.close()
print(l)
