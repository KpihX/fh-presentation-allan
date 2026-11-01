"""Badges circulaires : noeuds de l'organigramme, et pictogrammes numerotes.

Pourquoi des monogrammes et non des icones : la directive demande que « les
pictogrammes soient univoques et non interpretables ». Une icone dessinee a
la main pour « strategie produit » ou « fonctions corporate » serait
exactement le contraire. Un monogramme sobre, avec le role ecrit juste en
dessous par la disposition du gabarit, ne laisse aucune ambiguite.

Les couleurs suivent `theme.SEQUENCE` : Bleu et Dore d'abord, comme le
prescrivent les planches d'instructions du gabarit.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

import style
from style import C, save

#: (cle de figure, monogramme, couleur). L'ordre suit la lecture de
#: l'organigramme : sommet, puis les quatre fonctions.
NODES = (
    ("badge_dg", "DG", C["navy"]),
    ("badge_produit", "SP", C["gold"]),
    ("badge_marche", "MK", C["teal"]),
    ("badge_corporate", "FC", C["sage"]),
    ("badge_rd", "R&D", C["grey_dark"]),
)


def _disc(key, label, colour, size_in=1.57, ring=True):
    fig, ax = style.canvas(size_in, size_in)
    r = size_in / 2
    if ring:
        ax.add_patch(plt.Circle((r, r), r * 0.98, facecolor="none",
                                edgecolor=colour, linewidth=1.0, alpha=0.35))
    ax.add_patch(plt.Circle((r, r), r * 0.84, facecolor=colour,
                            edgecolor="none"))
    ax.text(r, r, label, ha="center", va="center", color=C["white"],
            fontsize=15 if len(label) <= 2 else 13, fontweight="bold")
    return save(fig, key)


def fig_org_badges():
    return [_disc(key, label, colour) for key, label, colour in NODES]


def fig_pictos():
    """Trois disques numerotes pour les colonnes du triptyque.

    Rendus carres a la hauteur de l'emplacement image du gabarit
    (1,18 x 0,78 pouce) : le disque occupe la hauteur, le blanc lateral est
    absorbe par le centrage de `deck.fit_picture`.
    """
    out = []
    for n, colour in enumerate((C["navy"], C["teal"], C["gold"]), start=1):
        out.append(_disc(f"picto_{n}", str(n), colour, size_in=0.78,
                         ring=False))
    return out


def fig_puces():
    """Deux marqueurs pleins, un par colonne, pour la disposition
    « Deux colonnes evenements ». Un simple aplat rond colore : il tient le
    rythme vertical de la colonne sans pretendre illustrer quoi que ce soit,
    et reste donc univoque au sens de la directive."""
    import matplotlib.pyplot as plt

    out = []
    for n, colour in enumerate((C["navy"], C["gold"]), start=1):
        fig, ax = style.canvas(0.78, 0.78)
        ax.add_patch(plt.Circle((0.39, 0.39), 0.15, facecolor=colour,
                                edgecolor="none"))
        ax.add_patch(plt.Circle((0.39, 0.39), 0.27, facecolor="none",
                                edgecolor=colour, linewidth=1.1, alpha=0.45))
        out.append(save(fig, f"puce_{n}"))
    return out


ALL = [fig_org_badges, fig_pictos, fig_puces]

if __name__ == "__main__":
    for build in ALL:
        build()
