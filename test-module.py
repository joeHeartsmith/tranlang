#!/usr/bin/env python3

# Updated prototype.  Uses actual HTML parsing, and exempts code blocks from translation.
# Performs translation via DeepL Free API, then by Google Cloud Translate API,
# but language has to be manually set via the URL 'lang=' query string.

import sys, os, requests, json
from html.parser import HTMLParser
from urllib.parse import parse_qs

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# https://www.deepl.com/docs-api/translating-text/
lang_list_deepl = ['BG','CS','DA','DE','EL','EN-GB','EN-US','EN','ES','ET','FI','FR','HU','IT','JA','LT','LV','NL','PL','PT-PT','PT-BR','PT','RO','RU','SK','SL','SV','ZH']
# https://cloud.google.com/translate/docs/languages
lang_list_google = ['af','sq','am','ar','hy','az','eu','be','bn','bs','bg','ca','ceb','zh-CN','zh-TW','co','hr','cs','da','nl','eo','et','fi','fr','fy','gl','ka','de','el','gu','ht','ha','haw','he','iw','hi','hmn','hu','is','ig','id','ga','it','ja','jv','kn','kk','km','rw','ko','ku','ky','lo','lv','lt','lb','mk','mg','ms','ml','mt','mi','mr','mn','my','ne','no','ny','or','ps','fa','pl','pt','pa','ro','ru','sm','gd','sr','st','sn','sd','si','sk','sl','so','es','su','sw','sv','tl','tg','ta','tt','te','th','tr','tk','uk','ur','ug','uz','vi','cy','xh','yi','yo','zu']

pathprefix = '/var/www/html/quickstart/public/'
docroot = 'index.html'
pagearg = 'page'
link_keyword = 'posts'

try:
    qs = parse_qs(qs=os.environ.get('QUERY_STRING'), keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None)
    qs_page = qs['page'][0]
except:
    qs_page = 'index.html'
content = str(pathprefix + qs_page).replace('//','/')

try:
    qs = parse_qs(qs=os.environ.get('QUERY_STRING'), keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None)
    qs_lang = qs['lang'][0]
except:
    qs_lang = 'EN'
target_lang = qs_lang    # This will be populated by the HTTP Accept-Language sent by the client's browser

try:
    thisscript = str(os.environ.get('SCRIPT_NAME'))
except:
    thisscript = 'tranlang.cgi'

try:
    f = open(content, 'r')
except:
    content = pathprefix + 'index.html'
    f = open(content, 'r')
l = f.read()
f.close()


def translateText(source_string, target_lang):
    hdr = {'User-Agent': 'tranlang-CGI'}

    if target_lang.upper() in lang_list_deepl:
        translation_engine = 'DeepL'
    elif target_lang.lower() in lang_list_google:
        translation_engine = 'Google'
    else:
        target_lang = 'EN'

    if translation_engine == 'Google':
        auth_key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        translate_api_url = 'https://www.googleapis.com/language/translate/v2?key=' + auth_key
    elif translation_engine == 'DeepL':
        auth_key = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:xx'
        translate_api_url = 'https://api-free.deepl.com/v2/translate?auth_key=' + auth_key

    if translation_engine == 'Google':
        rest_data = {'auth_key': auth_key, 'text': source_string, 'target_lang': target_lang.lower()}
        request = requests.post(translate_api_url + '&source=en&target=' + target_lang.lower() + '&q=' + source_string, data=None, headers=hdr)
        result = json.loads(request.content)['data']['translations'][0]['translatedText']
    elif translation_engine == 'DeepL':
        rest_data = {'auth_key': auth_key, 'text': source_string, 'target_lang': target_lang.upper()}
        request = requests.post('https://api-free.deepl.com/v2/translate', data=rest_data, headers=hdr)
        result = json.loads(request.content)["translations"][0]["text"]
    return result


class docparser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print('<{}'.format(tag), end='')
        for attr in attrs:
            stop = False
            if tag == str('a'):
                if attr[0] == str('href'):
                    if link_keyword in attr[1] or attr[1] == "/":
                        print(' {}="{}" '.format(attr[0], thisscript + '?' + pagearg + '=' + attr[1] + docroot + '&lang=' + target_lang), end='')
                        stop = True  # gross. fix this control flow later.
            if stop != True:
                print(' {}="{}" '.format(attr[0], attr[1]), end='')
        print('>', end='')

    def handle_endtag(self, tag):
        print('</{}>'.format(tag), end='')

    def handle_startendtag(self, tag, attrs):
        print('<{}'.format(tag), end='')
        for attr in attrs:
            print(' {}="{}"'.format(attr[0], attr[1]), end='')
        print(' />', end='')

    def handle_data(self, data):
        if len(data.strip()) > 0 and 'XXXPAGECODEFLAGXXX' not in data:
            notranslate = False
            if target_lang.upper() not in lang_list_deepl:
                if target_lang.lower() not in lang_list_google:
                    notranslate = True

            if target_lang.upper() == 'EN' or notranslate == True:
                result = data
            else:
                result = translateText(data, target_lang)
            print('{}'.format(result), end='')
        else:
            print('{}'.format(data).replace('XXXPAGECODEFLAGXXX', ''), end='')

    def handle_decl(self, data):
        print('<!{}>'.format(data), end='')
# TODO: add handle_pi, handle_charref, handle_entityref, and unknown_decl methods
parser = docparser()

page_render = l.replace('<code>', '<code> XXXPAGECODEFLAGXXX')

# TODO: Fill HTTP header fields (especially 'Content-Language')
print('Content-Type: text/html')
print()

parser.feed(page_render)
