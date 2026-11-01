"""Assemblage du .pptx sur le gabarit officiel de l'Ecole polytechnique.

Ce module n'ecrit aucune phrase. Tout mot visible sur une planche vient de
`slides/*.md`. Il ne choisit pas non plus une couleur ni un corps : tout
vient de `theme.py`. Il sait seulement OU les choses se posent dans chacune
des dispositions du gabarit.

Fichier de base : `Template_X.pptx`, la presentation de l'auteur. Ce
n'est pas son ancien contenu qui compte, ce sont ses trois premieres
planches : les instructions officielles du gabarit (palette, usage du
masque, niveaux de texte, enregistrement en .potx), que l'auteur garde
deliberement en tete de chacune de ses presentations. Elles portent
`show="0"` : presentes dans le fichier, absentes du diaporama projete. On
les conserve intactes, on supprime les planches de contenu qui suivent, et
on reconstruit avec les dispositions du meme masque.
"""

from __future__ import annotations

import pathlib

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

import slides as slidesmod
import theme

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = ROOT / "assets" / "Template_X.pptx"
FIGS = ROOT / "build" / "figs"
OUT = ROOT / "build" / "Presentation_FH_X2025_Allan_TAMO.pptx"

#: Les trois planches d'instructions du gabarit, toujours conservees.
KEPT = 3

ROMAN = ("I", "II", "III", "IV", "V", "VI")


# ============================================================ primitives ===
def _layout(prs, name):
    for lay in prs.slide_masters[0].slide_layouts:
        if lay.name == name:
            return lay
    have = sorted(l.name for l in prs.slide_masters[0].slide_layouts)
    raise SystemExit(
        f"disposition inconnue dans le gabarit : {name!r}\ndisponibles : {have}"
    )


def _drop_content_slides(prs):
    """Retire les planches de contenu du fichier de base.

    On supprime la relation AVANT de retirer l'entree de `sldIdLst` : sortir
    la seule entree laisse la part orpheline dans le zip, ce dont la couche
    OPC se plaint a chaque enregistrement.
    """
    lst = prs.slides._sldIdLst
    for sldId in list(lst)[KEPT:]:
        rId = sldId.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        prs.part.drop_rel(rId)
        lst.remove(sldId)


def _ph(slide):
    return {p.placeholder_format.idx: p for p in slide.placeholders}


def _drop_ph(slide, *idxs):
    """Retire des emplacements reserves non utilises.

    Un emplacement vide n'est pas neutre : PowerPoint y affiche son texte
    d'invite ("Texte", "Prenom Nom") a l'edition, et LibreOffice le rend
    parfois a l'export. Ce qui ne sert pas est retire, pas laisse vide.
    """
    for idx in idxs:
        for p in list(slide.placeholders):
            if p.placeholder_format.idx == idx:
                p._element.getparent().remove(p._element)
                break


def _layout_box(layout, idx, *, widen=0.0):
    """La geometrie d'un emplacement de la disposition, en pouces."""
    for p in layout.placeholders:
        if p.placeholder_format.idx == idx:
            return theme.Box(
                Emu(p.left).inches,
                Emu(p.top).inches,
                Emu(p.width).inches + widen,
                Emu(p.height).inches,
            )
    return None


