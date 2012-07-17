from genshi.input import XML
from genshi.template import NewTextTemplate
import copy
import os

class AssetBase(object):
    def __init__(self, filename, config):
        self.config = config
        self.content = ''
        self.date = None
        self.source = filename
        self.tags = []
        self.title = ''
        self.visited = False
        self.read()
        config.finalizeAsset(self)

    def read(self):
        # By default, just grab file modification time.  This method
        # should return True to indicate there have been *significant*
        # changes (that will affect site-wide metadata).
        self.mtime = os.path.getmtime(self.source)
        return False

    def generate(self):
        self.config.log.action('IGN', self.source)

    def maybeMakeParentDir(self, target):
        d = os.path.dirname(target)
        if not os.path.isdir(d):
            self.config.log.action('MKDIR', d)
            os.makedirs(d)

class MarkupAsset(AssetBase):
    def read(self):
        self.mtime = os.path.getmtime(self.source)
        self.config.log.action('READ', self.source)
        inf = open(self.source)
        buf = inf.read()
        inf.close()
        self.xml = XML(buf)
        self.changed = False
        self.noticeChange('title', self.config.extractTitle(self))
        self.noticeChange('tags', self.config.extractTags(self))
        self.noticeChange('date', self.config.extractDate(self))
        self.content = self.config.extractContent(self)
        return self.changed

    def noticeChange(self, attr, value):
        try:
            if getattr(self, attr) != value:
                self.recordChange(attr, value)
        except AttributeError:
            self.recordChange(attr, value)

    def recordChange(self, attr, value):
        setattr(self, attr, value)
        self.changed = True

    def generate(self):
        tmpl = self.config.loader.start(self)
        self.maybeMakeParentDir(self.target)
        self.config.log.action('WRITE', self.target)
        outf = open(self.target, 'w')
        stream = tmpl.generate(self.config.makeContext(self))
        docty = 'html' if self.target.endswith('html') else None
        print >>outf, stream.render('xhtml', doctype=docty,
                                    strip_whitespace=False)
        outf.close()


class TextAsset(AssetBase):
    def generate(self):
        inf = open(self.source)
        tmpl = NewTextTemplate(inf.read())
        inf.close()
        self.maybeMakeParentDir(self.target)
        self.config.log.action('WRITE', self.target)
        outf = open(self.target, 'w')
        print >>outf, tmpl.generate(self.config.makeContext(self))
        outf.close()

class LinkAsset(AssetBase):
    def generate(self):
        if not os.path.exists(self.target):
            self.maybeMakeParentDir(self.target)
            self.config.log.action('LINK', self.target)
            os.link(self.source, self.target)

class CompositeAsset(AssetBase):
    # has one source but many targets
    def __init__(self, orig):
        self.orig = orig
        self.config = orig.config

    def __getattr__(self, name):
        return getattr(self.orig, name)

    def read(self):
        return self.orig.read()

    def generate(self):
        self.copy = copy.copy(self.orig)
        self.expandTags(self.orig.source)

    def expandTags(self, source):
        if source.find('@TAG') >= 0:
            for t in self.config.ord['tags']:
                self.copy.tag = t
                self.expandDates(source.replace('@TAG', t))
        else:
            self.expandDates(source)

    def expandDates(self, source):
        if source.find('@MM') >= 0: # assumes MM also uses YYYY
            for y,m in self.config.ord['months']:
                self.copy.yyyy = y
                self.copy.mm = m
                yy = str(y)
                mm = '%02d' % m
                h = source.replace('@YYYY', yy).replace('@MM', mm)
                self.genInstance(h)
        elif source.find('@YYYY') >= 0:
            for y in self.config.ord['years']:
                self.copy.yyyy = y
                yy = str(y)
                self.genInstance(source.replace('@YYYY', yy))
        else:
            self.genInstance(source)

    def genInstance(self, source):
        self.copy.source = source # virtual source; file won't exist
        self.config.finalizeAsset(self.copy)
        self.copy.source = self.source # restore actual source
        self.copy.generate()
