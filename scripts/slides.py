"""Lecture des `slides/*.md`. Analyse seulement : ne dessine rien, ne place
rien, ne choisit aucune couleur.

Trois corrections deliberees par rapport au parseur du pipeline
`presentation/` dont ce dossier reprend la philosophie :

1. Le front-matter est du vrai YAML (`yaml.safe_load`), delimite par des
   `---` en debut de ligne. L'ancien `text.split("---", 2)` se decalait
   silencieusement des qu'un `---` apparaissait dans une note d'orateur.
2. Les puces existent, avec des niveaux reels exprimes par l'indentation.
   C'etait l'absence la plus couteuse : sans niveau, une hierarchie doit
   etre simulee a la main dans le texte ("-   ", "   -> "), ce qui produit
   exactement l'indentation invisible qu'on corrige ici.
3. Un niveau au-dela de `theme.MAX_LEVEL` est une erreur fatale, pas un
   rendu degrade. Trois niveaux de puces sur une planche projetee veut dire
   que la planche porte deux idees : elle doit etre coupee.
"""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass, field

import yaml

import theme

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLIDES = ROOT / "slides"

_FRONT = re.compile(r"\A---[ \t]*\n(.*?)\n---[ \t]*\n", re.DOTALL)
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_BULLET = re.compile(r"^(?P<pad>[ \t]*)-[ \t]+(?P<text>.*\S)[ \t]*$")
_SECTION = re.compile(r"^##[ \t]+(?P<name>.*\S)[ \t]*$")

#: Une indentation de deux espaces vaut un niveau. Les tabulations sont
#: converties, pour qu'un editeur mal configure ne change pas le rendu.
INDENT_UNIT = 2


@dataclass(frozen=True)
class Bullet:
    """Une ligne projetee.

    `cells` est le decoupage sur ` | ` : certaines dispositions du gabarit
    demandent plusieurs champs par entree (un noeud d'organigramme = cle de
    badge + role + ressource ; une entree de frise = date + libelle). Plutot
    que d'inventer une syntaxe par disposition, une puce porte des cellules
    et la fonction de remplissage decide de leur sens.
    """

    text: str
    level: int
    cells: tuple[str, ...]


@dataclass
class Section:
    """Un bloc du corps. `name` est None pour le bloc d'ouverture."""

    name: str | None
    bullets: list[Bullet] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)

    @property
    def depth(self) -> int:
        return max((b.level for b in self.bullets), default=-1)


@dataclass
class Slide:
    path: pathlib.Path
    meta: dict
    sections: list[Section]
    notes: str
    label: str = ""      # "3" pour une planche d'expose, "A2" pour une annexe

    # -- acces au front-matter, valide par ailleurs (voir `deck.SPECS`) -----
    @property
    def layout(self) -> str:
        return self.meta["layout"]

    @property
    def title(self) -> str:
        return self.meta.get("title", "")

    @property
    def part(self) -> str:
        """Le fil d'Ariane, pose dans la zone date du gabarit."""
        return self.meta.get("part", "")

    @property
    def figure(self) -> str:
        return self.meta.get("figure", "")

    @property
    def image(self) -> str:
        return self.meta.get("image", "")

    @property
    def caption(self) -> str:
        return self.meta.get("caption", "")

    @property
    def quote(self) -> str:
        return self.meta.get("quote", "")

    @property
    def is_annexe(self) -> bool:
        return self.path.name.startswith("A")

    # -- acces au corps ----------------------------------------------------
    @property
    def body(self) -> Section:
        """Le bloc sans nom. Toujours present, eventuellement vide."""
        for s in self.sections:
            if s.name is None:
                return s
        return Section(None)

    @property
    def columns(self) -> list[Section]:
        """Les blocs nommes, dans l'ordre du fichier."""
        return [s for s in self.sections if s.name is not None]

    def column(self, name: str) -> Section:
        for s in self.sections:
            if s.name == name:
                return s
        raise SystemExit(
            f"{self.path.name}: bloc `## {name}` absent. "
            f"Blocs presents : {[s.name for s in self.columns]}")

    @property
    def depth(self) -> int:
        return max((s.depth for s in self.sections), default=-1)

    @property
    def line_count(self) -> int:
        """Nombre de lignes de texte projetees, intertitres compris.

        C'est la grandeur que la directive de soutenance plafonne
        ("il est habituel qu'une planche comporte moins de six lignes").
        """
        n = sum(len(s.bullets) for s in self.sections)
        n += sum(1 for s in self.columns)
        n += 1 if self.quote else 0
        return n


