from genshi.template import NewTextTemplate
import os

class AssetBase(object):
    def __init__(self, filename, config):
        self.source = filename
        self.config = config
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
    pass

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
