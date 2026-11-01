"""Identite visuelle unique de presentation_x_v2.

Un seul endroit definit une couleur, une police, une taille de puce et une
coordonnee de planche. Les deux consommateurs (matplotlib pour les figures,
python-pptx pour l'assemblage) passent par des adaptateurs : c'est la
correction de la faiblesse n0 4 relevee dans le pipeline `presentation/`,
ou la meme couleur existait en trois exemplaires (hex, RGBColor, litteral).

Rien ici n'est invente. La palette et les polices sont lues dans le gabarit
officiel de l'Ecole polytechnique (`ppt/theme/theme1.xml`, clrScheme et
fontScheme) et recopiees telles quelles ; les tailles de niveau de texte
viennent des planches d'instructions que l'auteur garde en tete de chaque
presentation :

    Niveau 1 : Georgia, corps 24
    Niveau 2 : Georgia, corps 18
    Niveau 3 : Georgia gras, corps 12
    Niveau 4 : Century Gothic, corps 10
    Niveau 5 : Century Gothic, corps 10 - avec puce

    Les couleurs principales a utiliser sont le Bleu et le Dore, avec en
    complements les couleurs secondaires.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------- palette ---
# theme1.xml / <a:clrScheme name="Personnalise 4">. Source unique de verite.
NAVY = "003E5C"       # dk1  - couleur principale "Bleu"
GOLD = "A68B4E"       # accent1 - couleur principale "Dore"
GREY_DARK = "424242"  # dk2
GREY_LIGHT = "E7E6E6"  # lt2
TEAL = "006880"       # accent2
MINT = "6DCCBB"       # accent3
PALE = "D4E8EF"       # accent4
SAGE = "98B8B4"       # accent5
SKY = "96DCFF"        # accent6
WHITE = "FFFFFF"      # lt1

#: Ordre d'emploi des accents quand une figure a besoin de N teintes
#: distinctes. Bleu et Dore d'abord (regle du gabarit), secondaires ensuite.
SEQUENCE = (NAVY, GOLD, TEAL, SAGE, GREY_DARK, MINT)


def mpl(hexcode: str) -> str:
    """Adaptateur matplotlib : "003E5C" -> "#003E5C"."""
    return "#" + hexcode


def rgb(hexcode: str):
    """Adaptateur python-pptx : "003E5C" -> RGBColor(0x00, 0x3E, 0x5C)."""
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(hexcode)


# ------------------------------------------------------------- typographie ---
#: Les polices du gabarit. Jamais fixees sur le texte d'une planche : les
#: emplacements reserves les heritent du masque, ce qui est tout l'interet de
#: construire sur le gabarit plutot que sur une presentation vide.
FONT_HEAD = "Georgia"
FONT_BODY = "Century Gothic"

#: Pour les figures matplotlib uniquement. Georgia et Century Gothic ne sont
#: pas installables dans l'environnement de rendu ; on prend les substituts
#: metriquement les plus proches (serif a empattements pleins / geometrique
#: derive du Futura) afin que la figure ne jure pas avec le texte de planche.
#: Sur un poste Windows equipe du gabarit, remplacer par les vraies polices.
MPL_SERIF = ["Georgia", "Liberation Serif", "DejaVu Serif"]
MPL_GEOM = ["Century Gothic", "URW Gothic", "DejaVu Sans"]


# --------------------------------------------------- niveaux de puces ---
@dataclass(frozen=True)
class Level:
    """Un niveau de puce projete.

    `indent_in` est un retrait ABSOLU en pouces, et non un heritage du
    masque. Le masque du gabarit met `marL=0` sur ses quatre premiers
    niveaux : la hierarchie n'y est portee que par la taille. C'est
    exactement le defaut constate sur la soutenance precedente -- une
    indentation invisible depuis le fond de la salle. On empile donc trois
    signaux simultanes : saut de corps, retrait reel, puce coloree.
    """

    size: int          # corps en points, tel que defini par le gabarit
    indent_in: float   # retrait du bloc, en pouces
    bullet: str | None  # glyphe de puce, ou None
    colour: str        # couleur du texte
    bullet_colour: str  # couleur du glyphe
    space_before: int  # respiration au-dessus, en points


#: Deux niveaux, pas plus. Le gabarit descend jusqu'a Century Gothic 10, mais
#: 10 et 12 points ne se lisent pas depuis le fond d'une salle de reunion :
#: les employer serait reproduire le defaut qu'on corrige. Un troisieme
#: niveau signifie qu'une planche porte deux idees et doit etre coupee --
#: `slides.py` refuse le fichier plutot que de le rendre illisible.
LEVELS = (
    Level(size=24, indent_in=0.00, bullet=None, colour=NAVY,
          bullet_colour=GOLD, space_before=14),
    Level(size=18, indent_in=0.46, bullet="—", colour=GREY_DARK,
          bullet_colour=GOLD, space_before=6),
)

MAX_LEVEL = len(LEVELS) - 1

#: Facteur applique aux corps quand la planche partage sa largeur. Une
#: colonne de 5,5 pouces ne tient pas un Georgia 24 sans casser les lignes
#: n'importe ou ; 0,88 ramene 24/18 a 20/15, qui reste tres lisible en
#: projection et garde le rapport de hierarchie intact.
SCALE_WIDE = 1.00
SCALE_COLUMN = 0.88

#: Style des intertitres de colonne (le "EXPLORATION" / "EXPLOITATION" du
#: gabarit) : dore, capitales, plus petit que le niveau 0 qu'il coiffe.
HEADING_SIZE = 15
HEADING_COLOUR = GOLD

#: Style d'une citation mise en exergue sur une planche.
QUOTE_SIZE = 20
QUOTE_COLOUR = TEAL


# -------------------------------------------------------------- geometrie ---
@dataclass(frozen=True)
class Box:
    """Une zone de planche, en pouces (l'unite native de python-pptx)."""

    left: float
    top: float
    width: float
    height: float

    def as_emu(self):
        from pptx.util import Inches

        return (Inches(self.left), Inches(self.top),
                Inches(self.width), Inches(self.height))


#: La grille du gabarit, nommee une fois. Toutes les valeurs sont relevees
#: dans les dispositions du masque, pas choisies : une figure posee dans
#: FIGURE_FULL occupe donc exactement la zone que le gabarit reserve au
#: corps de texte, et s'aligne sur les titres des autres planches.
SLIDE = Box(0, 0, 13.333, 7.5)
TITLE = Box(0.92, 0.23, 11.50, 1.27)
FIGURE_FULL = Box(0.92, 1.72, 11.50, 4.90)
FIGURE_WITH_CAPTION = Box(0.92, 1.72, 11.50, 4.42)
CAPTION = Box(0.92, 6.20, 11.50, 0.34)
QUOTE_BAND = Box(0.92, 5.62, 11.50, 0.90)

#: Zones du gabarit reutilisees telles quelles (idx du placeholder).
PH_TITLE = 0
PH_DATE = 2          # bas-gauche : detourne en fil d'Ariane de partie
PH_SLIDE_NUMBER = 4  # bas-droite : la numerotation (x/x) exigee par le jury

CAPTION_SIZE = 11
CAPTION_COLOUR = GREY_DARK
BREADCRUMB_SIZE = 11
BREADCRUMB_COLOUR = GOLD
