# -*- coding: utf-8 -*-
from genshi.builder import tag
from genshi.core import Stream, Markup
from genshi.template import NewTextTemplate
import random

class GauzUtils:

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

    def monthly(self, assets):
        first = True
        cur = None
        for a in assets:
            if cur != a.date.month:
                br = tag.a(name = a.date.strftime('%m'))
                if not first:
                    br = tag(br, tag.div(class_ = 'archive-break'))
                yield br
                cur = a.date.month
            yield a
            first = False

    def yearly(self, assets):
        first = True
        cur = None
        for a in assets:
            if cur != a.date.year:
                br = tag.a(name = str(a.date.year))
                if not first:
                    br = tag(br, tag.div(class_ = 'archive-break'))
                yield br
                cur = a.date.year
            yield a
            first = False

    def expandText(self, text, page):
        tmpl = NewTextTemplate(text)
        return tmpl.generate(page.config.makeContext(page))

    def jsQuote(self, frag, subst):
        r = str(frag).replace('"', '\\"')
        r = r.replace('%s', '"+'+subst+'+"')
        return '"'+r+'"'

    def randomlyPartition(self, chars='abcdefghijklmnopqrstuvwxyz1234567890'):
        alpha = [c for c in chars] # must be a list
        random.shuffle(alpha)      # for shuffle to work
        mid = len(alpha)/2
        one = alpha[:mid]
        two = alpha[mid:]
        return ''.join(one), ''.join(two)

    def buildObfuscatedString(self, text, valid, ignore):
        either = valid + ignore
        buf = []
        i = 0;
        while i < len(text):
            if random.randint(0,2): # .33 probability of ignore block
                buf.append(random.choice(valid))
                buf.append(text[i])
                i += 1
            else:
                buf.append(random.choice(ignore))
                buf.append(random.choice(either))
        return ''.join(buf)

    def obfuscate(self, clearText,
                  format='<a href="mailto:%s">%s</a>',
                  noscript='%s',
                  at = u' § ', dot = u' · '):
        humanText = clearText.replace('@', at).replace('.', dot)
        valid, ignore = self.randomlyPartition()
        obfuText = self.buildObfuscatedString(humanText, valid, ignore)
        expr = '"' + obfuText + '"'
        expr += '.replace(/([%s](.)|[%s].)/ig,"$2")' % (valid, ignore)
        expr += '.replace(/%s/g, "@")' % at
        expr += '.replace(/%s/g, ".")' % dot
        var = 's%06x' % random.randrange(0x1000000)
        format = self.jsQuote(format, var)
        t = tag(tag.script('var ', var, ' = ', expr, ';\n',
                           'document.write(', Markup(format), ');\n',
                           type='text/javascript'))
        if noscript:
            t = t(tag.noscript(noscript.replace('%s', humanText)))
        return t
