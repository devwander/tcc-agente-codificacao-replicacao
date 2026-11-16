"""Gera as figuras do capítulo de metodologia com PIL (sem matplotlib).

Canvas de 2600 px de largura, inserido a 16 cm (~413 dpi): fonte de 40 px ~ 7 pt.
"""
import math
import sys
from datetime import date
from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

INK = (30, 30, 30)
MUTED = (80, 80, 80)
LINE = (60, 60, 60)
F_R1 = (226, 226, 226)
F_R2 = (200, 214, 229)
F_P = (140, 170, 204)
F_PI = (245, 222, 179)
F_W = (236, 236, 236)
F_BOX = (244, 246, 249)
F_HEAD = (214, 224, 236)


def font(sz, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, sz)


def wrap(d, text, f, maxw):
    lines = []
    for para in text.split("\n"):
        words, cur = para.split(), ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) <= maxw:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_center(d, b, text, f, fill=INK, spacing=1.22, pad=24):
    x0, y0, x1, y1 = b
    lines = wrap(d, text, f, x1 - x0 - 2 * pad)
    lh = int(f.size * spacing)
    y = y0 + (y1 - y0 - lh * len(lines)) / 2
    for ln in lines:
        w = d.textlength(ln, font=f)
        d.text((x0 + (x1 - x0 - w) / 2, y), ln, font=f, fill=fill)
        y += lh
    return lh * len(lines)


def box(d, b, fill=F_BOX, outline=LINE, width=4, r=16):
    d.rounded_rectangle(b, radius=r, fill=fill, outline=outline, width=width)


