from gauzlib.assets import *
from gauzlib.load import DependencyTracker
from gauzlib.log import SimpleLogger
from gauzlib.util import GauzUtils
from genshi.template.base import Context
from time import sleep
import datetime
import re

class Config(object):
    reIgnoredir = re.compile(r'^[_\.]')
    reIgnorefile = re.compile(r'(^|/)(_|\.#|#)|~$')
    reIso8601 = re.compile(r'(\d{4})[-/\.](\d{2})[-/\.](\d{2})')
    reMarkupfile = re.compile(r'\.(xml|html|xhtml|htm|rss)$')
    reTagsep = re.compile(r'[,;:\s]\s*')
    reTextfile = re.compile(r'\.css$')

    xpTitle = 'title/text()'
    xpTags = 'meta[@name="keywords"]/@content'
    xpDate = 'meta[@name="date"]/@content'

    log = SimpleLogger()
    gauz = GauzUtils()
    waitIntervalSec = 2
    namespaces = {'py': 'http://genshi.edgewall.org/',
                  'xi': 'http://www.w3.org/2001/XInclude'}

    def __init__(self, outputDir, includeDirs):
        self.outputDir = outputDir
        self.loader = DependencyTracker(includeDirs)

    def pruneDirs(self, parent, dirs):
        for d in reversed(dirs): # backwards so we can safely remove
            if self.reIgnoredir.search(d):
                dirs.remove(d)

    def makeAssetFor(self, pathname):
        if self.reIgnorefile.search(pathname):
            return None
        elif self.reMarkupfile.search(pathname):
            return MarkupAsset(pathname, self)
        elif self.reTextfile.search(pathname):
            return TextAsset(pathname, self)
        else:
            return LinkAsset(pathname, self)

    def finalizeAsset(self, a):
        a.target = os.path.join(self.outputDir, a.source)
        a.top = ''.join(['../' for x in a.source.split('/')[1:]])
        a.href = a.top + a.source

    def summarize(self, fileMap):
        pass

    def makeContext(self, asset):
        return Context(page=asset, gauz=self.gauz)

    def wait(self):
        self.log.wait()
        sleep(self.waitIntervalSec)

    def extractText(self, xml, xpath):
        stream = xml.select(xpath, namespaces = self.namespaces)
        return unicode(stream.render('text'), 'utf-8')

    def extractTitle(self, asset):
        return self.extractText(asset.xml, self.xpTitle)

    def extractTags(self, asset):
        tags = self.extractText(asset.xml, self.xpTags)
        tags = self.reTagsep.split(tags) if tags else []
        tags.sort()
        return tags

    def extractDate(self, asset):
        ymd = self.extractText(asset.xml, self.xpDate) or asset.source
        mo = self.reIso8601.search(ymd)
        if mo:
            return datetime.date(int(mo.group(1)), int(mo.group(2)),
                                 int(mo.group(3)))
        else:
            return None
