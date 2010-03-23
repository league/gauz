from gauzlib.config import Config
import os

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

def main(cf = Config):
    wl = Workload(cf('../www'), '.')
