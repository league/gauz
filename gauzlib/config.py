from gauzlib.assets import *
from gauzlib.load import DependencyTracker
from gauzlib.log import SimpleLogger
from gauzlib.util import GauzUtils
from genshi.template.base import Context
from optparse import OptionParser
from time import sleep
import datetime
import re

def doubly_link(ls):
    # We assume reverse-chron (in order for the next/prev to make sense).
    next = None
    for d in ls:
        d.next = next
        next = d
    prev = None
    for d in reversed(ls):
        d.prev = prev
        prev = d

class Config(object):
    reIgnoreDir = re.compile(r'^[_\.]')
    reIgnoreFile = re.compile(r'(^|/)(_|\.|\.#|#)|~$')
    reIso8601 = re.compile(r'(\d{4})[-/\.](\d{2})[-/\.](\d{2})')
    reMarkupFile = re.compile(r'\.(xml|html|xhtml|htm|rss)$')
    reTagSep = re.compile(r'[,;:\s]\s*')
    reTextFile = re.compile(r'\.css$')
    reWebPage = re.compile(r'\.(html|xhtml|htm|md)$')

    xpContent = '//body/*'
    xpDate = '//meta[@name="date"]/@content'
    xpTags = '//meta[@name="keywords"]/@content'
    xpTitle = '//head/title/text()'

    log = SimpleLogger()
    gauz = GauzUtils()
    waitIntervalSec = 2
    halfLifeInDays = 1000
    namespaces = {'py': 'http://genshi.edgewall.org/',
                  'xi': 'http://www.w3.org/2001/XInclude'}

    root = '.'
    outputDir = '_site'
    includeDirs = []
    watch = False

    def __init__(self):
        pass

    def setup(self):
        p = OptionParser()
        self.addOptions(p)
        _, args = p.parse_args(values=self)
        os.chdir(self.root)
        self.loader = DependencyTracker(self.includeDirs)
        self.filters = [re.compile(a) for a in args]

    def ensure_value(self, attr, value):
        setattr(self, attr, value)
        return value

    def addOptions(self, p):
        p.add_option('-C', '--directory', dest='root', metavar='DIR',
                     help='Change to DIR before doing anything.')
        p.add_option('-I', '--include', dest='includeDirs', metavar='DIR',
                     help='Append DIR to include path.', action='append')
        p.add_option('-o', '--output', dest='outputDir', metavar='DIR',
                     help='Write output files to DIR.')
        p.add_option('-w', '--watch', dest='watch', action='store_true',
                     help='Watch for changes in source files.')

    def pruneDirs(self, parent, dirs):
        for d in reversed(dirs): # backwards so we can safely remove
            if self.reIgnoreDir.search(d):
                dirs.remove(d)

    def makeAssetFor(self, pathname):
        if self.reIgnoreFile.search(pathname):
            return None
        if self.reMarkupFile.search(pathname):
            a = MarkupAsset(pathname, self)
        elif pathname.endswith('.md'):
            a = MarkdownAsset(pathname, self)
        elif self.reTextFile.search(pathname):
            a = TextAsset(pathname, self)
        else:
            a = LinkAsset(pathname, self)
        if pathname.find('@') >= 0:
            a = CompositeAsset(a)
        return a

    def finalizeAsset(self, a):
        a.href = a.source.replace(',', '/')
        a.target = os.path.join(self.outputDir, a.href)
        a.top = ''.join(['../' for x in a.href.split('/')[1:]])

    def makeContext(self, asset):
        return Context(page = asset, gauz = self.gauz, ord = self.ord,
                       posts = self.posts, pages = self.pages,
                       cloud = self.cloud,
                       by = {'year': self.by_year,
                             'month': self.by_month,
                             'tag': self.by_tag})

    def wait(self):
        self.log.wait()
        sleep(self.waitIntervalSec)

    def extractText(self, xml, xpath):
        stream = xml.select(xpath, namespaces = self.namespaces)
        return unicode(stream.render('text'), 'utf-8')

    def extractTitle(self, asset):
        return self.extractText(asset.xml, self.xpTitle)

    def extractContent(self, asset):
        stream = asset.xml.select(self.xpContent, namespaces = self.namespaces)
        return list(stream)

    def extractTags(self, asset):
        tags = self.extractText(asset.xml, self.xpTags)
        tags = self.reTagSep.split(tags) if tags else []
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

    def summarize(self, fileMap):
        self.posts = []         # post assets, in reverse chron
        self.pages = []         # page assets, ordered by title/source
        self.by_year = {}       # yyyy -> set(source)
        self.by_month = {}      # (yyyy,mm) -> set(source)
        self.by_tag = {}        # t -> set(source)
        for k, a in fileMap.iteritems():
            if self.isPost(a):
                self.posts.append(a)
            elif self.isPage(a):
                self.pages.append(a)
            if a.date:
                if a.date.year not in self.by_year:
                    self.by_year[a.date.year] = set()
                self.by_year[a.date.year].add(a.source)
                if (a.date.year, a.date.month) not in self.by_month:
                    self.by_month[(a.date.year, a.date.month)] = set()
                self.by_month[(a.date.year, a.date.month)].add(a.source)
            for t in a.tags:
                if t not in self.by_tag:
                    self.by_tag[t] = set()
                self.by_tag[t].add(a.source)
        self.cloud = self.makeCloud(self.posts, self.halfLifeInDays)
        self.posts.sort(key = lambda p: p.date, reverse=True)
        self.pages.sort(key = lambda p: p.title or p.source)
        doubly_link(self.posts)
        doubly_link(self.pages)
        self.ord = {'tags': sorted(self.by_tag.keys()),
                    'years': sorted(self.by_year.keys()),
                    'months': sorted(self.by_month.keys(), reverse=True)}

    def matchesFilter(self, name):
        if [] == self.filters:
            return True
        for f in self.filters:
            if f.search(name):
                return True
        return False

    def isPost(self, asset):
        return bool(asset.date)

    def isPage(self, asset):
        return self.reWebPage.search(asset.source)

    def makeCloud(self, posts, halfLife=None):
        cloud = {}
        today = datetime.date.today()
        for p in posts:
            if halfLife:
                age = today - p.date
                score = 1.0 / pow(2, float(age.days) / halfLife)
            else:
                score = 1
            for t in p.tags:
                if t not in cloud:
                    cloud[t] = score
                else:
                    cloud[t] += score
        self.normalizeCloudScores(cloud)
        return cloud

    def normalizeCloudScores(self, cloud):
        hi = None
        lo = None
        for v in cloud.itervalues():
            if not hi or v > hi:
                hi = v
            if not lo or v < lo:
                lo = v
        diff = (hi - lo) + 0.001
        for t in cloud.iterkeys():
            cloud[t] = (cloud[t]-lo)/diff
