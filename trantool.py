#!/usr/bin/env python3

### Trantool - generates an XML sitemap for your robots.txt, and optionally
#              requests a copy of every site page in every language to create
#              cache files for faster access.

import requests
from pathlib import Path

generate_robots = True     # Generate XML Sitemap for robots.txt - very fast
pretranslate_pages = True  # Visit all site pages in every language - very slow

# Script options
server_location = 'http://127.0.0.1/cgi-bin/tranlang.cgi'
pathprefix = '/var/www/html/quickstart/public/'
contentpath = pathprefix + 'posts/'
sitemap_file = '/var/www/html/sitemap.xml'

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
lang_list_aggr.sort()  ### THIS IS A LOT OF DATA TO PROCESS/PAY FOR!  Uncomment
                         # the line below to process a customized language list
                         # instead.

#lang_list_aggr = ['zh-CN', 'hi', 'es', 'fr', 'ar', 'bn', 'ru']

srcpages = ['/index.html']
for path in Path(contentpath).rglob('*.html'):
    srcpages.append(str(str(path.parent) + '/' + str(path.name)).replace(pathprefix, '/'))
total_lookups = len(srcpages) * len(lang_list_aggr) * 2
p = 0
if pretranslate_pages == True:
    for langs in lang_list_aggr:
        for pages in srcpages:
            requests.get(server_location + '?page=' + pages + '&lang=' + langs, data=None, headers=None)
            requests.get(server_location + '?page=' + pages + '&lang=' + langs + '&hide_toolbar=1', data=None, headers=None)
            p = p + 2
            print('Progress: {}/{} pages'.format(p, total_lookups))

if generate_robots == True:
    f = open(sitemap_file, 'w')
    print('<?xml version="1.0" encoding="UTF-8">', file=f)
    print('<urlset xmlns="http://www.sitemaps.org/schemes/sitemap/0.9">', file=f)
    for langs in lang_list_aggr:
        for pages in srcpages:
            print('    <url>', file=f)
            print('        <loc>' + server_location + '?page=' + pages + '&lang=' + langs + '</loc>', file=f)
#            print('        <lastmod>' + LOCATION_URL + '</lastmod>', file=f)
            print('        <changefreq>' + 'monthly' + '</changefreq>', file=f)
            print('        <priority>' + '0.5' + '</priority>', file=f)
            print('    </url>', file=f)

            print('    <url>', file=f)
            print('        <loc>' + server_location + '?page=' + pages + '&lang=' + langs + '&hide_toolbar=1' + '</loc>', file=f)
#            print('        <lastmod>' + LOCATION_URL + '</lastmod>', file=f)
            print('        <changefreq>' + 'monthly' + '</changefreq>', file=f)
            print('        <priority>' + '0.5' + '</priority>', file=f)
            print('    </url>', file=f)
    print('</urlset>', file=f)
f.close()
