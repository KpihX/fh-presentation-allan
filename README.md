# fh-presentation-allan

Support de soutenance de la période de formation humaine X2025 d'Allan Tamo,
construit sur le template officiel de l'École polytechnique.

## Livrables

- `build/Presentation_FH_X2025_Allan_TAMO.pptx`
- `build/Presentation_FH_X2025_Allan_TAMO.pdf`
- `build/preview/` : planches PNG et feuilles de contact

## Construction

```bash
uv sync
make check
make build
```

Le contenu projeté et les notes orateur vivent dans `slides/`. Les figures
sont générées par `scripts/figures/allan.py`. Les documents, photographies et
le clone de référence restent dans `refs/`.

## Format

- 10 planches utiles pour 10 minutes, avec une marge de respiration ;
- 4 annexes après la conclusion ;
- conclusion maintenue à l'écran pendant les questions ;
- aucune planche « Merci » ou « Questions » ;
- pagination `x/10`, puis `A1` à `A4`.
