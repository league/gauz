# -*- coding: utf-8 -*-
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

    def obfuscate(self, email, mailto=True):
        import random
        email = email.replace('@', ' ') # sub space for at sign
        # Split the alphabet randomly into two parts.
        alpha = [c for c in 'abcdefghijklmnopqrstuvwxyz1234567890']
        random.shuffle(alpha)
        mid = len(alpha)/2
        valid = alpha[:mid]
        ignore = alpha[mid:]
        # Now we randomly choose whether to output a character of the
        # email address (preceded by a random member of valid) or a
        # totally random character (preceded by member of ignore).
        ls = []
        i = 0
        while i < len(email):
            if random.randint(0,1): # flip a coin
                ls.append(random.choice(valid))
                ls.append(email[i])
                i += 1
            else:
                ls.append(random.choice(ignore))
                ls.append(random.choice(alpha))
        # Finally, output the javascript to decode it
        return ('''<script type="text/javascript">
var cl_obfu = "%s".replace(/([%s](.)|[%s].)/ig, "$2").replace(/ /, "@");
document.write(%s);
</script><noscript>%s</noscript>''' %
                (''.join(ls), ''.join(valid), ''.join(ignore),
                 '"<a href=\'mailto:"+cl_obfu+"\'>"+cl_obfu+"</a>"'
                 if mailto else 'cl_obfu',
                 email.replace(' ', u' § ').replace('.', u' • ')))
