"""Relecture du .pptx sans ouvrir PowerPoint.

Convertit le livrable en PDF puis en PNG, une image par planche, et monte
des planches de contact 3 x 2 pour juger le RYTHME de la presentation et pas
seulement une page isolee.

Avertissement a garder en tete : la conversion passe par LibreOffice, qui ne
dispose ni de Georgia ni de Century Gothic et leur substitue des polices
approchantes. Les longueurs de ligne et les retours a la ligne peuvent donc
differer legerement du rendu PowerPoint reel.

Piege verifie, et resolu : le substitut choisi par defaut n'avait pas les
glyphes « u circonflexe », « E grave capitale », « U circonflexe capitale »
ni « O circonflexe capitale », et les rendait sous la forme d'une lettre
suivie d'un accent detache -- « cout » s'affichait « cou^t ». Le pptx etait
pourtant correct : seul l'apercu mentait. Un fichier
`~/.config/fontconfig/fonts.conf` qui impose Liberation Serif et URW Gothic
comme substituts complets suffit a le corriger. Si vous voyez reapparaitre
des accents detaches, c'est cette configuration qui manque, pas le
document. La verification finale se fait
sur le poste de soutenance, avec le materiel de la salle -- ce que la
directive demande de toute facon ("il est fortement conseille de tester le
materiel en amont").
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
OUT = BUILD / "preview"


def _run(cmd, cwd=None):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"echec : {' '.join(map(str, cmd))}\n{res.stderr[-1500:]}")
    return res.stdout


def main(pptx: pathlib.Path | None = None, sheets=True):
    pptx = pptx or next(BUILD.glob("*.pptx"))
    if shutil.which("soffice") is None:
        raise SystemExit("`soffice` introuvable : impossible de rendre un "
                         "apercu. Ouvrez le .pptx directement.")
    OUT.mkdir(parents=True, exist_ok=True)
    # Les anciens PNG sont ecrases, pas supprimes : selon l'endroit ou le
    # depot est monte, la suppression peut etre refusee alors que la
    # reecriture passe. On signale simplement les restes eventuels d'un
    # rendu precedent plus long que celui-ci.
    before = {p.name for p in OUT.glob("planche-*.png")}
    _run(["soffice", "--headless", "--convert-to", "pdf", "--outdir",
          str(BUILD), str(pptx)])
    pdf = BUILD / (pptx.stem + ".pdf")
    _run(["pdftoppm", "-png", "-r", "110", str(pdf), str(OUT / "planche")])
    pages = sorted(OUT.glob("planche-*.png"))
    print(f"[preview] {len(pages)} planches -> {OUT}")
    orphans = before - {p.name for p in pages}
    if orphans:
        print(f"[preview] restes d'un rendu precedent, a ignorer : "
              f"{sorted(orphans)}")

    if sheets and pages:
        try:
            from PIL import Image
        except ImportError:
            return pages
        per, cols = 6, 3
        for start in range(0, len(pages), per):
            chunk = pages[start:start + per]
            ims = [Image.open(p) for p in chunk]
            w, h = ims[0].size
            rows = (len(chunk) + cols - 1) // cols
            sheet = Image.new("RGB", (w * cols, h * rows), "white")
            for i, im in enumerate(ims):
                sheet.paste(im, ((i % cols) * w, (i // cols) * h))
            name = OUT / f"contact_{start // per + 1}.png"
            sheet.save(name)
            print(f"[preview] {name.name}")
    return pages


if __name__ == "__main__":
    main()
