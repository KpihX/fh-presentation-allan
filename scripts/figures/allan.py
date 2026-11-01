"""Figures analytiques de la soutenance de formation humaine d'Allan."""

from __future__ import annotations

import pathlib

from matplotlib.patches import FancyBboxPatch

from .style import C, arrow, band, box, canvas, photo, save, tag, text_block

ROOT = pathlib.Path(__file__).resolve().parents[2]
REFS = ROOT / "refs"
W, H = 11.50, 4.90


def campus():
    fig, ax = canvas(W, H)
    band(ax, 0.25, 4.12, 11.0, 0.58,
         "Former à un métier, reconstruire la confiance", bold=True, size=17)
    stats = [
        ("1866", "Fondation Apprentis d'Auteuil"),
        ("250", "élèves et apprentis"),
        ("14 ha", "un campus à Marcoussis"),
    ]
    for i, (value, label) in enumerate(stats):
        x = 0.35 + i * 3.73
        box(ax, x, 2.35, 3.30, 1.35, [value, label],
            fill=C["white"], edge=C["pale"], sizes=(25, 12))
    tag(ax, 0.45, 1.82, "UNE DOUBLE MISSION")
    box(ax, 0.45, 0.35, 4.65, 1.15,
        ["Former aux métiers", "nature et services"],
        fill=C["pale"], edge=C["pale"], sizes=(17, 12))
    box(ax, 6.40, 0.35, 4.65, 1.15,
        ["Accompagner les fragilités", "vers l'insertion"],
        fill="#F3F0E8", edge="#E7DDC5", sizes=(17, 12))
    arrow(ax, (5.15, 0.93), (6.35, 0.93), colour=C["gold"], lw=2.2)
    return save(fig, "campus")


def missions():
    fig, ax = canvas(W, H)
    centre_x, centre_y = 5.75, 2.45
    ax.add_patch(FancyBboxPatch(
        (4.30, 1.88), 2.90, 1.14,
        boxstyle="round,pad=0.08,rounding_size=0.18",
        facecolor=C["navy"], edgecolor="none", zorder=3))
    ax.text(centre_x, centre_y + 0.16, "Faire grandir", ha="center",
            va="center", color=C["white"], fontsize=18, fontweight="bold")
    ax.text(centre_x, centre_y - 0.18, "par un cadre ajusté", ha="center",
            va="center", color=C["white"], fontsize=12)
    cards = [
        (0.30, 3.20, "Accompagner", "adapter les supports"),
        (7.85, 3.20, "Soutenir", "maths et sciences"),
        (0.30, 0.40, "Encadrer", "internat et sécurité"),
        (7.85, 0.40, "Animer", "projets et médiation"),
    ]
    for x, y, title, detail in cards:
        box(ax, x, y, 3.35, 1.10, [title, detail],
            fill=C["white"], edge=C["pale"], sizes=(17, 12))
        start = (x + 3.35 if x < centre_x else x, y + 0.55)
        end = (4.22 if x < centre_x else 7.28, centre_y)
        arrow(ax, start, end, colour=C["gold"], lw=1.6)
    return save(fig, "missions")


def adaptation():
    fig, ax = canvas(W, H)
    photo(ax, 0.15, 1.15, 4.65, 3.55, REFS / "3EB0036A34A1E53318DE51.jpeg")
    photo(ax, 6.70, 1.15, 4.65, 3.55, REFS / "3EB032EE457435C50D3748.jpeg")
    ax.text(2.48, 0.72, "Mesurer pour comprendre", ha="center", va="center",
            fontsize=14, color=C["navy"], fontweight="bold")
    ax.text(9.02, 0.72, "Manipuler pour calculer", ha="center", va="center",
            fontsize=14, color=C["navy"], fontweight="bold")
    arrow(ax, (4.95, 2.93), (6.55, 2.93), colour=C["gold"], lw=2.4)
    text_block(ax, 5.75, 2.55, "Observer avant d'expliquer", width_chars=18,
               size=13, colour=C["teal"], bold=True, va="center")
    return save(fig, "adaptation")


