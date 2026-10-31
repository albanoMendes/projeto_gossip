"""Draw the three seminar diagrams as PNGs using Pillow (no network/node needed).

Grupo 7 — Autores: Albano Mendes, Gustavo Cunha, Arthur Bastos.

Produces docs/img/{seq_push_pull,arch_asyncio,topo_panel}.png. These schematic
renders mirror the Mermaid sources in docs/img/*.mmd and are embedded in the
slides by scripts/make_slides.py.

Usage:
    .venv/bin/python scripts/make_diagrams.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

IMG_DIR = Path(__file__).resolve().parents[1] / "docs" / "img"

BG = (255, 255, 255)
INK = (20, 20, 20)
BOX = (235, 245, 255)
BOX2 = (235, 255, 240)
LINE = (60, 60, 60)
ACCENT = (40, 90, 160)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _text_center(draw, cx, cy, text, font, fill=INK):
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (r - l) / 2, cy - (b - t) / 2), text, font=font, fill=fill)


def _box(draw, xy, text, font, fill=BOX):
    draw.rounded_rectangle(xy, radius=10, fill=fill, outline=LINE, width=2)
    cx = (xy[0] + xy[2]) / 2
    cy = (xy[1] + xy[3]) / 2
    _text_center(draw, cx, cy, text, font)


def _arrow(draw, p1, p2, width=2, fill=LINE):
    draw.line([p1, p2], fill=fill, width=width)
    import math

    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    size = 10
    for da in (math.radians(160), math.radians(-160)):
        draw.line(
            [p2, (p2[0] + size * math.cos(ang + da), p2[1] + size * math.sin(ang + da))],
            fill=fill,
            width=width,
        )


# --- Diagram 1: push-pull sequence ------------------------------------------
def seq_push_pull() -> None:
    W, H = 900, 560
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f = _font(18)
    fb = _font(20)
    fs = _font(15)

    _text_center(d, W / 2, 24, "Troca push-pull (fanout = 2)", fb, ACCENT)
    lanes = {"A": 150, "B": 470, "C": 780}
    labels = {"A": "A (iniciador)", "B": "B (par 1)", "C": "C (par 2)"}
    top, bottom = 70, 520
    for k, x in lanes.items():
        _box(d, (x - 70, top, x + 70, top + 36), labels[k], fs)
        d.line([(x, top + 36), (x, bottom)], fill=(180, 180, 180), width=2)

    y = top + 90
    _text_center(d, W / 2, y - 18, "Timer ~300 ms: seleciona 2 pares distintos (B, C)", fs, ACCENT)

    # Exchange 1: A <-> B
    _arrow(d, (lanes["A"], y + 10), (lanes["B"], y + 10))
    _text_center(d, (lanes["A"] + lanes["B"]) / 2, y - 4, "GOSSIP {A, estado(A)}", fs)
    _text_center(d, lanes["B"], y + 42, "merge(estado A)", fs, ACCENT)
    _arrow(d, (lanes["B"], y + 70), (lanes["A"], y + 70))
    _text_center(d, (lanes["A"] + lanes["B"]) / 2, y + 56, "REPLY {B, estado(B)}", fs)
    _text_center(d, lanes["A"], y + 100, "merge(estado B)", fs, ACCENT)

    # Exchange 2: A <-> C
    y2 = y + 160
    _arrow(d, (lanes["A"], y2 + 10), (lanes["C"], y2 + 10))
    _text_center(d, (lanes["A"] + lanes["C"]) / 2, y2 - 4, "GOSSIP {A, estado(A)}", fs)
    _text_center(d, lanes["C"], y2 + 42, "merge(estado A)", fs, ACCENT)
    _arrow(d, (lanes["C"], y2 + 70), (lanes["A"], y2 + 70))
    _text_center(d, (lanes["A"] + lanes["C"]) / 2, y2 + 56, "REPLY {C, estado(C)}", fs)
    _text_center(d, lanes["A"], y2 + 100, "merge(estado C)", fs, ACCENT)

    _text_center(
        d, W / 2, bottom + 20,
        "Qualquer GOSSIP/REPLY pode ser descartado por perda; trocas futuras reparam.",
        fs, (120, 120, 120),
    )
    img.save(IMG_DIR / "seq_push_pull.png")
    print("wrote seq_push_pull.png")


# --- Diagram 2: asyncio architecture ----------------------------------------
def arch_asyncio() -> None:
    W, H = 900, 520
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    fb = _font(20)
    fs = _font(15)

    _text_center(d, W / 2, 24, "Concorrência: um event loop asyncio por nó", fb, ACCENT)
    d.rounded_rectangle((40, 60, 860, 300), radius=12, outline=LINE, width=2)
    _text_center(d, 230, 78, "Event loop asyncio (um por nó)", fs, ACCENT)

    boxes = [
        (70, 110, 300, 160, "corrotina: ciclo gossip\nawait sleep(0.3)"),
        (330, 110, 560, 160, "DatagramProtocol: gossip\n(porta de gossip)"),
        (590, 110, 830, 160, "DatagramProtocol: status\n(porta de status)"),
        (200, 210, 430, 260, "CLI: to_thread(input)"),
    ]
    centers = []
    for x1, y1, x2, y2, label in boxes:
        d.rounded_rectangle((x1, y1, x2, y2), radius=10, fill=BOX, outline=LINE, width=2)
        lines = label.split("\n")
        for i, ln in enumerate(lines):
            _text_center(d, (x1 + x2) / 2, (y1 + y2) / 2 - 8 + i * 16, ln, fs)
        centers.append(((x1 + x2) / 2, y2))

    store = (330, 380, 560, 440)
    d.rounded_rectangle(store, radius=10, fill=BOX2, outline=LINE, width=2)
    _text_center(d, 445, 402, "NoticeStore", fs)
    _text_center(d, 445, 420, "(instância única compartilhada)", fs)

    scx = 445
    for i, (cx, cy) in enumerate(centers):
        dashed = i == 2  # status is read-only
        if dashed:
            # dashed arrow
            steps = 14
            for s in range(0, steps, 2):
                xa = cx + (scx - cx) * s / steps
                ya = cy + (380 - cy) * s / steps
                xb = cx + (scx - cx) * (s + 1) / steps
                yb = cy + (380 - cy) * (s + 1) / steps
                d.line([(xa, ya), (xb, yb)], fill=LINE, width=2)
            _text_center(d, (cx + scx) / 2 + 60, (cy + 380) / 2, "somente leitura", _font(13), (120, 120, 120))
        else:
            _arrow(d, (cx, cy), (scx + (cx - scx) * 0.15, 380))
    img.save(IMG_DIR / "arch_asyncio.png")
    print("wrote arch_asyncio.png")


# --- Diagram 3: topology + panel --------------------------------------------
def topo_panel() -> None:
    import math

    W, H = 900, 520
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    fb = _font(20)
    fs = _font(16)

    _text_center(d, W / 2, 24, "Topologia de gossip (UDP) + painel observador", fb, ACCENT)

    ids = ["A", "B", "C", "D", "E", "F"]
    cx, cy, R = 330, 280, 170
    pos = {}
    for i, k in enumerate(ids):
        ang = -math.pi / 2 + i * (2 * math.pi / len(ids))
        pos[k] = (cx + R * math.cos(ang), cy + R * math.sin(ang))

    edges = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F"), ("F", "A"),
             ("A", "D"), ("B", "E")]
    for a, b in edges:
        d.line([pos[a], pos[b]], fill=(150, 150, 150), width=2)
    r = 26
    for k, (x, y) in pos.items():
        d.ellipse((x - r, y - r, x + r, y + r), fill=BOX, outline=LINE, width=2)
        _text_center(d, x, y, k, fs)

    # Panel on the right, dashed read-only links to a few nodes.
    panel = (700, 240, 860, 300)
    d.rounded_rectangle(panel, radius=10, fill=BOX2, outline=LINE, width=2)
    _text_center(d, 780, 270, "Painel observer", fs)
    for k in ("A", "C", "F"):
        px, py = pos[k]
        steps = 16
        for s in range(0, steps, 2):
            xa = 700 + (px - 700) * s / steps
            ya = 270 + (py - 270) * s / steps
            xb = 700 + (px - 700) * (s + 1) / steps
            yb = 270 + (py - 270) * (s + 1) / steps
            d.line([(xa, ya), (xb, yb)], fill=ACCENT, width=2)
    _text_center(d, 780, 316, "status read-only", _font(13), (120, 120, 120))
    img.save(IMG_DIR / "topo_panel.png")
    print("wrote topo_panel.png")


def main() -> None:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    seq_push_pull()
    arch_asyncio()
    topo_panel()


if __name__ == "__main__":
    main()
