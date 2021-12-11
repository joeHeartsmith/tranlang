#!/usr/bin/env python3

# Updated prototype.  Uses actual HTML parsing, and exempts code blocks from translation.  Still only updates hyperlinks.

import os
from html.parser import HTMLParser

pathprefix = '/var/www/html/quickstart/public/'
docroot = 'index.html'
pagearg = 'page'
link_keyword = 'posts'

try:
    thisscript = str(os.environ.get('SCRIPT_NAME'))
except:
    thisscript = 'tranlang.cgi'
try:
    content = pathprefix + str(os.environ.get('QUERY_STRING')).split("page=")[1]
except:
    content = pathprefix + 'index.html'
try:
    f = open(content, 'r')
except:
    content = pathprefix + 'index.html'
    f = open(content, 'r')

class docparser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        print('<{}'.format(tag), end='')
        for attr in attrs:
            stop = False
            if tag == str('a'):
                if attr[0] == str('href'):
                    if link_keyword in attr[1] or attr[1] == "/":
                        print(' {}="{}" '.format(attr[0], thisscript + '?' + pagearg + '=' + attr[1] + docroot), end='')
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
            print('(TRANSLATE!) {}'.format(data), end='')
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
