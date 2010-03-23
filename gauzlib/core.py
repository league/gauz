from gauzlib.config import Config
import os
import traceback

class Workload:
    def __init__(self, config, root):
        self.config = config
        self.root = root
        self.fileMap = {}       # relative, normalized file path -> asset
        for parent, dirs, names in os.walk(root):
            config.pruneDirs(parent, dirs)
            for n in names:
                f = os.path.normpath(os.path.join(parent, n))
                a = config.makeAssetFor(f)
                if a:
                    self.fileMap[f] = a
        config.summarize(self.fileMap)
        for a in self.fileMap.itervalues():
            a.generate()

    def update(self):
        self.checkForUpdates()
        if self.metaChanged:
            self.config.summarize(self.fileMap)
        for a in self.fileMap.itervalues():
            a.visited = False
        for f in self.filesChanged:
            self.fileMap[f].generate()
            self.fileMap[f].visited = True
        self.checkIncludes()
        if self.metaChanged:
            for a in self.fileMap.itervalues():
                if not a.visited:
                    a.generate()

    def checkForUpdates(self):
        self.filesChanged = []   # List of new or updated files
        self.metaChanged = False # Did metadata change significantly?
        for a in self.fileMap.itervalues():
            a.visited = False # Use visit flag to detect removed files
        for parent, dirs, names in os.walk(self.root):
            self.config.pruneDirs(parent, dirs)
            for n in names:
                f = os.path.normpath(os.path.join(parent, n))
                if f in self.fileMap:
                    self.visitOldFile(self.fileMap[f])
                else:
                    self.visitNewFile(self.config.makeAssetFor(f))
        self.pruneUnvisited()

    def visitOldFile(self, a):
        a.visited = True
        if a.mtime != os.path.getmtime(a.source):
            self.filesChanged.append(a.source)
            self.metaChanged = a.read()

    def visitNewFile(self, a):
        if a:
            a.visited = True
            self.fileMap[a.source] = a
            self.filesChanged.append(a.source)
            self.metaChanged = True

    def pruneUnvisited(self):
        for f, a in self.fileMap.items():
            if not a.visited:
                del self.fileMap[f]
                self.metaChanged = True

    def checkIncludes(self):
        for inc,t0 in self.config.loader.times.iteritems():
            t1 = os.path.getmtime(inc)
            if t0 != t1:
                self.config.log.action('CHANGE', inc)
                for f in self.config.loader.depends[inc]:
                    if not self.fileMap[f].visited:
                        self.fileMap[f].generate()
                        self.fileMap[f].visited = True


def main(CF = Config):
    cf = CF('../www', ['../include'])
    wl = Workload(cf, '.')
    while 1:
        cf.wait()
        try:
            wl.update()
        except:
            traceback.print_exc()