def _pPr(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    return pPr


def _no_bullet(paragraph):
    pPr = _pPr(paragraph)
    for tag in ("a:buChar", "a:buAutoNum", "a:buNone", "a:buClr", "a:buFont"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    pPr.append(pPr.makeelement(qn("a:buNone"), {}))


def _bullet(paragraph, glyph, colour, font=theme.FONT_HEAD):
    pPr = _pPr(paragraph)
    for tag in ("a:buChar", "a:buAutoNum", "a:buNone", "a:buClr", "a:buFont"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    clr = pPr.makeelement(qn("a:buClr"), {})
    srgb = pPr.makeelement(qn("a:srgbClr"), {"val": colour})
    clr.append(srgb)
    pPr.append(clr)
    pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": font}))
    pPr.append(pPr.makeelement(qn("a:buChar"), {"char": glyph}))


def _spacing(paragraph, before_pt, line_pct=None):
    pPr = _pPr(paragraph)
    for tag in ("a:lnSpc", "a:spcBef"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    if line_pct is not None:
        ln = pPr.makeelement(qn("a:lnSpc"), {})
        pct = pPr.makeelement(qn("a:spcPct"), {"val": str(int(line_pct * 1000))})
        ln.append(pct)
        pPr.insert(0, ln)
    sb = pPr.makeelement(qn("a:spcBef"), {})
    pts = pPr.makeelement(qn("a:spcPts"), {"val": str(int(before_pt * 100))})
    sb.append(pts)
    pPr.append(sb)


def _indent(paragraph, marL_in, indent_in):
    pPr = _pPr(paragraph)
    pPr.set("marL", str(int(Inches(marL_in))))
    pPr.set("indent", str(int(Inches(indent_in))))


def _write(
    paragraph, text, *, size, colour, bold=False, italic=False, font=None, caps=False
):
    """Ecrit un fragment, avec une police explicite.

    Pourquoi explicite : les emplacements de corps n'heritent pas tous de la
    meme fonte selon la disposition (« Liste a puces + armes » descend sur
    Century Gothic la ou « Bloc de texte » reste en Georgia), ce qui donnait
    deux planches voisines dans deux typographies.

    Pourquoi ce seuil : les planches d'instructions du gabarit prescrivent
    Georgia pour les niveaux 1 a 3 (24, 18 et 12 points) et Century Gothic
    pour les niveaux 4 et 5 (10 points). On applique la meme frontiere --
    Georgia pour le propos, Century Gothic pour l'appareil (legendes, fil
    d'Ariane, numeros, dates de frise).
    """
    if font is None:
        font = theme.FONT_HEAD if size >= 13 else theme.FONT_BODY
    run = paragraph.add_run()
    run.text = text.upper() if caps else text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = theme.rgb(colour)
    if font:
        run.font.name = font
    return run


def _clear(tf):
    """Vide un cadre de texte en gardant son unique paragraphe.

    Retire aussi les `a:fld`, et pas seulement les `a:r`. C'est ce qui
    manquait : l'emplacement de numero du gabarit contient un CHAMP
    automatique (`<a:fld type="slidenum">`), que `paragraph.runs` n'expose
    pas. Sans cette ligne, le champ continue de rendre l'index reel de la
    planche dans le fichier -- instructions du gabarit comprises -- et notre
    propre texte s'ajoutait derriere : la planche 2 affichait « 52/12 ».
    """
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    for extra in list(tf.paragraphs[1:]):
        extra._p.getparent().remove(extra._p)
    for tag in ("a:r", "a:fld", "a:br"):
        for el in p0._p.findall(qn(tag)):
            p0._p.remove(el)
    return p0


def _paragraphs(tf, count):
    """Rend `count` paragraphes vides, prets a etre remplis."""
    first = _clear(tf)
    out = [first]
    for _ in range(count - 1):
        out.append(tf.add_paragraph())
    return out


def set_text(
    placeholder,
    text,
    *,
    size=None,
    colour=None,
    bold=False,
    italic=False,
    caps=False,
    align=None,
):
    tf = placeholder.text_frame
    p = _clear(tf)
    _no_bullet(p)
    _indent(p, 0, 0)
    if align is not None:
        p.alignment = align
    if size is None and colour is None and not bold and not italic and not caps:
        p.add_run().text = text
        return
    _write(
        p,
        text,
        size=size or theme.LEVELS[0].size,
        colour=colour or theme.NAVY,
        bold=bold,
        italic=italic,
        caps=caps,
    )


def set_bullets(
    placeholder,
    bullets,
    *,
    heading=None,
    quote=None,
    scale=theme.SCALE_WIDE,
    anchor=MSO_ANCHOR.MIDDLE,
):
    """Ecrit une liste a puces avec les niveaux REELS du gabarit.

    C'est le coeur de la correction demandee. Sur la soutenance precedente,
    la hierarchie etait tapee a la main dans le texte (« -   », « -> ») et
    tous les paragraphes restaient au niveau 0 : le jury, a distance, ne
    voyait aucune structure. Ici chaque niveau cumule trois signaux
    simultanes, tous lisibles depuis le fond d'une salle :

      * un saut de corps         (24 -> 18 points, ratio 3/4) ;
      * un retrait absolu reel   (`marL`, que le masque laisse a zero) ;
      * une puce doree suspendue (`indent` negatif) sur les sous-niveaux.

    `heading` (intertitre de colonne) et `quote` (citation) sont poses en
    tete, chacun sur son paragraphe, avant les puces.
    """
    tf = placeholder.text_frame
    tf.word_wrap = True
    # Le bloc est centre verticalement dans l'emplacement, et non colle en
    # haut. Six lignes ancrees en haut d'une zone de 4,6 pouces laissent un
    # vide de trois pouces sous le texte : la planche parait inachevee alors
    # qu'elle respecte la regle des six lignes. Centrer rend le meme contenu
    # deliberement aere plutot que tronque.
    tf.vertical_anchor = anchor
    n = len(bullets) + (1 if heading else 0) + (1 if quote else 0)
    if n == 0:
        return
    paras = _paragraphs(tf, n)
    i = 0

    if heading:
        p = paras[i]
        i += 1
        _no_bullet(p)
        _indent(p, 0, 0)
        _spacing(p, 0)
        # Pas de passage en capitales : le gabarit les autorise, mais la
        # substitution de Georgia par un rendu qui n'a pas toutes les
        # capitales accentuees decompose « È » en « E` ». Constate sur
        # « LE PROBLÈME POSÉ ». Le dore et le gras suffisent a distinguer
        # un intertitre, sans dependre de la fonte disponible.
        _write(
            p,
            heading,
            size=round(theme.HEADING_SIZE * scale),
            colour=theme.HEADING_COLOUR,
            bold=True,
        )

    if quote:
        p = paras[i]
        i += 1
        _no_bullet(p)
        _indent(p, 0, 0)
        _spacing(p, 6 if heading else 0, line_pct=95)
        _write(
            p,
            f"« {quote} »",
            size=round(theme.QUOTE_SIZE * scale),
            colour=theme.QUOTE_COLOUR,
            italic=True,
        )

    for bullet in bullets:
        lvl = theme.LEVELS[bullet.level]
        p = paras[i]
        i += 1
        p.level = bullet.level
        if lvl.bullet:
            # 0,38 et non 0,26 : le cadratin occupe presque tout un retrait
            # de 0,26 pouce, et la puce venait coller le texte
            # (« —repérer »). Le retrait suspendu doit valoir la largeur du
            # glyphe PLUS une chasse visible.
            hang = 0.38
            _indent(p, lvl.indent_in + hang, -hang)
            _bullet(p, lvl.bullet, lvl.bullet_colour)
        else:
            _indent(p, lvl.indent_in, 0)
            _no_bullet(p)
        _spacing(p, lvl.space_before, line_pct=92)
        _write(p, bullet.text, size=round(lvl.size * scale), colour=lvl.colour)


def fit_picture(slide, box, path, *, anchor="center"):
    """Pose une image dans `box` sans la deformer, centree.

    Les figures sont produites aux dimensions exactes de leur zone, donc
    l'ajustement ne joue que pour les photographies du rapport, dont le
    rapport d'aspect est impose par la source.
    """
    from PIL import Image

    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(box.width / (iw / 96), box.height / (ih / 96))
    w = (iw / 96) * scale
    h = (ih / 96) * scale
    left = box.left + (box.width - w) / 2
    top = box.top if anchor == "top" else box.top + (box.height - h) / 2
    return slide.shapes.add_picture(
        str(path), Inches(left), Inches(top), Inches(w), Inches(h)
    )


def textbox(
    slide,
    box,
    text,
    *,
    size,
    colour,
    bold=False,
    italic=False,
    align=PP_ALIGN.LEFT,
    caps=False,
):
    shape = slide.shapes.add_textbox(*box.as_emu())
    tf = shape.text_frame
    tf.word_wrap = True
    p = _clear(tf)
    p.alignment = align
    _no_bullet(p)
    _write(p, text, size=size, colour=colour, bold=bold, italic=italic, caps=caps)
    return shape


def cover_rect(slide, box):
    """Masque une decoration de la disposition avec un aplat de fond.

    Employe une seule fois, sur le sommaire : la disposition « Sommaire 4
    parties » imprime un « p. » en dur a cote de chaque titre de partie,
    pour un renvoi de pagination. Or la directive de cette annee tranche :
    « L'indication dans le sommaire des numeros de planche des differentes
    parties est inutile. » Le « p. » vit dans la disposition et non dans la
    planche : on ne peut donc pas le supprimer par planche sans toucher au
    masque -- ce qu'on refuse de faire. On le couvre.
    """
    from pptx.enum.shapes import MSO_SHAPE

    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, *box.as_emu())
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor.from_string(theme.WHITE)
    shape.line.fill.background()
    shape.shadow.inherit = False
    shape.text_frame.text = ""
    return shape


def separator(slide, *, x, top, bottom, colour=theme.GREY_LIGHT):
    """Un filet vertical fin, dans le gris clair du gabarit."""
    from pptx.enum.shapes import MSO_CONNECTOR

    line = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(top), Inches(x), Inches(bottom)
    )
    line.line.color.rgb = theme.rgb(colour)
    line.line.width = Pt(1.0)
    return line


def _figure_path(slide):
    if slide.image:
        p = (ROOT / slide.image).resolve()
    elif slide.figure:
        p = FIGS / f"{slide.figure}.png"
    else:
        raise SystemExit(f"{slide.path.name}: `figure:` ou `image:` attendu.")
    if not p.exists():
        raise SystemExit(f"{slide.path.name}: fichier absent -- {p}")
    return p


# ======================================================== remplissages ===
# Une fonction par disposition du gabarit. Chacune declare, dans `SPECS`,
# ce qu'elle exige du markdown : `render.py check` croise les deux et
# refuse un fichier incomplet AVANT de produire un pptx trompeur.


def fill_couverture(slide, s, layout):
    """« La premiere planche suit les memes regles que la page de couverture
    du rapport ecrit » : nom de l'eleve, dates du stage, intitule, entite
    d'accueil et sa localisation. Le logo de l'Ecole est deja dans la
    disposition, et c'est le plus visible -- exigence explicite."""
    ph = _ph(slide)
    set_text(ph[10], s.title)
    set_text(ph[11], s.meta["auteur"])
    set_text(ph[12], f"{s.meta['entite']}  ·  {s.meta['periode']}")


def fill_sommaire(slide, s, layout):
    """Sommaire a quatre parties : titres de niveau 1 uniquement.

    Les emplacements ne sont pas dans l'ordre de lecture. Releve par
    coordonnees dans la disposition : au-dessus de chaque titre se trouve
    une zone de numero de partie, et sous chaque titre un renvoi « p. ## ».
    Paire par paire, de haut en bas et de gauche a droite :
        haut-gauche  titre 31, numero 72, pagination 71
        haut-droite  titre 34, numero 70, pagination 69
        bas-gauche   titre 37, numero 68, pagination 67
        bas-droite   titre 40, numero 66, pagination 64
    """
    ph = _ph(slide)
    zones = ((31, 72, 71), (34, 70, 69), (37, 68, 67), (40, 66, 64))
    parts = [b for b in s.body.bullets if b.level == 0]
    if len(parts) != 4:
        raise SystemExit(f"{s.path.name}: 4 parties attendues, {len(parts)} lues.")
    for (t_idx, n_idx, p_idx), roman, bullet in zip(zones, ROMAN, parts):
        set_text(ph[t_idx], bullet.text)
        set_text(
            ph[n_idx],
            roman,
            size=theme.HEADING_SIZE,
            colour=theme.GOLD,
            bold=True,
            align=PP_ALIGN.CENTER,
        )
        _drop_ph(slide, p_idx)
    # Les quatre « p. » de la disposition, couverts (voir cover_rect).
    for left, top in ((2.95, 3.78), (9.11, 3.78), (2.95, 6.24), (9.11, 6.24)):
        cover_rect(slide, theme.Box(left, top, 1.24, 0.42))


def fill_triptyque(slide, s, layout):
    """Trois colonnes, chacune : un intertitre, un pictogramme numerote,
    puis des entrees « libelle | precision ». Les emplacements image et
    texte sont apparies par ligne, releves par coordonnees."""
    ph = _ph(slide)
    heads = (10, 26, 35)
    rows = (
        ((56, 18), (55, 44), (58, 45), (57, 46)),
        ((60, 47), (59, 48), (62, 49), (61, 50)),
        ((64, 51), (63, 52), (66, 53), (65, 54)),
    )
    cols = s.columns
    if len(cols) != 3:
        raise SystemExit(f"{s.path.name}: 3 blocs attendus, {len(cols)} lus.")
    used = set()
    for c, (head_idx, row_set, col) in enumerate(zip(heads, rows, cols)):
        set_text(
            ph[head_idx],
            col.name,
            size=theme.HEADING_SIZE,
            colour=theme.NAVY,
            bold=True,
        )
        used.add(head_idx)
        for r, (pic_idx, body_idx) in enumerate(row_set):
            if r >= len(col.bullets):
                continue
            bullet = col.bullets[r]
            main, aside = (list(bullet.cells) + [""])[:2]
            paras = _paragraphs(ph[body_idx].text_frame, 2 if aside else 1)
            _no_bullet(paras[0])
            _indent(paras[0], 0, 0)
            _spacing(paras[0], 0)
            _write(paras[0], main, size=14, colour=theme.GREY_DARK)
            if aside:
                _no_bullet(paras[1])
                _indent(paras[1], 0, 0)
                _spacing(paras[1], 2, line_pct=92)
                _write(paras[1], aside, size=11.5, colour=theme.GREY_DARK)
            used.add(body_idx)
            if r == 0:
                pic = FIGS / f"picto_{c + 1}.png"
                if pic.exists():
                    box = ph[pic_idx]
                    fit_picture(
                        slide,
                        theme.Box(
                            Emu(box.left).inches,
                            Emu(box.top).inches,
                            Emu(box.width).inches,
                            Emu(box.height).inches,
                        ),
                        pic,
                    )
                    _drop_ph(slide, pic_idx)
                    used.add(pic_idx)
    for idx in list(ph):
        if idx not in used and idx not in (
            theme.PH_TITLE,
            theme.PH_DATE,
            theme.PH_SLIDE_NUMBER,
        ):
            _drop_ph(slide, idx)


def fill_organigramme(slide, s, layout):
    """Cinq noeuds sur les six emplacements de la disposition : un sommet,
    deux au milieu, deux aux extremites basses -- la seule combinaison
    symetrique. Le sixieme (centre bas, idx 12 et ses libelles 28/29) est
    retire.

    Chaque noeud porte un role et, en dessous, sa ressource propre : la
    disposition prevoit « Prenom Nom » puis « Poste », on y met un role
    collectif puis sa zone d'incertitude. L'organigramme devient ainsi une
    lecture du pouvoir et non une decoration -- et il reste non nominatif,
    comme la figure correspondante du rapport ecrit.
    """
    ph = _ph(slide)
    slots = ((10, 20, 21), (11, 24, 25), (13, 26, 27), (15, 18, 19), (16, 22, 23))
    nodes = s.column("Noeuds").bullets
    if len(nodes) != 5:
        raise SystemExit(f"{s.path.name}: 5 noeuds attendus, {len(nodes)} lus.")
    for (pic_idx, name_idx, role_idx), bullet in zip(slots, nodes):
        key, role, ressource = (list(bullet.cells) + ["", ""])[:3]
        img = FIGS / f"{key}.png"
        if not img.exists():
            raise SystemExit(f"{s.path.name}: badge absent -- {img}")
        box = ph[pic_idx]
        fit_picture(
            slide,
            theme.Box(
                Emu(box.left).inches,
                Emu(box.top).inches,
                Emu(box.width).inches,
                Emu(box.height).inches,
            ),
            img,
        )
        _drop_ph(slide, pic_idx)
        set_text(
            ph[name_idx],
            role,
            size=13,
            colour=theme.NAVY,
            bold=True,
            align=PP_ALIGN.CENTER,
        )
        set_text(
            ph[role_idx],
            ressource,
            size=11,
            colour=theme.GREY_DARK,
            align=PP_ALIGN.CENTER,
        )
    _drop_ph(slide, 12, 28, 29)


def fill_bloc(slide, s, layout):
    ph = _ph(slide)
    set_bullets(ph[10], s.body.bullets, quote=s.quote)


def fill_double(slide, s, layout):
    ph = _ph(slide)
    cols = s.columns
    if len(cols) != 2:
        raise SystemExit(f"{s.path.name}: 2 blocs attendus, {len(cols)} lus.")
    # Filet de separation entre les deux blocs. La disposition « Deux
    # colonnes evenements » du gabarit en pose un ; « Double bloc de texte »
    # non, et deux colonnes courtes flottaient alors au milieu d'une zone de
    # 4,6 pouces sans rien pour les tenir. Le meme filet, a la meme place,
    # rend les deux dispositions solidaires -- et c'est la « meme ligne
    # graphique pour l'ensemble de la presentation » que demande la
    # directive.
    separator(slide, x=6.67, top=2.10, bottom=6.42)
    set_bullets(ph[10], cols[0].bullets, heading=cols[0].name, scale=theme.SCALE_COLUMN)
    set_bullets(ph[12], cols[1].bullets, heading=cols[1].name, scale=theme.SCALE_COLUMN)
    if s.quote:
        textbox(
            slide,
            theme.QUOTE_BAND,
            f"« {s.quote} »",
            size=theme.QUOTE_SIZE,
            colour=theme.QUOTE_COLOUR,
            italic=True,
            align=PP_ALIGN.CENTER,
        )


def _two_columns_with_headers(slide, s, scale):
    ph = _ph(slide)
    cols = s.columns
    if len(cols) != 2:
        raise SystemExit(f"{s.path.name}: 2 blocs attendus, {len(cols)} lus.")
    for head_idx, body_idx, col in ((11, 13, cols[0]), (12, 14, cols[1])):
        set_text(
            ph[head_idx],
            col.name,
            size=theme.HEADING_SIZE,
            colour=theme.HEADING_COLOUR,
            bold=True,
        )
        set_bullets(ph[body_idx], col.bullets, scale=scale)


def fill_liste_photo(slide, s, layout):
    """Deux colonnes de puces, et un bandeau image pleine largeur en bas
    (la disposition le pose a 0 / 5.58 sur 13.33 x 1.92)."""
    _two_columns_with_headers(slide, s, theme.SCALE_COLUMN)
    ph = _ph(slide)
    box = ph[10]
    band = theme.Box(
        Emu(box.left).inches,
        Emu(box.top).inches,
        Emu(box.width).inches,
        Emu(box.height).inches,
    )
    fit_picture(slide, band, _figure_path(s))
    _drop_ph(slide, 10)
    if s.caption:
        textbox(
            slide,
            theme.Box(0.92, 5.20, 11.50, 0.30),
            s.caption,
            size=theme.CAPTION_SIZE,
            colour=theme.CAPTION_COLOUR,
            italic=True,
        )


def fill_liste_armes(slide, s, layout):
    """Deux colonnes encadrant les armes de l'Ecole, deja dans la
    disposition. Reserve a la planche d'orientation : c'est la seule ou
    l'embleme ajoute du sens plutot que de la decoration."""
    _two_columns_with_headers(slide, s, theme.SCALE_COLUMN)


def fill_figure(slide, s, layout):
    """Disposition « Slide vide » : un titre, et une figure qui occupe
    exactement la zone que le gabarit reserve au corps de texte. Les
    figures sont produites aux dimensions de cette zone, donc un corps de
    14 points dans la figure se projette a 14 points."""
    box = theme.FIGURE_WITH_CAPTION if s.caption else theme.FIGURE_FULL
    fit_picture(slide, box, _figure_path(s), anchor="top")
    if s.caption:
        textbox(
            slide,
            theme.CAPTION,
            s.caption,
            size=theme.CAPTION_SIZE,
            colour=theme.CAPTION_COLOUR,
            italic=True,
        )


def fill_tableau(slide, s, layout):
    """Un vrai tableau PowerPoint, pas une image de tableau : le jury peut
    le lire a l'ecran pendant les questions. La premiere puce donne
    l'en-tete, les suivantes les lignes ; les cellules sont separees par
    ` | ` dans le markdown."""
    rows = [b.cells for b in s.body.bullets]
    if len(rows) < 2:
        raise SystemExit(f"{s.path.name}: en-tete + au moins une ligne attendus.")
    ncol = len(rows[0])
    if any(len(r) != ncol for r in rows):
        raise SystemExit(
            f"{s.path.name}: lignes de largeurs inegales ({[len(r) for r in rows]})."
        )
    ph = _ph(slide)
    box = ph[10]
    shape = slide.shapes.add_table(
        len(rows), ncol, box.left, box.top, box.width, box.height
    )
    _drop_ph(slide, 10)
    table = shape.table
    for c, head in enumerate(rows[0]):
        cell = table.cell(0, c)
        p = _clear(cell.text_frame)
        _no_bullet(p)
        _write(p, head, size=14, colour=theme.WHITE, bold=True)
        cell.fill.solid()
        cell.fill.fore_color.rgb = theme.rgb(theme.NAVY)
    for r, row in enumerate(rows[1:], start=1):
        for c, val in enumerate(row):
            cell = table.cell(r, c)
            p = _clear(cell.text_frame)
            _no_bullet(p)
            _write(
                p,
                val,
                size=12,
                colour=theme.NAVY if c == 0 else theme.GREY_DARK,
                bold=(c == 0),
            )
            cell.fill.solid()
            cell.fill.fore_color.rgb = theme.rgb(theme.WHITE if r % 2 else theme.PALE)


def fill_timeline(slide, s, layout):
    """Frise a cinq entrees : « date | libelle » par puce."""
    ph = _ph(slide)
    slots = ((18, 19, 10), (26, 27, 14), (20, 21, 11), (28, 29, 15), (22, 23, 12))
    entries = s.body.bullets
    if len(entries) != 5:
        raise SystemExit(f"{s.path.name}: 5 entrees attendues, {len(entries)} lues.")
    for (date_idx, text_idx, pic_idx), bullet in zip(slots, entries):
        date, label = (list(bullet.cells) + [""])[:2]
        set_text(ph[date_idx], date, size=12, colour=theme.GOLD, bold=True)
        set_text(ph[text_idx], label, size=12, colour=theme.GREY_DARK)
        _drop_ph(slide, pic_idx)


def _footers(slide, layout, s, total):
    """Numerotation (x/x) et rappel de position, en ZONES DE TEXTE.

    On n'utilise pas les emplacements `dt` et `sldNum` du gabarit, bien
    qu'ils existent et soient exactement aux bonnes coordonnees. Raison
    mesuree : ces deux types d'emplacement portent un CHAMP automatique, et
    a l'export le moteur de rendu ajoute la valeur du champ A COTE du texte
    qu'on y ecrit -- la planche 3 affichait « 63/12 » (index reel 6, puis
    notre « 3/12 ») et « 05/08/2025I · Trois etonnements ». Le XML produit
    etait pourtant propre : le doublon vient du rendu, pas du fichier. Une
    zone de texte ordinaire, posee aux coordonnees relevees dans la
    disposition, donne le meme resultat visuel sans ce risque.

    La numerotation compte l'expose que le jury voit (1..N), les annexes
    portant A1, A2... : elles suivent la conclusion et ne font pas partie
    de la douzaine de planches utiles.
    """
    num_box = _layout_box(layout, theme.PH_SLIDE_NUMBER)
    if num_box is not None:
        shape = textbox(
            slide,
            num_box,
            s.label if s.is_annexe else f"{s.label}/{total}",
            size=theme.BREADCRUMB_SIZE,
            colour=theme.GOLD,
            align=PP_ALIGN.RIGHT,
        )
        shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    if not s.part:
        return
    # Elargie : la zone date du gabarit fait 3 pouces, ou « II · Un modele
    # qui oblige a chercher » passait a la ligne et debordait sous le bord
    # de la planche.
    crumb_box = _layout_box(layout, theme.PH_DATE, widen=2.2)
    if crumb_box is not None:
        shape = textbox(
            slide,
            crumb_box,
            s.part,
            size=theme.BREADCRUMB_SIZE,
            colour=theme.BREADCRUMB_COLOUR,
        )
        shape.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE


def fill_deux_colonnes(slide, s, layout):
    """Deux colonnes d'evenements : un intertitre par colonne, puis des
    entrees « ligne principale | precision » precedees d'un pictogramme.

    Les emplacements image et texte sont apparies par ligne, releves par
    coordonnees dans la disposition.
    """
    ph = _ph(slide)
    heads = (10, 26)
    rows = (
        ((56, 18), (57, 44), (58, 45), (59, 46)),
        ((60, 47), (61, 48), (62, 49), (63, 50)),
    )
    cols = s.columns
    if len(cols) != 2:
        raise SystemExit(f"{s.path.name}: 2 blocs attendus, {len(cols)} lus.")
    used = set()
    for c, (head_idx, row_set, col) in enumerate(zip(heads, rows, cols)):
        set_text(
            ph[head_idx],
            col.name,
            size=theme.HEADING_SIZE,
            colour=theme.HEADING_COLOUR,
            bold=True,
        )
        used.add(head_idx)
        # La disposition offre quatre rangees a hauteur fixe. Avec deux
        # entrees, on prend celles du milieu : remplir par le haut laisserait
        # la moitie basse de la planche vide.
        first = max(0, (len(row_set) - len(col.bullets)) // 2)
        for r, (pic_idx, body_idx) in enumerate(row_set):
            k = r - first
            if k < 0 or k >= len(col.bullets):
                continue
            main, aside = (list(col.bullets[k].cells) + [""])[:2]
            paras = _paragraphs(ph[body_idx].text_frame, 2 if aside else 1)
            ph[body_idx].text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            _no_bullet(paras[0])
            _indent(paras[0], 0, 0)
            _spacing(paras[0], 0)
            _write(paras[0], main, size=14, colour=theme.NAVY, bold=True)
            if aside:
                _no_bullet(paras[1])
                _indent(paras[1], 0, 0)
                _spacing(paras[1], 2, line_pct=92)
                _write(paras[1], aside, size=12, colour=theme.GREY_DARK)
            used.add(body_idx)
            pic = FIGS / f"puce_{c + 1}.png"
            if pic.exists():
                b = ph[pic_idx]
                fit_picture(
                    slide,
                    theme.Box(
                        Emu(b.left).inches,
                        Emu(b.top).inches,
                        Emu(b.width).inches,
                        Emu(b.height).inches,
                    ),
                    pic,
                )
                _drop_ph(slide, pic_idx)
                used.add(pic_idx)
    for idx in list(ph):
        if idx not in used and idx not in (
            theme.PH_TITLE,
            theme.PH_DATE,
            theme.PH_SLIDE_NUMBER,
        ):
            _drop_ph(slide, idx)


#: Dispositions dont le contenu est de la prose projetee, et auxquelles
#: s'applique donc le plafond de la directive ("moins de six lignes et moins
#: de six mots par ligne"). Une figure, un tableau, une frise ou un
#: organigramme ne sont pas de la prose : la directive les regit par une
#: autre phrase ("les images sont bienvenues si elles contiennent un
#: message") et les compter en lignes n'aurait aucun sens.
TEXT_LAYOUTS = frozenset(
    {
        "Bloc de texte",
        "Double bloc de texte",
        "Liste à puces + photo",
        "Liste à puces + armes",
        "1_Triptyque évênements ",
        "Deux colonnes évênements",
    }
)

#: Plafonds de densite, et pourquoi ceux-la.
#:
#: La directive dit deux choses dans la meme liste, et pas sur le meme ton.
#: L'une est une obligation : « l'espace disponible sur la planche doit etre
#: utilise de maniere optimale, elle ne doit etre ni vide, ni surchargee ».
#: L'autre est une habitude : « il est HABITUEL qu'une planche comporte
#: moins de six lignes et moins de six mots par ligne ». La contrainte qui
#: lie est donc la premiere. On la traduit en deux plafonds verifiables :
#: un bloc de texte ne depasse pas cinq lignes projetees (intertitre
#: compris), une planche a bloc unique n'en depasse pas six -- et la limite
#: de mots par ligne, elle, est tenue strictement, parce que c'est elle qui
#: empeche une planche de devenir une page de prose.
MAX_LINES_SINGLE = 6
MAX_LINES_PER_BLOCK = 5
MAX_WORDS_PER_LINE = 6

#: Contrat de chaque disposition : (remplissage, champs obligatoires,
#: nombre de blocs nommes attendu ou None).
SPECS = {
    "2_Couverture": (fill_couverture, ("title", "auteur", "entite", "periode"), 0),
    "1_Sommaire 4 parties": (fill_sommaire, (), 0),
    "1_Triptyque évênements ": (fill_triptyque, ("title", "part"), 3),
    "Organigramme": (fill_organigramme, ("title", "part"), 1),
    "Bloc de texte": (fill_bloc, ("title",), 0),
    "Double bloc de texte": (fill_double, ("title",), 2),
    "Liste à puces + photo": (fill_liste_photo, ("title", "part"), 2),
    "Liste à puces + armes": (fill_liste_armes, ("title", "part"), 2),
    "Slide vide": (fill_figure, ("title",), 0),
    "Tableau": (fill_tableau, ("title",), 0),
    "Timeline 5 entrées": (fill_timeline, ("title",), 0),
    "Deux colonnes évênements": (fill_deux_colonnes, ("title", "part"), 2),
}


def validate(all_slides):
    """Verifie le contrat markdown <-> disposition, dans les deux sens.

    La faiblesse la plus couteuse du pipeline dont ce dossier s'inspire
    etait que son `check` demandait seulement « le PNG existe-t-il ? », ce
    qui est exactement la mauvaise question. Ici on verifie les champs
    obligatoires, le nombre de blocs, la profondeur de puces, le plafond de
    lignes de la directive, et l'existence de chaque figure declaree.
    """
    problems = []
    for s in all_slides:
        if s.layout not in SPECS:
            problems.append(
                f"{s.path.name}: disposition non geree "
                f"« {s.layout} ». Connues : {sorted(SPECS)}"
            )
            continue
        _, required, ncols = SPECS[s.layout]
        for key in required:
            if not s.meta.get(key):
                problems.append(
                    f"{s.path.name}: champ `{key}:` manquant "
                    f"(exige par « {s.layout} »)."
                )
        if ncols is not None and len(s.columns) != ncols:
            problems.append(
                f"{s.path.name}: « {s.layout} » attend {ncols} "
                f"bloc(s) `##`, le fichier en declare "
                f"{len(s.columns)}."
            )
        if s.depth > theme.MAX_LEVEL:
            problems.append(
                f"{s.path.name}: profondeur de puces {s.depth} > {theme.MAX_LEVEL}."
            )
        if s.figure and not (FIGS / f"{s.figure}.png").exists():
            problems.append(
                f"{s.path.name}: figure `{s.figure}` non "
                f"produite ({FIGS}). Lancez `render.py figures`."
            )
        if s.image and not (ROOT / s.image).resolve().exists():
            problems.append(f"{s.path.name}: image absente -- {s.image}")
        if not s.is_annexe and s.layout in TEXT_LAYOUTS:
            if s.columns:
                for col in s.columns:
                    n = len(col.bullets) + 1
                    if n > MAX_LINES_PER_BLOCK:
                        problems.append(
                            f"{s.path.name}: bloc « {col.name} » a {n} "
                            f"lignes, plafond {MAX_LINES_PER_BLOCK}."
                        )
            elif s.line_count > MAX_LINES_SINGLE:
                problems.append(
                    f"{s.path.name}: {s.line_count} lignes projetees, "
                    f"plafond {MAX_LINES_SINGLE} pour un bloc unique."
                )
        # Le plafond de mots ne vaut que pour l'expose. Une annexe n'est
        # projetee que si le jury pose la question : c'est une piece de
        # reference qu'on lit, pas une idee maitresse qu'on saisit d'un coup
        # d'oeil, et une cellule de tableau y a le droit d'etre complete.
        if not s.is_annexe:
            for sec in s.sections:
                for b in sec.bullets:
                    for cell in b.cells:
                        words = len(cell.split())
                        if words > MAX_WORDS_PER_LINE:
                            problems.append(
                                f"{s.path.name}: {words} mots sur « "
                                f"{cell[:44]} » (plafond "
                                f"{MAX_WORDS_PER_LINE})."
                            )
    return problems


def build(strict=True):
    prs = Presentation(str(BASE))
    prs.core_properties.title = "Soutenance de formation humaine X2025"
    prs.core_properties.subject = "Campus Saint-Antoine, Apprentis d'Auteuil"
    prs.core_properties.author = "Allan Chastel TAMO KENGNE"
    prs.core_properties.last_modified_by = "Allan Chastel TAMO KENGNE"
    _drop_content_slides(prs)
    all_slides = slidesmod.load()

    problems = validate(all_slides)
    if problems:
        head = "\n".join("  - " + p for p in problems)
        if strict:
            raise SystemExit("Le markdown ne respecte pas son contrat :\n" + head)
        print("AVERTISSEMENTS :\n" + head)

    total = sum(1 for s in all_slides if not s.is_annexe)
    for s in all_slides:
        layout = _layout(prs, s.layout)
        page = prs.slides.add_slide(layout)
        if page.shapes.title is not None and s.title:
            page.shapes.title.text = s.title
        SPECS[s.layout][0](page, s, layout)

        _footers(page, layout, s, total)
        if s.notes:
            page.notes_slide.notes_text_frame.text = s.notes

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUT))

    _budget(all_slides, total)
    return OUT


#: Debit de lecture a voix haute retenu pour l'estimation. 140 mots par
#: minute est un debit d'exposé pose, avec des respirations -- pas un debit
#: de lecture rapide, qui serait de l'ordre de 180 et donnerait une
#: estimation faussement rassurante.
WORDS_PER_MINUTE = 140
TALK_MINUTES = 10


def _budget(all_slides, total):
    """Un budget de temps par planche, imprime a chaque assemblage.

    La directive X2025 plafonne l'expose a dix minutes et precise que « passee
    la 11e minute, le jury est libre d'interrompre ». Le seul moyen de
    tenir ce plafond est de savoir, avant la premiere repetition, quelle
    planche est trop longue. Les annexes sont comptees a part : elles ne
    sont projetees que si une question les appelle.
    """
    talk = [s for s in all_slides if not s.is_annexe]
    words = sum(len(s.notes.split()) for s in talk)
    minutes = words / WORDS_PER_MINUTE
    print(f"[deck] {OUT}")
    print(
        f"[deck] {total} planches d'expose + "
        f"{len(all_slides) - total} annexes (+ {KEPT} planches "
        f"d'instructions du gabarit, masquees)"
    )
    print(
        f"[deck] budget de parole ({WORDS_PER_MINUTE} mots/min, "
        f"didascalies comprises) :"
    )
    for s in talk:
        secs = len(s.notes.split()) / WORDS_PER_MINUTE * 60
        bar = "#" * max(1, round(secs / 6))
        print(f"       {s.label:>2}  {secs:4.0f}s  {bar:<20} {s.path.stem}")
    verdict = "dans le budget" if minutes <= TALK_MINUTES else "AU-DESSUS"
    print(
        f"[deck] total expose : {words} mots, ~{minutes:.1f} min "
        f"({verdict} de {TALK_MINUTES} min)."
    )
    if minutes > TALK_MINUTES:
        print(
            f"       Une partie des notes est de la didascalie, non "
            f"prononcee : chronometrez avant de couper."
        )


if __name__ == "__main__":
    build()
