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
