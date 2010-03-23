from gauzlib.assets import *
from gauzlib.log import SimpleLogger
from genshi.template.base import Context
import re

class Config(object):
    ignoreDirRegex = re.compile(r'^[_\.]')
    ignoreFileRegex = re.compile(r'(^_|^\.#|~$)')
    markupFileRegex = re.compile(r'\.(xml|html|xhtml|htm|rss)$')
    textFileRegex = re.compile(r'\.css$')

    log = SimpleLogger()

    def __init__(self, outputDir):
        self.outputDir = outputDir

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
