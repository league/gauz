from gauzlib.assets import *
from gauzlib.log import SimpleLogger
from gauzlib.load import DependencyTracker
from genshi.template.base import Context
from time import sleep
import re

class Config(object):
    ignoreDirRegex = re.compile(r'^[_\.]')
    ignoreFileRegex = re.compile(r'(^|/)(_|\.#|#)|~$')
    markupFileRegex = re.compile(r'\.(xml|html|xhtml|htm|rss)$')
    textFileRegex = re.compile(r'\.css$')
    iso8601Regex = re.compile(r'(\d{4})[-/\.](\d{2})[-/\.](\d{2})')

    log = SimpleLogger()
    waitIntervalSec = 2

    def __init__(self, outputDir, includeDirs):
        self.outputDir = outputDir
        self.loader = DependencyTracker([os.path.realpath(d)
                                         for d in ['.'] + includeDirs])

    def pruneDirs(self, parent, dirs):
        for d in reversed(dirs): # backwards so we can safely remove
            if self.ignoreDirRegex.search(d):
                dirs.remove(d)

    def makeAssetFor(self, pathname):
        if self.ignoreFileRegex.search(pathname):
            return None
        elif self.markupFileRegex.search(pathname):
            return MarkupAsset(pathname, self)
        elif self.textFileRegex.search(pathname):
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
        return Context(page = asset)

    def wait(self):
        self.log.wait()
        sleep(self.waitIntervalSec)

    def extractTitle(self, xml):
        return self.extractFunctionBody('page_title', xml)

    def extractTags(self, xml):
        tags = self.extractFunctionBody('page_tags', xml)
        tags = tagSepRegex.split(tags) if tags else []
        tags.sort()
        return tags

    def extractDate(self, xml):
        ymd = self.extractFunctionBody('page_date', xml)
        mo = self.iso8601Regex.search(ymd)
        if mo:
            return datetime.date(int(mo.group(1)), int(mo.group(2)),
                                 int(mo.group(3)))
        else:
            return None

    def extractFunctionBody(self, func, xml):
        py = {'py': 'http://genshi.edgewall.org/'}
        stream = xml.select('py:def[@function="%s"]/text()' % func,
                            namespaces = py)
        return unicode(stream.render('text'), 'utf-8')