def _levels_ok(path: pathlib.Path, level: int, text: str) -> None:
    if level > theme.MAX_LEVEL:
        raise SystemExit(
            f"{path.name}: puce de niveau {level} (« {text[:40]} »). "
            f"Le maximum projetable est {theme.MAX_LEVEL} "
            f"(corps {theme.LEVELS[-1].size} pt). Au-dela, le gabarit "
            f"descend a 12 puis 10 points, illisibles depuis le fond de la "
            f"salle. Coupez la planche en deux au lieu d'ajouter un niveau.")


def parse(path: pathlib.Path) -> Slide:
    raw = path.read_text(encoding="utf-8")
    m = _FRONT.match(raw)
    if not m:
        raise SystemExit(f"{path.name}: front-matter `---` absent en tete.")
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"{path.name}: front-matter YAML invalide -- {exc}")
    if not isinstance(meta, dict):
        raise SystemExit(f"{path.name}: le front-matter doit etre un mapping.")
    if "layout" not in meta:
        raise SystemExit(f"{path.name}: champ `layout:` obligatoire.")

    body = _COMMENT.sub("", raw[m.end():])
    sections: list[Section] = [Section(None)]
    notes: list[str] = []
    in_notes = False

    for line in body.splitlines():
        sec = _SECTION.match(line)
        if sec:
            name = sec.group("name")
            if name.lower() == "notes":
                in_notes = True
                continue
            in_notes = False
            sections.append(Section(name))
            continue
        if in_notes:
            notes.append(line)
            continue
        bul = _BULLET.match(line)
        if bul:
            pad = bul.group("pad").replace("\t", " " * INDENT_UNIT)
            level, rest = divmod(len(pad), INDENT_UNIT)
            if rest:
                raise SystemExit(
                    f"{path.name}: indentation de {len(pad)} espaces devant "
                    f"« {bul.group('text')[:34]} ». Utilisez des multiples "
                    f"de {INDENT_UNIT}.")
            text = bul.group("text")
            _levels_ok(path, level, text)
            cells = tuple(c.strip() for c in text.split("|"))
            sections[-1].bullets.append(Bullet(cells[0] if len(cells) == 1
                                               else text, level, cells))
            continue
        if line.strip():
            sections[-1].lines.append(line.strip())

    sections = [s for s in sections
                if s.name is not None or s.bullets or s.lines]
    return Slide(path=path, meta=meta, sections=sections,
                 notes="\n".join(notes).strip())


def load() -> list[Slide]:
    """Toutes les planches, expose d'abord puis annexes.

    Le nombre en tete de nom de fichier est une CLE DE TRI, pas un numero de
    planche : inserer une planche entre la 4 et la 5 s'ecrit `04b_...md` et
    ne renomme rien. Les annexes commencent par `A` et sont numerotees a
    part, parce que la directive les autorise apres la conclusion sans
    qu'elles comptent dans la douzaine de planches utiles.
    """
    paths = sorted(SLIDES.glob("*.md"), key=lambda p: p.name)
    if not paths:
        raise SystemExit(f"aucune planche sous {SLIDES}")
    talk = [p for p in paths if not p.name.startswith("A")]
    annexes = [p for p in paths if p.name.startswith("A")]

    out: list[Slide] = []
    for n, p in enumerate(talk, start=1):
        s = parse(p)
        s.label = str(n)
        out.append(s)
    total = len(talk)
    for s in out:
        s.meta.setdefault("_total", total)
    for n, p in enumerate(annexes, start=1):
        s = parse(p)
        s.label = f"A{n}"
        s.meta["_total"] = total
        out.append(s)
    return out
