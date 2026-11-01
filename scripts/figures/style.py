"""Primitives de dessin partagees par toutes les figures.

Deux regles tenues dans tout le dossier :

1. Aucune couleur n'est ecrite ici. Elles viennent toutes de `theme.py`, qui
   les lit du gabarit officiel. Ce module ne fait que les convertir.
2. Une figure est produite AUX DIMENSIONS EXACTES de la zone ou elle sera
   posee, en pouces. Consequence : `fontsize=14` dans une figure se projette
   a 14 points sur la planche, comme un texte d'emplacement reserve. C'est
   la seule facon d'avoir une typographie coherente entre une planche de
   puces et une planche de figure -- et donc de garantir la lisibilite
   depuis le fond de la salle, qui est la contrainte de conception n0 1.

`savefig` est appele SANS `bbox_inches="tight"` : le recadrage automatique
changerait les dimensions du PNG et casserait ce rapport de 1 pour 1.
"""

from __future__ import annotations

import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import theme  # noqa: E402

FIGS = pathlib.Path(__file__).resolve().parent.parent.parent / "build" / "figs"
DPI = 200

C = {name: theme.mpl(getattr(theme, name.upper()))
     for name in ("navy", "gold", "grey_dark", "grey_light", "teal", "mint",
                  "pale", "sage", "sky", "white")}

matplotlib.rcParams.update({
    "font.family": theme.MPL_SERIF,
    "text.color": C["navy"],
    "figure.facecolor": C["white"],
    "savefig.facecolor": C["white"],
    "savefig.dpi": DPI,
    "axes.facecolor": C["white"],
})


def canvas(width_in: float, height_in: float):
    """Des axes dont l'unite de donnee EST le pouce.

    Un rectangle a coins arrondis reste donc arrondi et non ovalise, et une
    coordonnee de figure se raisonne dans la meme unite que la grille de
    planche de `theme.py`.
    """
    fig = plt.figure(figsize=(width_in, height_in))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, width_in)
    ax.set_ylim(0, height_in)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def save(fig, key: str) -> pathlib.Path:
    FIGS.mkdir(parents=True, exist_ok=True)
    path = FIGS / f"{key}.png"
    fig.savefig(path, dpi=DPI)          # jamais bbox_inches="tight"
    plt.close(fig)
    print(f"[figures] {key}.png")
    return path


# ------------------------------------------------------------- primitives ---
def box(ax, x, y, w, h, lines, *, fill=None, edge=None, text=None,
        sizes=(14, 11), pad=0.10, lw=1.4):
    """Un bloc a coins arrondis portant une a trois lignes.

    `lines` : la premiere est le libelle (corps `sizes[0]`), les suivantes
    la precision (corps `sizes[1]`), plus claires.
    """
    fill = fill or C["white"]
    edge = edge or C["grey_light"]
    text = text or C["navy"]
    ax.add_patch(FancyBboxPatch(
        (x + pad, y + pad), w - 2 * pad, h - 2 * pad,
        boxstyle=f"round,pad={pad},rounding_size=0.10",
        facecolor=fill, edgecolor=edge, linewidth=lw, zorder=2))
    lines = [ln for ln in lines if ln]
    n = len(lines)
    gap = 0.235
    y0 = y + h / 2 + (n - 1) * gap / 2
    for i, line in enumerate(lines):
        ax.text(x + w / 2, y0 - i * gap, line, ha="center", va="center",
                fontsize=sizes[0] if i == 0 else sizes[1],
                color=text if i == 0 else C["grey_dark"],
                fontweight="bold" if i == 0 else "normal", zorder=3)


def arrow(ax, start, end, *, colour=None, lw=1.8, rad=0.0, label=None,
          label_offset=(0, 0.18), size=11, style="-|>"):
    colour = colour or C["gold"]
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=15,
        connectionstyle=f"arc3,rad={rad}", color=colour, linewidth=lw,
        shrinkA=2, shrinkB=2, zorder=1))
    if label:
        mx = (start[0] + end[0]) / 2 + label_offset[0]
        my = (start[1] + end[1]) / 2 + label_offset[1]
        ax.text(mx, my, label, ha="center", va="center", fontsize=size,
                color=C["grey_dark"], zorder=3,
                bbox=dict(boxstyle="round,pad=0.18", facecolor=C["white"],
                          edgecolor="none"))


def band(ax, x, y, w, h, text, *, fill=None, colour=None, size=14,
         bold=False, italic=False, align="center"):
    """Un aplat clair portant une phrase : sert aux enonces de contrainte."""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor=fill or C["pale"], edgecolor="none", zorder=1))
    ha = {"center": "center", "left": "left"}[align]
    tx = x + w / 2 if align == "center" else x + 0.18
    ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=size,
            color=colour or C["navy"], fontweight="bold" if bold else "normal",
            style="italic" if italic else "normal", zorder=3)


def rule(ax, x, y0, y1, *, colour=None, lw=1.2):
    ax.plot([x, x], [y0, y1], color=colour or C["grey_light"], lw=lw,
            zorder=1, solid_capstyle="round")


