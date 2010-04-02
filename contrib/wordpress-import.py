#!/usr/bin/env python
from genshi.input import HTML
from genshi.core import QName, Attrs, Stream
import MySQLdb
import os
import re

def replace_entities(s):
    s = s.replace('&', '&amp;')
    s = s.replace('$', '$$')
    return s

def strip_ctrl_m(s):
    return s.replace('\r', '')

def replace_phodb(s):
    buf = ''
    k = 0
    for m in re.finditer('\[phodb\[(\w+)\](\[\w*\])?([^\]]*)\]', s):
        buf += s[k:m.start()]
        pad = '00'+m.group(1)
        buf += ('<div class="frame_240_3 right unlink">'
                '<a href="http://contrapunctus.net/photo/show/%s%s"><img alt=""'
                ' src="http://contrapunctus.net/pix/phodb/%c/%c/%s.1.jpg" />'
                '</a>' %
                (m.group(1),
                 '?t='+m.group(2).strip('[]') if m.group(2) else '',
                 pad[-3], pad[-2], m.group(1)))
        if m.group(3):
            cap = m.group(3)
            c = db.cursor(MySQLdb.cursors.DictCursor)
            c.execute("SELECT * FROM cl_photo where ph_id=0x%s" % m.group(1))
            for p in c:
                cap = cap.replace('%t', p['ph_title'])
            buf += '<div class="caption">%s</div>' % cap
        buf += '</div>'
        k = m.end()
    buf += s[k:]
    return buf


def replace_inlinephoto(s):
    return s.replace('inlinephoto', 'frame_240_3 right unlink')

def trivial(s):
    return s == '' or s.isspace()

def paragraph_filter(stream):
    depth = 0
    npos = (None, 1, 0)
    qp = QName('p')
    startp = (Stream.START, (qp, Attrs()), npos)
    endp = (Stream.END, qp, npos)
    para = False
    for kind, data, pos in stream:
        if Stream.START == kind:
            depth += 1
            if data[0] == qp:
                para = True
            yield kind, data, pos
        elif Stream.END == kind:
            depth -= 1
            if data == qp:
                para = False
            yield kind, data, pos
        elif Stream.TEXT == kind and 0 == depth:
            if not para and not data.isspace():
                yield startp
                para = True
            gs = re.split('\\n\\n+', data)
            for i in range(len(gs)):
                yield Stream.TEXT, gs[i], pos
                if i+1 < len(gs) and not trivial(gs[i]):
                    yield endp
                    yield Stream.TEXT, '\n\n', pos
                    if trivial(gs[i+1]):
                        para = False
                    else:
                        yield startp
        else:
            yield kind, data, pos
    if para:
        yield endp

def header_demote(stream):
    h2 = QName('h2')
    h3 = QName('h3')
    for kind, data, pos in stream:
        if Stream.START == kind and data[0] == h2:
            yield Stream.START, (h3, data[1]), pos
        elif Stream.END == kind and data == h2:
            yield Stream.END, h3, pos
        else:
            yield kind, data, pos

def markup_fixes(s):
#    print "BEFORE: ", s
    # header_demote
    return HTML(s).filter(paragraph_filter).render()

content_transforms = [replace_entities, strip_ctrl_m, replace_phodb,
                      replace_inlinephoto,
                      markup_fixes]
title_transforms = [replace_entities]

def fetch_tags(db, id):
    c = db.cursor()
    c.execute("SELECT name FROM wp_term_relationships r, wp_term_taxonomy x,"+
              "wp_terms t WHERE object_id=%s and r.term_taxonomy_id = "+
              "x.term_taxonomy_id and x.term_id = t.term_id", (id,))
    ts = []
    for tag in c:
        ts.append(tag[0])
    return ts

def transform(s, ts):
    for t in ts:
        s = t(s)
    return s

def fetch_posts(db):
    c = db.cursor()
    c.execute("SELECT ID, post_name, post_date, post_title, post_content "+
              "FROM wp_posts WHERE post_status = 'publish'"
#              " AND post_name = 'ireland-in-watercolour'"
              )
    for post in c:
        tags = fetch_tags(db, post[0])
        data = {'tags': tags, 'name': post[1], 'date': post[2],
                'title': transform(post[3], title_transforms),
                'content': transform(post[4], content_transforms)}
        yield data

def format_output_path(post):
    return("blog/%d/%02d-%02d-%s.html" %
           (post['date'].year,
            post['date'].month,
            post['date'].day,
            post['name']))

def format_tags(post):
    return ', '.join(post['tags'])

def format_content(post):
    return post['content']

def post_as_html(post):
    return """
<html xmlns:xi="http://www.w3.org/2001/XInclude"
      xmlns:py="http://genshi.edgewall.org/">
  <xi:include href="post.html" />
  <head>
    <title py:replace="None">%s</title>
    <meta name="keywords" content="%s" />
  </head>
  <body>
    %s
  </body>
</html>""" % (post['title'],
              format_tags(post),
              format_content(post))

def write_post(post):
    path = format_output_path(post)
    dir = os.path.dirname(path)
    if os.path.exists(path):
        print 'EXISTS', path
    else:
        if not os.path.isdir(dir):
            print 'MKDIR ', dir
            os.makedirs(dir)
        print 'OUTPUT', path
        out = open(path, 'w')
        print >>out, post_as_html(post)
        out.close()

db = MySQLdb.connect(user="root", passwd="adminuser", db="league_wp")
for post in fetch_posts(db):
    write_post(post)



