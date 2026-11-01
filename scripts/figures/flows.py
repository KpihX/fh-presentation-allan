"""Les trois figures analytiques du support.

Chacune est produite aux dimensions exactes de la zone de planche ou elle
sera posee (`theme.FIGURE_FULL` ou `theme.FIGURE_WITH_CAPTION`), de sorte
qu'un corps de 14 points ici se projette a 14 points la-bas.

Aucun chiffre financier n'apparait dans ces figures : aucune donnee de ce
type n'a ete communiquee pendant le stage, et en inventer serait la faute
la plus grave possible devant un jury. Ce qui est represente est un
mecanisme observe, pas une comptabilite.
"""

from __future__ import annotations

import pathlib

import style
import theme
from style import (C, arrow, band, box, canvas, disc, elbow, note, photo,
                   return_path, rule, save, tag, text_block)

ASSETS = pathlib.Path(__file__).resolve().parent.parent.parent / "assets"


# ---------------------------------------------------------------------------
def fig_valeur_boucle():
    """Le moteur economique : pourquoi l'absence d'abonnement rend la R&D
    vitale plutot que decorative.

    C'est la charniere de la demonstration orale, donc la figure est
    volontairement pauvre en mots : quatre etapes, une boucle de retour,
    une phrase de consequence. Le raisonnement complet est dit, pas ecrit.
    """
    key = "valeur_boucle"
    W, H = theme.FIGURE_FULL.width, theme.FIGURE_FULL.height
    fig, ax = canvas(W, H)

    steps = (
        ("Expertise image", "R&D : hypothèses, limites", C["navy"], C["pale"]),
        ("Une version qui se voit", "produit, qualité, doc.", C["teal"], C["white"]),
        ("Achat ou mise à niveau", "e-commerce, support", C["gold"], C["white"]),
        ("Photographe", "usage, confiance", C["sage"], C["white"]),
    )
    bw, gap = 2.45, 0.55
    y, bh = 3.16, 1.30
    xs = []
    for i, (title, sub, edge, fill) in enumerate(steps):
        x = 0.02 + i * (bw + gap)
        xs.append(x)
        box(ax, x, y, bw, bh, [title, sub], fill=fill, edge=edge,
            sizes=(14, 11))
    for i in range(3):
        arrow(ax, (xs[i] + bw - 0.06, y + bh / 2),
              (xs[i + 1] + 0.06, y + bh / 2), lw=2.0)

    # Boucle de retour : ce qui distingue un modele interactif d'un couloir
    # sequentiel recherche -> produit -> marche.
    return_path(ax, (xs[3] + bw / 2, y + 0.06), (xs[0] + bw / 2, y + 0.06),
                drop=2.16,
                label="retours d'usage  →  nouvelles questions de recherche")

    band(ax, 0.02, 0.30, W - 0.04, 0.98,
         "Pas d'abonnement : aucune rente. Chaque version doit se mériter.",
         size=17, bold=True)
    tag(ax, 0.20, 4.72, "le mécanisme observé", size=11)
    return save(fig, key)


# ---------------------------------------------------------------------------
ETONNEMENTS = (
    ("1", "« Personne ne m'a dit quoi faire »",
     "Ajustement mutuel, pas laisser-faire", "navy"),
    ("2", "« Un week-end, une maquette »",
     "L'innovation déborde de la R&D", "teal"),
    ("3", "« On vend, on ne loue pas »",
     "Chaque version doit se mériter", "gold"),
)


def fig_trois_etonnements():
    """Les trois faits d'ouverture, en panneau de comparaison.

    Dessine plutot que pose en puces : trois colonnes separees par des
    filets, chacune avec son disque numerote, la phrase entendue, et sa
    lecture organisationnelle. Le meme contenu en liste a puces laisserait
    les deux tiers bas de la planche vides -- ce que la directive interdit
    explicitement ("elle ne doit etre ni vide, ni surchargee").
    """
    key = "trois_etonnements"
    W, H = theme.FIGURE_FULL.width, theme.FIGURE_FULL.height
    fig, ax = canvas(W, H)
    colw = W / 3

    for i, (num, quoted, reading, hue) in enumerate(ETONNEMENTS):
        cx = colw * (i + 0.5)
        if i:
            rule(ax, colw * i, 0.30, H - 0.10, lw=1.0)
        disc(ax, cx, H - 0.62, 0.34, num, C[hue], size=17)
        text_block(ax, cx, H - 1.42, quoted, width_chars=24, size=16,
                   bold=True, colour=C["navy"])
        ax.plot([cx - 0.70, cx + 0.70], [2.52, 2.52], color=C["gold"],
                lw=1.6, solid_capstyle="round")
        text_block(ax, cx, 2.18, reading, width_chars=26, size=14,
                   colour=C["grey_dark"])

    band(ax, 0.02, 0.28, W - 0.04, 0.86,
         "Trois faits que le modèle économique suffit à expliquer.",
         size=15, bold=True)
    return save(fig, key)


