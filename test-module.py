#!/usr/bin/python3

# Test CGI prototype module.  Presents content + updates hyperlinks.

import os, re

pathprefix = "/var/www/html/quickstart/public/"
content = pathprefix + str(os.environ.get('QUERY_STRING')).split("page=")[1]
docroot = 'index.html'
thisscript = str(os.environ.get('SCRIPT_NAME'))
pagearg = 'page'

f = open(content, "r")
l = f.readlines()

print("Content-Type: text/html")
print()
for i in l:
    if "<a href=" in str(i):
        origlink = re.findall('href="/.+/"|href="/"', i, flags=re.IGNORECASE)[0].lstrip('href=').strip('"') + docroot + '"'
        print('<a href="' + thisscript + '?' + pagearg + '=' + origlink, i.strip()[len(origlink):], end='')
    else:
        print(i, end='')

f.close()
print()
