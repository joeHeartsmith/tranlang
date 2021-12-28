# tranlang
TranLang - CGI-based Language Translation for Static Web Content

![logo](tranlang-III-CM.png)

### About
Renders statically-generated HTML content, and dynamically translates content to a user's preferred language.  The language can be detected by the 'HTTP_ACCEPT_LANGUAGE' HTTP header sent by the client's browser, or set manually via the 'lang=' parameter in the URL query string.  If supplied with appropriate API keys, the software will attempt to translate using DeepL, and then by using Google.  To eliminate page generation latency and API service charges, TranLang will cache pages that have been translated and only re-translate them if they have been updated.  When viewing web content with TranLang, users will be presented with a collapsible toolbar at the top of the page to give them control over which language is presented.

### Installation
Just put tranlang.cgi in your cgi-bin (or equivalent) folder, and set the options at the top of the file.  Ensure your httpd has the correct permissions to read the appropriate files, and to write cache files to the specified cache directory.  Once setup and working, you can optionally run the accompanying _trantool.py_ to pre-cache all available pages into all languages, and additionally create a _sitemap.xml_ for your _robots.txt_.

Make sure you get API keys from DeepL and/or Google, and also place them in the configuration portion at the top of the script.


_Version 0.9 (28 December 2021)_
