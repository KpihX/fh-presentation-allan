"""Point d'entree unique.

    python render.py            tout : figures puis assemblage
    python render.py figures    seulement les PNG
    python render.py figures badges       un module
    python render.py deck       seulement l'assemblage du .pptx
    python render.py preview    rendu PNG de chaque planche + contacts
    python render.py check      verifie le contrat sans rien produire
    python render.py all        figures + deck + preview

`check` est le garde-fou important : il croise chaque planche markdown avec
la disposition du gabarit qu'elle declare (champs obligatoires, nombre de
blocs, profondeur de puces, plafond de six lignes de la directive, existence
des figures). Il repond donc a la vraie question -- « ce fichier peut-il
etre rendu correctement ? » -- et pas seulement « le PNG existe-t-il ? ».
"""

from __future__ import annotations

import importlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / "figures")]

FIGURE_MODULES = ("allan",)


def figures(which=()):
    names = which or FIGURE_MODULES
    for name in names:
        if name not in FIGURE_MODULES:
            raise SystemExit(f"module de figures inconnu : {name!r} "
                             f"-- choisir parmi {FIGURE_MODULES}")
        mod = importlib.import_module(f"figures.{name}")
        for build in mod.ALL:
            build()


def check():
    import deck
    import slides as slidesmod

    all_slides = slidesmod.load()
    problems = deck.validate(all_slides)
    talk = [s for s in all_slides if not s.is_annexe]
    print(f"[check] {len(talk)} planches d'expose, "
          f"{len(all_slides) - len(talk)} annexes")
    for s in all_slides:
        flag = "  " if not any(s.path.name in p for p in problems) else "!!"
        print(f"  {flag} {s.label:>3}  {s.layout:<26} "
              f"{s.line_count} ligne(s)  {s.path.name}")
    if problems:
        print("\n[check] problemes :")
        for p in problems:
            print("  - " + p)
        return 1
    print("[check] contrat respecte.")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else "all"
    rest = argv[1:]
    if cmd == "check":
        raise SystemExit(check())
    if cmd in ("figures", "all", "deck"):
        if cmd != "deck":
            figures(tuple(rest) if cmd == "figures" else ())
    if cmd in ("deck", "all"):
        import deck
        deck.build()
    if cmd in ("preview", "all"):
        import preview
        preview.main()
    if cmd not in ("figures", "deck", "all", "preview"):
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
