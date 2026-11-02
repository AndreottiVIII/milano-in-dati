"""Piccolo albero DOM costruito con html.parser (solo libreria standard)."""
import html
import re
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP_TEXT = {"script", "style", "noscript", "svg", "template"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag, attrs=None, parent=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.children = []  # Node oppure str
        self.parent = parent

    @property
    def cls(self):
        return (self.attrs.get("class") or "").split()

    def iter(self):
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def text(self):
        if self.tag in SKIP_TEXT:
            return ""
        out = []
        for c in self.children:
            if isinstance(c, str):
                out.append(c)
            else:
                t = c.text()
                if c.tag in ("p", "li", "div", "br", "h1", "h2", "h3", "h4", "tr", "ul", "ol", "table", "section", "details", "summary"):
                    out.append(" " + t + " ")
                else:
                    out.append(t)
        return clean("".join(out))


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


class _B(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def parse(src):
    b = _B()
    b.feed(src)
    return b.root
