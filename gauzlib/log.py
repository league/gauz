class SimpleLogger:
    # flag to indicate whether we've recently informed user we're
    # waiting for changes
    waiting = False

    def action(self, verb, obj):
        self.waiting = False
        print '%-8s %s' % (verb, obj)

    def wait(self):
        if not self.waiting:
            print 'Awaiting changes...'
            self.waiting = True