# ---------------------------------------------------------------------------
ROLES = (
    ("Fonctions corporate", "cadre et continuité", "sage"),
    ("Stratégie produit", "traduit en usage", "gold"),
    ("Marketing, support", "accès au client", "teal"),
    ("R&D", "expertise image rare", "grey_dark"),
)


def fig_pouvoir_roles():
    """L'organigramme relu comme une carte de ressources.

    Sous chaque fonction n'est pas ecrit un effectif mais ce qu'elle
    detient et que les autres ne peuvent obtenir sans elle -- la zone
    d'incertitude de Crozier et Friedberg. La disposition « Organigramme »
    du gabarit a ete ecartee : elle dispose ses six noeuds en escalier, sans
    trait de liaison, ce qui suggere une hierarchie a cinq etages qui
    n'existe pas.

    Non nominatif, comme la figure correspondante du rapport ecrit.
    """
    key = "pouvoir_roles"
    W, H = theme.FIGURE_FULL.width, theme.FIGURE_FULL.height
    fig, ax = canvas(W, H)

    top_w, top_h = 3.60, 0.86
    top_x, top_y = (W - top_w) / 2, H - top_h - 0.12
    box(ax, top_x, top_y, top_w, top_h, ["Direction générale"],
        fill=C["navy"], edge=C["navy"], text=C["white"], sizes=(15, 11))

    bw, gap, bh = 2.62, 0.35, 1.42
    y = 1.52
    x0 = (W - (4 * bw + 3 * gap)) / 2
    bus = y + bh + 0.42
    for i, (name, resource, hue) in enumerate(ROLES):
        x = x0 + i * (bw + gap)
        elbow(ax, (W / 2, top_y + 0.02), (x + bw / 2, y + bh - 0.02), bus)
        box(ax, x, y, bw, bh, [name, resource], edge=C[hue], sizes=(14, 11.5))

    band(ax, 0.02, 0.28, W - 0.04, 0.86,
         "Chacun détient ce que les autres ne peuvent obtenir seuls.",
         size=15, bold=True)
    return save(fig, key)


# ---------------------------------------------------------------------------
def fig_regimes_preuve():
    """Les deux sujets du stage cotes a cote : ils se ressemblent et ne
    donnent pas droit au meme type de conclusion.

    Les deux photographies viennent du rapport ecrit, donc de corpus
    publics deja credites la-bas (Eyeblink8 et CUHK Blur Detection) ; la
    legende de la planche le redit. Elles portent un message et ne sont pas
    de la decoration : c'est la condition posee par la directive.
    """
    key = "regimes_preuve"
    W, H = theme.FIGURE_WITH_CAPTION.width, theme.FIGURE_WITH_CAPTION.height
    fig, ax = canvas(W, H)
    half = W / 2

    rule(ax, half, 0.30, H - 0.15, lw=1.0)

    ph = 1.95
    ptop = H - 0.62
    # Gauche : une region localisable.
    tag(ax, 0.10, H - 0.22, "état des yeux", size=12, colour=C["navy"])
    photo(ax, 0.10, ptop - ph, 5.35, ph,
          ASSETS / "eye_status_detection_landmarks.png")
    ax.text(0.10, 1.62, "Une région : la frontière se nomme", ha="left",
            va="center", fontsize=14, fontweight="bold", color=C["navy"])
    note(ax, 0.10, 1.24, "une taxonomie fine, et des cas assumés ambigus",
         size=12)

    # Droite : une propriete repartie.
    tag(ax, half + 0.25, H - 0.22, "flou", size=12, colour=C["gold"])
    photo(ax, half + 1.30, ptop - ph, 2.92, ph,
          ASSETS / "blur_motion0192_width_field.png")
    ax.text(half + 0.25, 1.62, "Une propriété répartie : la position fait le sens",
            ha="left", va="center", fontsize=14, fontweight="bold",
            color=C["navy"])
    note(ax, half + 0.25, 1.24, "bokeh voulu ou mise au point manquée",
         size=12)

    band(ax, 0.02, 0.10, W - 0.04, 0.82,
         "L'un se mesure et se nomme. L'autre demande l'intention du photographe.",
         size=15, bold=True, fill=C["pale"])
    return save(fig, key)