def arrow(d, p0, p1, width=5, head=24, fill=LINE):
    d.line([p0, p1], fill=fill, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    pts = [p1] + [(p1[0] + head * math.cos(ang + s * math.radians(150)),
                   p1[1] + head * math.sin(ang + s * math.radians(150))) for s in (1, -1)]
    d.polygon(pts, fill=fill)


def tag(d, x1, y0, label, fill):
    f = font(40, True)
    w = d.textlength(label, font=f) + 40
    b = (x1 - w - 14, y0 - 30, x1 - 14, y0 + 30)
    d.rounded_rectangle(b, radius=12, fill=fill, outline=LINE, width=3)
    text_center(d, b, label, f, pad=0)


# ---------------------------------------------------------------- Figura 4.1
def fig_timeline():
    W, H = 2600, 1700
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    x0, x1 = 640, 2560
    d0, d1 = date(2026, 7, 29), date(2026, 11, 30)
    span = (d1 - d0).days

    def X(dt):
        return x0 + (x1 - x0) * (dt - d0).days / span

    f_lab = font(46, True)
    f_txt = font(42)
    f_small = font(40)

    ya = 110
    d.line([(x0, ya), (x1, ya)], fill=LINE, width=4)
    for m, lab in [(8, "ago."), (9, "set."), (10, "out."), (11, "nov.")]:
        xm = X(date(2026, m, 1))
        d.line([(xm, ya - 18), (xm, ya + 18)], fill=LINE, width=4)
        d.text((xm + 10, ya - 70), lab, font=f_small, fill=MUTED)

    def band(a, b, y, h, fill, text, f=f_txt):
        bb = (X(a), y, X(b), y + h)
        box(d, bb, fill=fill, r=12)
        if text:
            text_center(d, bb, text, f, pad=14)

    rows = [("Regimes", 170, 190), ("Paralelismo", 400, 110), ("Retrabalho", 550, 110), ("Percepção", 700, 110)]
    for lab, y, h in rows:
        d.text((30, y + h / 2 - 26), lab, font=f_lab, fill=INK)

    band(date(2026, 7, 29), date(2026, 8, 31), 170, 190, F_R1, "R1: 29/07 a 31/08\nsessões multitarefa")
    band(date(2026, 9, 1), date(2026, 10, 31), 170, 190, F_R2, "R2: 01/09 a 31/10\numa issue por sessão")
    band(date(2026, 10, 23), date(2026, 10, 31), 400, 110, F_PI, "")
    d.text((X(date(2026, 10, 31)) + 24, 428), "sessões em worktrees", font=f_txt, fill=INK)
    band(date(2026, 7, 29), date(2026, 11, 14), 550, 110, F_W, "janela de 14 dias após cada merge, até 14/11")
    band(date(2026, 11, 2), date(2026, 11, 14), 700, 110, F_P, "")
    d.text((X(date(2026, 7, 29)) + 10, 728), "instrumento retrospectivo por módulo, após o corte", font=f_txt, fill=INK)
    xc = X(date(2026, 10, 31))
    d.line([(xc, 150), (xc, 840)], fill=(170, 40, 40), width=5)
    d.text((xc + 12, 860 - 10), "corte: 31/10", font=f_lab, fill=(170, 40, 40))

    ty = 1000
    d.text((30, ty), "Dados disponíveis", font=f_lab, fill=INK)
    cols = [(x0, X(date(2026, 8, 31))), (X(date(2026, 9, 1)), X(date(2026, 10, 31)))]
    items = [
        ("Esforço e\nprodutividade", ["por sessão e por módulo", "por sessão, tarefa e módulo"]),
        ("Qualidade\nobjetiva", ["retrabalho por linha\ne testes reconstruídos", "retrabalho por linha\ne testes reconstruídos"]),
        ("Percepção", ["falas nas sessões;\navaliação retrospectiva", "falas nas sessões;\navaliação retrospectiva"]),
    ]
    y = ty + 80
    rh = 170
    for lab, vals in items:
        d.line([(30, y), (x1, y)], fill=(190, 190, 190), width=3)
        lines = lab.split("\n")
        ly = y + (rh - 50 * len(lines)) / 2
        for ln in lines:
            d.text((30, ly), ln, font=f_txt, fill=INK)
            ly += 50
        for (ca, cb), v in zip(cols, vals):
            text_center(d, (ca, y, cb, y + rh), v, f_small, pad=8)
        y += rh
    d.line([(30, y), (x1, y)], fill=(190, 190, 190), width=3)
    im = im.crop((0, 0, W, y + 20))
    im.save(f"{OUT}/fig41_linha_tempo.png", dpi=(300, 300))


# ---------------------------------------------------------------- Figura 4.2
def fig_arquitetura():
    W, H = 2600, 2000
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f_h = font(48, True)
    f_t = font(42)

    cx = [(20, 900), (1010, 1690), (1800, 2580)]
    for (a, b), lab in zip(cx, ["Fontes", "Coleta e armazenamento", "Saídas"]):
        d.text((a, 20), lab, font=f_h, fill=INK)

    src = [
        ("Transcritos das sessões do Claude Code", "O"),
        ("ccusage: tokens e custo equivalente", "O"),
        ("Git: commits, escopos de módulo, branches e merges", "O"),
        ("Cópia dos transcritos com resumo SHA-256 (até 31/10)", "O"),
        ("Instrumento retrospectivo de percepção por módulo", "D"),
    ]
    y, ys, bh = 120, [], 230
    for txt, nat in src:
        b = (cx[0][0], y, cx[0][1], y + bh)
        box(d, b)
        text_center(d, (b[0], b[1] + 20, b[2], b[3]), txt, f_t)
        tag(d, b[2], y, nat, F_P if nat == "O" else F_PI)
        ys.append(y + bh / 2)
        y += bh + 60
    bottom = y - 60

    bus = 955
    d.line([(bus, ys[0]), (bus, ys[-1])], fill=LINE, width=5)
    for yy in ys:
        d.line([(cx[0][1], yy), (bus, yy)], fill=LINE, width=5)
    colb = (cx[1][0], 360, cx[1][1], 720)
    box(d, colb, fill=F_HEAD)
    text_center(d, colb, "Coletores e sincronização incremental; vínculo entre sessão, tarefa e commit", f_t)
    arrow(d, (bus, 540), (cx[1][0], 540))
    dbb = (cx[1][0], 900, cx[1][1], 1260)
    box(d, dbb, fill=F_HEAD)
    text_center(d, dbb, "PostgreSQL e arquivo dos transcritos brutos com resumo SHA-256", f_t)
    arrow(d, ((colb[0] + colb[2]) / 2, colb[3]), ((colb[0] + colb[2]) / 2, dbb[1]))

    outs = [
        ("Métricas rotuladas pela natureza: O, Der, D e I (falas codificadas, validadas por kappa)", 120, 500),
        ("Exportação congelada e tabelas por sessão, tarefa e módulo", 600, 900),
        ("Métricas por módulo calculadas só após o instrumento congelado", 1000, 1300),
    ]
    bus2 = 1745
    d.line([(cx[1][1], 1080), (bus2, 1080)], fill=LINE, width=5)
    d.line([(bus2, 310), (bus2, 1150)], fill=LINE, width=5)
    for txt, a, b in outs:
        bb = (cx[2][0], a, cx[2][1], b)
        box(d, bb)
        text_center(d, bb, txt, f_t)
        arrow(d, (bus2, (a + b) / 2), (cx[2][0], (a + b) / 2))
    leg = "O = observado; Der = derivado; D = declarado; I = inferido."
    d.text((20, max(bottom, 1300) + 40), leg, font=font(40), fill=MUTED)
    im = im.crop((0, 0, W, max(bottom, 1300) + 110))
    im.save(f"{OUT}/fig43_arquitetura.png", dpi=(300, 300))


# ---------------------------------------------------------------- Figura 4.2 (níveis)
def fig_niveis():
    W, H = 2600, 1560
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f_h = font(46, True)
    f_t = font(40)
    f_s = font(38)
    # nível 1: módulos
    d.text((20, 20), "Módulo", font=f_h, fill=INK)
    d.text((20, 80), "todo o recorte (R1 e R2)", font=f_s, fill=MUTED)
    mods = ["Pacientes", "Agenda", "Estratégico", "...", "Transversais"]
    mx, mw, gap = 620, 340, 50
    for i, m in enumerate(mods):
        b = (mx + i * (mw + gap), 30, mx + i * (mw + gap) + mw, 170)
        box(d, b, fill=F_HEAD if m != "..." else "white", outline=LINE if m != "..." else "white")
        text_center(d, b, m, f_t)
    # nível 2: tarefas
    d.text((20, 330), "Tarefa", font=f_h, fill=INK)
    d.text((20, 390), "issue + merge request (R2)", font=f_s, fill=MUTED)
    tasks = [("#296", 620), ("#297", 1010), ("#301", 1400), ("#229 ... #287", 1790)]
    for lab, x in tasks:
        b = (x, 320, x + 340, 440)
        box(d, b)
        text_center(d, b, lab, f_t)
    for x in (620, 1010, 1400):
        arrow(d, (x + 170, 320), (mx + 2 * (mw + gap) + mw / 2 - 120 + (x - 1010) / 4, 170), width=4, head=18)
    arrow(d, (1960, 320), (mx + 4 * (mw + gap) + 100, 170), width=4, head=18)
    # nível 3: sessões
    d.text((20, 650), "Sessão", font=f_h, fill=INK)
    d.text((20, 710), "unidade de registro", font=f_s, fill=MUTED)
    sess = [("tarefa única", 620, F_R2, [620]), ("tarefa única", 1010, F_R2, [1010]),
            ("tarefa única (2 sessões)", 1400, F_R2, [1400]), ("tarefa agrupada", 1790, F_PI, [1790]),
            ("integração", 2180, F_W, [1790, 1400])]
    for lab, x, fill, targets in sess:
        b = (x, 620, x + 340, 760)
        box(d, b, fill=fill)
        text_center(d, b, lab, f_s)
        for tx in targets:
            arrow(d, (x + 170, 620), (tx + 170, 440), width=4, head=18)
    b = (2180, 320, 2520, 440)
    d.text((2190, 350), "outra: sem issue", font=f_s, fill=MUTED)
    # regras
    rules = [
        "Tarefa única: esforço somado por issue; entra nas análises por tarefa.",
        "Tarefa agrupada: grupo próprio (H4); esforço só no módulo, não repartido entre issues (repartição igual como sensibilidade).",
        "Integração e outras: entram no esforço por módulo e por regime, não nas análises por tarefa.",
        "Sessão → módulo: proporção de arquivos modificados por módulo; transversais quando dominam interface ou harness.",
    ]
    y = 860
    for r in rules:
        for ln in wrap(d, "• " + r, f_t, W - 60):
            d.text((30, y), ln, font=f_t, fill=INK)
            y += 52
        y += 16
    im = im.crop((0, 0, W, y + 20))
    im.save(f"{OUT}/fig42_niveis.png", dpi=(300, 300))


fig_timeline()
fig_arquitetura()
fig_niveis()
print("ok")
