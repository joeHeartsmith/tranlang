#!/usr/bin/env python3

# Updated prototype.  Uses actual HTML parsing, and exempts code blocks from translation.
# Performs translation via DeepL Free API, but language has to be manually set via the URL 'lang=' query string.

import sys, os, requests, json
from html.parser import HTMLParser
from urllib.parse import parse_qs

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

pathprefix = '/var/www/html/quickstart/public/'
docroot = 'index.html'
pagearg = 'page'
link_keyword = 'posts'

try:
    qs = parse_qs(qs=os.environ.get('QUERY_STRING'), keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None)
    qs_page = qs['page'][0]
except:
    qs_page = 'index.html'

try:
    qs = parse_qs(qs=os.environ.get('QUERY_STRING'), keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None)
    qs_lang = qs['lang'][0]
except:
    qs_lang = 'EN'

try:
    thisscript = str(os.environ.get('SCRIPT_NAME'))
except:
    thisscript = 'tranlang.cgi'

content = str(pathprefix + qs_page).replace('//','/')

try:
    f = open(content, 'r')
except:
    content = pathprefix + 'index.html'
    f = open(content, 'r')

target_lang = qs_lang    # This will be populated by the HTTP Accept-Language sent by the client's browser
auth_key = '7ecc9ecc-2f15-119d-e6c3-fac982730290:fx'
url = 'https://api-free.deepl.com/v2/translate?auth_key=' + auth_key
hdr = {'User-Agent': 'tranlang-CGI'}

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
            if target_lang.upper() == 'EN':
                result = data
            else:
                data = {'auth_key': auth_key, 'text': data, 'target_lang': target_lang}
                request = requests.post('https://api-free.deepl.com/v2/translate', data=data, headers=hdr)
                result = json.loads(request.content)["translations"][0]["text"]

            print('{}'.format(result), end='')
        else:
            print('{}'.format(data).replace('XXXPAGECODEFLAGXXX', ''), end='')

    def handle_decl(self, data):
        print('<!{}>'.format(data), end='')
# TODO: add handle_pi, handle_charref, handle_entityref, and unknown_decl methods
parser = docparser()

l = f.read()
f.close()

page_render = l.replace('<code>', '<code> XXXPAGECODEFLAGXXX')

# TODO: Fill HTTP header fields (especially 'Content-Language')
print('Content-Type: text/html')
print()

parser.feed(page_render)