def projects():
    fig, ax = canvas(W, H)
    photo(ax, 0.15, 1.55, 3.65, 3.15, REFS / "3EB072F026B77B43652EB1.jpeg")
    photo(ax, 7.70, 1.55, 3.65, 3.15, REFS / "3EB031B1B5BC8B1F2CDAF1.jpeg")
    box(ax, 3.93, 1.55, 3.65, 3.15,
        ["Tournoi sur un mois", "sport", "mathématiques", "végétaux + culture"],
        fill=C["pale"], edge=C["pale"], sizes=(16, 12))
    labels = [
        (0.15, "Ciné-débat", "Faire parler sans imposer"),
        (3.93, "Tournoi", "Mobiliser des profils variés"),
        (7.70, "Soirée camerounaise", "Anticiper budget et quantités"),
    ]
    for x, title, lesson in labels:
        ax.text(x + 1.825, 1.18, title, ha="center", va="center",
                fontsize=15, color=C["navy"], fontweight="bold")
        ax.text(x + 1.825, 0.72, lesson, ha="center", va="center",
                fontsize=11.5, color=C["grey_dark"])
    return save(fig, "projects")


def hierarchy():
    fig, ax = canvas(W, H)
    steps = [
        (0.15, "Idée", "besoin observé"),
        (2.48, "Formalisation", "budget et risques"),
        (4.81, "Validation", "chef de service"),
        (7.14, "Action", "équipe mobilisée"),
        (9.47, "Retour", "expérience vécue"),
    ]
    for i, (x, title, detail) in enumerate(steps):
        box(ax, x, 1.75, 1.90, 1.45, [title, detail],
            fill=C["white"] if i % 2 == 0 else C["pale"],
            edge=C["pale"], sizes=(14, 10.5))
        if i < len(steps) - 1:
            arrow(ax, (x + 1.90, 2.47), (x + 2.28, 2.47),
                  colour=C["gold"], lw=1.9)
    band(ax, 1.35, 3.68, 8.80, 0.62,
         "La hiérarchie transforme une initiative en action sûre",
         bold=True, size=16)
    band(ax, 2.20, 0.50, 7.10, 0.55,
         "Sécuriser ne signifie pas empêcher", fill="#F3F0E8", size=14)
    return save(fig, "hierarchy")


def transformation():
    fig, ax = canvas(W, H)
    tag(ax, 0.30, 4.55, "AVANT")
    tag(ax, 4.72, 4.55, "DÉCLIC")
    tag(ax, 9.15, 4.55, "APRÈS")
    rows = [
        ("Méthode standard", "Observer l'élève", "Approche concrète"),
        ("Souplesse", "Cadre insuffisant", "Exigence calme"),
        ("Réserve", "Aller vers l'équipe", "Confiance partagée"),
        ("Stress diffus", "Décomposer le risque", "Anticipation"),
    ]
    y = 3.55
    for left, middle, right in rows:
        box(ax, 0.20, y, 3.05, 0.70, [left], sizes=(13, 10), pad=0.06)
        box(ax, 4.23, y, 3.05, 0.70, [middle], fill=C["pale"],
            edge=C["pale"], sizes=(13, 10), pad=0.06)
        box(ax, 8.26, y, 3.05, 0.70, [right], fill="#F3F0E8",
            edge="#E7DDC5", sizes=(13, 10), pad=0.06)
        arrow(ax, (3.30, y + 0.35), (4.18, y + 0.35), colour=C["gold"], lw=1.5)
        arrow(ax, (7.33, y + 0.35), (8.21, y + 0.35), colour=C["gold"], lw=1.5)
        y -= 0.90
    return save(fig, "transformation")


ALL = (campus, missions, adaptation, projects, hierarchy, transformation)
