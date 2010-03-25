from genshi.template import TemplateLoader
from genshi.template.markup import MarkupTemplate
import os

class DependencyTracker(TemplateLoader):
    def __init__(self, search_path):
        super(DependencyTracker, self).__init__(search_path, True)
        self.times = {}       # map full pathname to last known mtime
        self.depends = {}     # full pathname to set of files to rebuild

    def start(self, asset):
        self.target = asset.source
        return MarkupTemplate(asset.xml, loader=self)

    def load(self, filename, relative_to=None, cls=None, encoding=None):
        t = super(DependencyTracker, self).load(
            filename, relative_to, cls, encoding)
        self.times[t.filepath] = os.path.getmtime(t.filepath)
        if t.filepath not in self.depends:
            self.depends[t.filepath] = set([self.target])
        else:
            self.depends[t.filepath].add(self.target)
        return t
