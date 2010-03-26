from genshi.input import XML
from genshi.template import NewTextTemplate
import os

class AssetBase(object):
    def __init__(self, filename, config):
        self.source = filename
        self.config = config
        self.visited = False
        self.title = ''
        self.tags = []
        self.date = None
        self.content = ''
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
        print >>outf, stream.render('xhtml')
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
    pass
