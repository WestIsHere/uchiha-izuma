"""Prépare la candidature après une modification de index.html.

1. Corrige la typographie française dans le texte de la page
   (apostrophes courbes, espaces insécables avant : ; ! ? et dans les guillemets).
2. Met à jour la liste des caractères japonais chargés depuis Google Fonts.
3. Régénère candidature.txt, la version texte à coller dans le launcher.

Usage (depuis le dossier du projet) :  python tools/build.py
Le script ne dépend que de la bibliothèque standard de Python.
"""

from __future__ import annotations

import html
import re
import sys
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
TXT = ROOT / "candidature.txt"

# Adresse publique du site, ajoutée en tête de la version texte si elle est renseignée.
SITE_URL = "https://westishere.github.io/uchiha-izuma/"

NBSP = " "
NNBSP = " "


# --------------------------------------------------------------------------
# 1. Typographie
# --------------------------------------------------------------------------

def fix_text(t: str) -> str:
    t = t.replace("'", "’")
    t = t.replace("...", "…")
    t = re.sub(r" ([?!;])", NNBSP + r"\1", t)
    t = re.sub(r" :", NBSP + ":", t)
    t = re.sub(r"« ", "«" + NBSP, t)
    t = re.sub(r" »", NBSP + "»", t)
    t = re.sub(r"— ", "—" + NBSP, t)
    return t


def fix_typography(src: str) -> str:
    start = src.index("<body")
    end = src.index("</body>")
    body = src[start:end]
    # On ne touche ni aux balises, ni aux scripts, ni aux styles.
    parts = re.split(r"(<script\b.*?</script>|<style\b.*?</style>|<[^>]+>)", body, flags=re.S)
    for i, part in enumerate(parts):
        if i % 2 == 0 and part:
            parts[i] = fix_text(part)
    return src[:start] + "".join(parts) + src[end:]


# --------------------------------------------------------------------------
# 2. Sous-ensemble japonais
# --------------------------------------------------------------------------

def bust_cache(src: str) -> str:
    """Ajoute à la feuille de style et au script un paramètre lié à leur contenu."""
    import hashlib
    for rel in ("assets/css/style.css", "assets/js/main.js"):
        digest = hashlib.md5((ROOT / rel).read_bytes()).hexdigest()[:8]
        src = re.sub(re.escape(rel) + r'(\?v=[0-9a-f]*)?"', f'{rel}?v={digest}"', src)
    return src


def update_jp_subset(src: str) -> str:
    chars = sorted(set(re.findall(r"[　-ヿ㐀-鿿]", src)))
    text = urllib.parse.quote("".join(chars))
    return re.sub(r'(family=Shippori\+Mincho[^"]*?&amp;text=|family=Shippori\+Mincho[^"]*?&text=)[^"]*',
                  lambda m: m.group(1) + text, src)


# --------------------------------------------------------------------------
# 3. Version texte
# --------------------------------------------------------------------------

VOID = {"br", "img", "hr", "meta", "link", "input", "source"}


class Node:
    def __init__(self, tag: str, attrs: dict[str, str], parent: "Node | None"):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[Node | str] = []

    @property
    def classes(self) -> set[str]:
        return set(self.attrs.get("class", "").split())

    def find(self, cls: str) -> "Node | None":
        for c in self.children:
            if isinstance(c, Node):
                if cls in c.classes:
                    return c
                hit = c.find(cls)
                if hit:
                    return hit
        return None


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def skipped(n: Node) -> bool:
    a = n.attrs
    return (
        a.get("data-export") == "skip"
        or a.get("aria-hidden") == "true"
        or n.tag in {"figcaption", "img", "svg", "button", "script", "style", "textarea", "dialog"}
    )


BR = "\x00"


def inline(n: Node | str) -> str:
    """Texte d'un nœud, sur une ligne ; seuls les <br> deviennent des retours."""
    if isinstance(n, str):
        return re.sub(r"[ \t\r\n]+", " ", n)
    if skipped(n):
        return ""
    if n.tag == "br":
        return BR
    if n.tag == "del":
        return "[barré : " + "".join(inline(c) for c in n.children).strip() + "]"
    inner = "".join(inline(c) for c in n.children)
    if "tampon" in n.classes:
        return " [" + inner.strip() + "]"
    return inner


def clean(s: str) -> str:
    s = re.sub(r"[ \t\r\n]+", " ", s)
    return "\n".join(line.strip() for line in s.split(BR)).strip()


ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