# ---------------------------------------------------------------------------
def _stack(ax, x, y, w, h, head, items, colour):
    """Un bloc de fonction avec son entete colore et ses sous-fonctions.

    Employe seulement en annexe : sur une planche d'expose, cette densite
    violerait la regle des six lignes. En annexe, la planche n'est projetee
    que si le jury pose la question, et elle doit alors etre complete.
    """
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0,rounding_size=0.08",
        facecolor=C["white"], edgecolor=C["grey_light"], linewidth=1.2,
        zorder=2))
    ax.add_patch(FancyBboxPatch(
        (x, y + h - 0.46), w, 0.46,
        boxstyle="round,pad=0,rounding_size=0.08",
        facecolor=colour, edgecolor="none", zorder=3))
    ax.text(x + w / 2, y + h - 0.23, head, ha="center", va="center",
            fontsize=12.5, fontweight="bold", color=C["white"], zorder=4)
    for i, item in enumerate(items):
        ax.text(x + 0.18, y + h - 0.78 - i * 0.30, "·  " + item, ha="left",
                va="center", fontsize=11, color=C["grey_dark"], zorder=4)


def fig_organigramme_detail():
    """Annexe : l'organigramme fonctionnel avec ses sous-fonctions.

    Reconstitue a partir de l'organigramme interne consulte pendant le
    stage, et volontairement non nominatif : ce sont des fonctions, pas des
    personnes. Meme regle que la figure correspondante du rapport ecrit.
    """
    key = "organigramme_detail"
    W, H = theme.FIGURE_WITH_CAPTION.width, theme.FIGURE_WITH_CAPTION.height
    fig, ax = canvas(W, H)

    box(ax, W / 2 - 1.75, H - 0.90, 3.50, 0.80, ["Direction générale"],
        fill=C["navy"], edge=C["navy"], text=C["white"], sizes=(14, 11))

    cols = (
        ("Fonctions corporate", ["finance", "ressources humaines",
                                 "informatique", "sécurité"], C["sage"]),
        ("Stratégie produit", ["gestion de produit", "UX / UI",
                               "documentation"], C["gold"]),
        ("Marketing", ["e-commerce", "contenu, relations externes",
                       "support client", "développement, localisation"],
         C["teal"]),
        ("R&D", ["recherche image", "framework", "interfaces",
                 "assurance qualité", "programme, bêta-test"], C["grey_dark"]),
    )
    bw, gap = 2.62, 0.35
    total = 4 * bw + 3 * gap
    x0 = (W - total) / 2
    y, bh = 0.55, 2.40
    for i, (head, items, colour) in enumerate(cols):
        x = x0 + i * (bw + gap)
        _stack(ax, x, y, bw, bh, head, items, colour)
        arrow(ax, (W / 2, H - 0.94), (x + bw / 2, y + bh + 0.06),
              rad=0.0, lw=1.2, colour=C["grey_light"], style="-")
    note(ax, W / 2, y + bh + 0.42,
         "structure fonctionnelle, rôles non nominatifs", size=11,
         ha="center")
    return save(fig, key)


ORIENTATION = (
    ("Ce que je cherche", "navy",
     ("La R&D exploratoire", "PA en IA, vision par ordinateur")),
    ("Ce que j'écarte", "grey_dark",
     ("Exécuter un processus figé", "là où la valeur est déjà stabilisée")),
    ("Ce que je surveille", "gold",
     ("Mon surinvestissement", "cinq heures dues, souvent dépassées")),
)


def fig_orientation():
    """La projection professionnelle, en trois zones.

    Les attendus posent la question frontalement (« en quoi ce stage a-t-il
    fait evoluer mon projet academique, mon projet professionnel ? ») et
    demandent aussi, a defaut, quels metiers ne conviennent pas -- d'ou la
    colonne du milieu, qui serait autrement absente.

    La disposition « Liste a puces + armes » a ete essayee et ecartee : ses
    deux colonnes de texte chevauchent horizontalement les armes de l'Ecole
    posees au centre par le masque, et le texte devenait illisible par-dessus
    le casque.
    """
    key = "orientation"
    W, H = theme.FIGURE_FULL.width, theme.FIGURE_FULL.height
    fig, ax = canvas(W, H)
    colw = W / 3

    for i, (heading, hue, (main, aside)) in enumerate(ORIENTATION):
        cx = colw * (i + 0.5)
        if i:
            rule(ax, colw * i, 1.55, H - 0.10, lw=1.0)
        tag(ax, cx, H - 0.34, heading, size=12.5, ha="center", colour=C[hue])
        y = text_block(ax, cx, H - 1.20, main, width_chars=22, size=18,
                       bold=True, colour=C["navy"])
        ax.plot([cx - 0.62, cx + 0.62], [y - 0.10, y - 0.10], color=C[hue],
                lw=1.6, solid_capstyle="round")
        text_block(ax, cx, y - 0.46, aside, width_chars=28, size=13.5,
                   colour=C["grey_dark"])

    band(ax, 0.02, 0.28, W - 0.04, 0.94,
         "Explorer me convient. Reste à en faire une force soutenable.",
         size=16, bold=True)
    return save(fig, key)


ALL = [fig_trois_etonnements, fig_pouvoir_roles, fig_valeur_boucle,
       fig_regimes_preuve, fig_orientation, fig_organigramme_detail]

if __name__ == "__main__":
    for build in ALL:
        build()
