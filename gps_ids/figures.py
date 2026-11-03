from pathlib import Path

DPI = 1000
WIDTH_IN = 7.5
HEIGHT_IN = 4.3
FORMATS = ("pdf", "png")


def save(stem, fig=None, *, width=WIDTH_IN, height=HEIGHT_IN, dpi=DPI, formats=FORMATS):
    import matplotlib.pyplot as plt

    figure = plt.gcf() if fig is None else fig
    if width and height:
        figure.set_size_inches(width, height)
    stem = Path(stem)
    if stem.suffix:
        stem = stem.with_suffix("")
    if stem.parent != Path("."):
        stem.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for extension in formats:
        path = stem.with_suffix("." + extension)
        figure.savefig(path, dpi=dpi, bbox_inches="tight")
        written.append(path)
    return written


def save_and_close(stem, fig=None, **kwargs):
    import matplotlib.pyplot as plt

    figure = plt.gcf() if fig is None else fig
    written = save(stem, fig=figure, **kwargs)
    plt.close(figure)
    return written