class Exporter:
    def __init__(self):
        self.out: list[str] = []

    def emit(self, s: str = ""):
        self.out.append(s)

    def para(self, s: str):
        s = clean(s)
        if s:
            self.emit(s)
            self.emit("")

    def rule(self, title: str, kicker: str = ""):
        bar = "═" * 48
        self.emit("")
        self.emit(bar)
        self.emit(title.upper() + (f"  ·  {kicker}" if kicker else ""))
        self.emit(bar)
        self.emit("")

    def walk(self, n: Node | str):
        if isinstance(n, str):
            if n.strip():
                self.para(n)
            return
        if skipped(n):
            return
        cls = n.classes
        t = n.tag

        if "ouverture" in cls:
            return self.opening(n)
        if "partie__tete" in cls:
            kicker = n.find("partie__kicker")
            h2 = next((c for c in n.children if isinstance(c, Node) and c.tag == "h2"), None)
            return self.rule(clean(inline(h2)) if h2 else "", clean(inline(kicker)) if kicker else "")
        if "chap__tete" in cls:
            num = clean(inline(n.find("chap__num")))
            title = clean(inline(n.find("chap__titre")))
            age = clean(inline(n.find("chap__age")))
            self.emit("")
            self.emit("─" * 32)
            self.emit(f"{num}. {title}".upper() if num not in {"Prologue", "Épilogue"} else f"{num.upper()} — {title.upper()}")
            if age:
                self.emit(f"({age})")
            self.emit("─" * 32)
            self.emit("")
            return
        if "carnet" in cls and t == "aside":
            return self.notebook(n)
        if "epigraphe" in cls:
            body = clean(inline(next(c for c in n.children if isinstance(c, Node) and c.tag == "p")))
            foot = next((c for c in n.children if isinstance(c, Node) and c.tag == "footer"), None)
            for line in body.split("\n"):
                self.emit("    " + line)
            if foot:
                self.emit("    — " + clean(inline(foot)))
            self.emit("")
            return
        if t == "hr":
            self.emit("· · ·")
            self.emit("")
            return
        if t == "dl":
            return self.definitions(n)
        if "paire" in cls:
            return self.pair(n)
        if "encadre" in cls:
            self.emit(f"[{n.attrs.get('data-titre', '')}]")
            for c in n.children:
                self.walk(c)
            return
        if "page" in cls and t == "article":
            return self.page(n)
        if "definition" in cls and t == "aside":
            self.emit("OMOKAGE (面影), nom japonais")
            for c in n.children:
                if isinstance(c, Node) and c.tag == "ol":
                    for i, li in enumerate([x for x in c.children if isinstance(x, Node)], 1):
                        self.emit(f"  {i}. {clean(inline(li))}")
                if isinstance(c, Node) and "definition__exemple" in c.classes:
                    self.emit("  " + clean(inline(c)))
            self.emit("")
            return
        if t in {"ul", "ol"}:
            return self.listing(n)
        if t in {"h3", "h4"}:
            title = clean(inline(n))
            self.emit("")
            self.emit(title.upper() if t == "h4" else title)
            self.emit("-" * min(len(title), 48) if t == "h3" else "")
            return
        if t in {"p", "blockquote"}:
            if "note-hrp" in cls:
                self.para(f"[{n.attrs.get('data-titre', 'Note hors RP')}] " + inline(n))
            else:
                self.para(inline(n))
            return
        for c in n.children:
            self.walk(c)

    def opening(self, n: Node):
        self.emit("OMOKAGE — ce qui reste d'un visage")
        self.emit("Candidature au clan Uchiha")
        self.emit("")
        qui = n.find("ouverture__qui")
        phrase = n.find("ouverture__phrase")
        if qui:
            self.emit(clean(inline(qui)))
        if phrase:
            self.emit(clean(inline(phrase)))
        if SITE_URL:
            self.emit("")
            self.emit(f"Version illustrée : {SITE_URL}")
        self.emit("")

    def definitions(self, n: Node):
        items = [c for c in n.children if isinstance(c, Node)]
        for dt, dd in zip(items[0::2], items[1::2]):
            label = clean(inline(dt))
            if dd.find("lignee"):
                lineage = dd.find("lignee")
                names = [clean(inline(li)) for li in lineage.children if isinstance(li, Node)]
                rest = clean("".join(inline(c) for c in dd.children if c is not lineage))
                value = " → ".join(names) + (f". {rest}" if rest else "")
            else:
                value = clean(inline(dd))
            self.emit(f"{label} : {value}")
        self.emit("")

    def listing(self, n: Node):
        cls = n.classes
        items = [c for c in n.children if isinstance(c, Node) and c.tag == "li"]
        if "scenes" in cls:
            for i, li in enumerate(items, 1):
                self.scene(li, i)
            return
        for i, li in enumerate(items):
            if "toc" in cls:
                continue
            if "choix" in cls:
                prefix = f"{ROMAN[i]}. "
            elif "verifs" in cls:
                prefix = "✓ "
            elif "lignee" in cls:
                continue
            else:
                prefix = "• "
            sub = [c for c in li.children if isinstance(c, Node) and c.tag in {"ul", "ol"}]
            text = clean("".join(inline(c) for c in li.children if c not in sub))
            self.emit(prefix + text)
            for s in sub:
                for sli in [c for c in s.children if isinstance(c, Node)]:
                    self.emit("    – " + clean(inline(sli)))
        self.emit("")

    def scene(self, li: Node, index: int):
        h3 = next(c for c in li.children if isinstance(c, Node) and c.tag == "h3")
        self.emit(f"{index:02d} · {clean(inline(h3))}")
        for c in li.children:
            if isinstance(c, Node) and c.tag == "p":
                txt = clean(inline(c))
                self.emit(f"({txt})" if "scene__qui" in c.classes else txt)
        self.emit("")

    def notebook(self, n: Node):
        title = n.find("carnet__titre")
        label = " — ".join(clean(inline(s)) for s in title.children if isinstance(s, Node)) if title else "Carnet"
        self.emit(f"[ {label} ]")
        for entry in [c for c in n.children if isinstance(c, Node) and "carnet__entree" in c.classes]:
            for c in entry.children:
                if not isinstance(c, Node):
                    continue
                if c.tag == "h4":
                    self.emit("  " + clean(inline(c)).upper())
                elif c.tag == "p":
                    raw = inline(c).lstrip(" ")
                    indent = "      " if raw.startswith(NBSP) else "    "
                    self.emit(indent + clean(raw))
            self.emit("")

    def pair(self, n: Node):
        h3 = next(c for c in n.children if isinstance(c, Node) and c.tag == "h3")
        self.emit(clean(inline(h3)).upper())
        for div in [c for c in n.children if isinstance(c, Node) and c.tag == "div"]:
            label_node = div.find("libelle-mobile")
            label = clean(inline(label_node)) if label_node else ""
            body = " ".join(clean(inline(c)) for c in div.children if isinstance(c, Node) and c is not label_node)
            self.emit(f"  {label} : {body}")
        self.emit("")

    def page(self, n: Node):
        h3 = next(c for c in n.children if isinstance(c, Node) and c.tag == "h3")
        stamp = n.find("tampon")
        self.emit(clean(inline(h3)).upper() + (f"  [{clean(''.join(inline(c) for c in stamp.children))}]" if stamp else ""))
        idx = n.find("page__indices")
        if idx:
            self.emit("  (carnet) " + clean(inline(idx)).replace("\n", " / "))
        txt = n.find("page__texte")
        if txt:
            for p in [c for c in txt.children if isinstance(c, Node)]:
                self.emit("  " + clean(inline(p)))
        self.emit("")


def export_text(src: str) -> str:
    builder = TreeBuilder()
    builder.feed(src)
    main = None
    stack = [builder.root]
    while stack:
        node = stack.pop()
        if node.tag == "main":
            main = node
            break
        stack.extend(c for c in node.children if isinstance(c, Node))
    exp = Exporter()
    for c in main.children:
        exp.walk(c)
    text = "\n".join(exp.out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


def main() -> int:
    src = INDEX.read_text(encoding="utf-8")
    fixed = bust_cache(update_jp_subset(fix_typography(src)))
    if fixed != src:
        INDEX.write_text(fixed, encoding="utf-8")
        print("index.html : typographie et sous-ensemble japonais mis à jour.")
    else:
        print("index.html : déjà à jour.")
    text = export_text(fixed)
    TXT.write_text(text, encoding="utf-8")
    words = len(re.findall(r"\w+", text))
    print(f"candidature.txt : {len(text)} caractères, environ {words} mots.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