def tag(ax, x, y, text, *, colour=None, size=11, ha="left"):
    """Une etiquette en capitales doree : sert de sur-titre de zone."""
    ax.text(x, y, text.upper(), ha=ha, va="center", fontsize=size,
            color=colour or C["gold"], fontweight="bold", zorder=3)


def note(ax, x, y, text, *, size=11, colour=None, ha="left", italic=True):
    ax.text(x, y, text, ha=ha, va="center", fontsize=size,
            color=colour or C["grey_dark"],
            style="italic" if italic else "normal", zorder=3)


def photo(ax, x, y, w, h, path, *, frame=True):
    """Pose une photographie dans une boite, recadree au centre pour
    remplir exactement w x h sans deformation."""
    import matplotlib.image as mpimg

    img = mpimg.imread(str(path))
    ih, iw = img.shape[0], img.shape[1]
    want = w / h
    have = iw / ih
    if have > want:                       # trop large : rogner les cotes
        keep = int(ih * want)
        off = (iw - keep) // 2
        img = img[:, off:off + keep]
    else:                                 # trop haut : rogner haut et bas
        keep = int(iw / want)
        off = (ih - keep) // 2
        img = img[off:off + keep, :]
    ax.imshow(img, extent=(x, x + w, y, y + h), aspect="auto", zorder=2)
    if frame:
        ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="square,pad=0",
            facecolor="none", edgecolor=C["grey_light"], linewidth=1.2,
            zorder=3))


def wrap(text: str, width_chars: int) -> list[str]:
    """Decoupe un texte en lignes. matplotlib ne fait aucun retour a la
    ligne automatique : sans cela un libelle deborde silencieusement de sa
    colonne, ce qui ne se voit qu'apres rendu."""
    import textwrap

    return textwrap.wrap(text, width=width_chars) or [""]


def text_block(ax, x, y, text, *, width_chars, size, colour=None, bold=False,
               italic=False, ha="center", leading=None, va="top"):
    """Un paragraphe centre, coupe a `width_chars`, dessine ligne par ligne.

    Retourne le `y` atteint sous la derniere ligne, pour empiler la suite
    sans coordonnee magique.
    """
    lines = wrap(text, width_chars)
    lead = leading if leading is not None else size / 72 * 1.30
    if va == "center":
        y = y + (len(lines) - 1) * lead / 2
    for i, line in enumerate(lines):
        ax.text(x, y - i * lead, line, ha=ha, va="center", fontsize=size,
                color=colour or C["navy"],
                fontweight="bold" if bold else "normal",
                style="italic" if italic else "normal", zorder=3)
    return y - (len(lines) - 1) * lead - lead


def disc(ax, x, y, r, label, colour, *, size=17):
    """Un disque plein portant un chiffre ou deux lettres."""
    ax.add_patch(plt.Circle((x, y), r, facecolor=colour, edgecolor="none",
                            zorder=3))
    ax.text(x, y, label, ha="center", va="center", color=C["white"],
            fontsize=size, fontweight="bold", zorder=4)


def elbow(ax, top, bottom, bus_y, *, colour=None, lw=1.2):
    """Un connecteur coude parent -> enfant, passant par une barre
    horizontale a la hauteur `bus_y`. Trois segments explicites plutot
    qu'une courbe : la geometrie est previsible, donc verifiable."""
    colour = colour or C["grey_light"]
    ax.plot([top[0], top[0]], [top[1], bus_y], color=colour, lw=lw, zorder=1)
    ax.plot([top[0], bottom[0]], [bus_y, bus_y], color=colour, lw=lw, zorder=1)
    ax.plot([bottom[0], bottom[0]], [bus_y, bottom[1]], color=colour, lw=lw,
            zorder=1)


def return_path(ax, start, end, drop, *, colour=None, lw=1.8, label=None,
                size=12):
    """Une fleche de retour qui descend, traverse, et remonte.

    Remplace un `arc3` : l'arc calculait sa courbure a partir de la corde et
    passait DERRIERE les blocs qu'il etait cense contourner, donc
    invisible. Un chemin en trois segments passe ou on le lui dit.
    """
    from matplotlib.patches import FancyArrowPatch

    colour = colour or C["teal"]
    ax.plot([start[0], start[0]], [start[1], drop], color=colour, lw=lw,
            zorder=1, solid_capstyle="round")
    ax.plot([start[0], end[0]], [drop, drop], color=colour, lw=lw, zorder=1,
            solid_capstyle="round")
    ax.add_patch(FancyArrowPatch((end[0], drop), (end[0], end[1]),
                                 arrowstyle="-|>", mutation_scale=15,
                                 color=colour, linewidth=lw, shrinkA=0,
                                 shrinkB=2, zorder=1))
    if label:
        ax.text((start[0] + end[0]) / 2, drop, label, ha="center",
                va="center", fontsize=size, color=colour, style="italic",
                zorder=3,
                bbox=dict(boxstyle="round,pad=0.28", facecolor=C["white"],
                          edgecolor="none"))
