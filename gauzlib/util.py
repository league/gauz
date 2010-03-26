from genshi.core import Stream

class GauzUtils:

    def hello(self):
        return 'HeLlO!'

    def markupToString(self, value):
        if hasattr(value, '__call__'):
            value = value()
        if hasattr(value, 'next'):
            buf = []
            for k, v, _ in value:
                if Stream.TEXT == k:
                    buf.append(v)
            return ''.join(buf)
        return value

    def filter(self, assets, year=None, month=None, tag=None, ids=None):
        for a in assets:
            if ((not year or a.date and a.date.year == year) and
                (not month or a.date and a.date.month == month) and
                (not tag or tag in a.tags) and
                (not ids or a.source in ids)):
                yield a
