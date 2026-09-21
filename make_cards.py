#!/usr/bin/env python3
"""Afrimax-style title overlay + moral end card via PIL (1080x1920 canvases).

- title.png : transparent overlay, bold condensed gold title w/ black stroke
- moral.png : opaque end card rendered at 1188x2112 for a slow drift crop
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pathlib import Path

BASE = Path(__file__).parent
F = BASE / "fonts"
W, H = 1080, 1920


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(F / name), size)


def draw_tracked(draw, xy, text, fnt, fill, tracking=0, anchor_center=True):
    """Draw letter-spaced text; returns total width."""
    widths = [draw.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = xy[0] - total / 2 if anchor_center else xy[0]
    y = xy[1]
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w + tracking
    return total


def gold_gradient(size, top=(255, 224, 138), bottom=(196, 132, 26)):
    w, h = size
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        grad.putpixel((0, y), tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)))
    return grad.resize((w, h))


def text_gold_stroke(canvas, center_xy, text, fnt, stroke_w, shadow=True):
    """Gold-gradient-filled text with black stroke + soft shadow."""
    W_, H_ = canvas.size
    txt_layer = Image.new("L", (W_, H_), 0)
    d = ImageDraw.Draw(txt_layer)
    bbox = d.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    y_top = int(center_xy[1] - th / 2)
    pos = (center_xy[0] - tw / 2 - bbox[0], y_top - bbox[1])
    d.text(pos, text, font=fnt, fill=255)
    if shadow:
        sh = txt_layer.filter(ImageFilter.GaussianBlur(10))
        shadow_layer = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
        shadow_layer.paste(Image.new("RGBA", (W_, H_), (0, 0, 0, 190)), (8, 12), sh)
        canvas.alpha_composite(shadow_layer)
    # stroke = dilated text mask
    thick = txt_layer.filter(ImageFilter.MaxFilter(stroke_w * 2 + 1))
    stroke_layer = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    stroke_layer.paste(Image.new("RGBA", (W_, H_), (16, 9, 3, 255)), (0, 0), thick)
    # gold fill: gradient band across the text height, masked by text
    gold_band = gold_gradient((W_, th + 80)).convert("RGBA")
    gold_full = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    gold_full.paste(gold_band, (0, y_top - 40))
    fill_layer = Image.new("RGBA", (W_, H_), (0, 0, 0, 0))
    fill_layer.paste(gold_full, (0, 0), txt_layer)
    canvas.alpha_composite(stroke_layer)
    canvas.alpha_composite(fill_layer)


def make_title():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f_line1 = font("BebasNeue-Regular.ttf", 128)
    f_line2 = font("BebasNeue-Regular.ttf", 226)
    f_sub = font("ArchivoBlack-Regular.ttf", 44)

    text_gold_stroke(img, (W / 2, 600), "THE FISHERMAN'S", f_line1, 9)
    text_gold_stroke(img, (W / 2, 760), "GOLD", f_line2, 13)

    # divider + subtitle
    y = 940
    d.rectangle([W / 2 - 170, y + 26, W / 2 + 170, y + 30], fill=(232, 179, 75, 255))
    draw_tracked(d, (W / 2, y + 60), "AN AFRICAN MORAL STORY", f_sub,
                 (255, 243, 224, 255), tracking=10)
    img.save(BASE / "cards" / "title.png")
    print("title.png done")


def make_moral():
    # oversized canvas for slow drift crop (1188x2112 -> crop 1080x1920)
    w, h = 1188, 2112
    img = Image.new("RGBA", (w, h))
    # vertical gradient bg
    top, bottom = (26, 16, 8), (10, 6, 3)
    for y in range(h):
        t = y / (h - 1)
        row = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)) + (255,)
        ImageDraw.Draw(img).line([(0, y), (w, y)], fill=row)
    # radial warm glow behind heading
    glow = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w / 2 - 520, 780 - 260, w / 2 + 520, 780 + 260], fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    warm = Image.new("RGBA", (w, h), (196, 116, 34, 255))
    img = Image.composite(warm, img, glow.point(lambda p: p // 2))

    d = ImageDraw.Draw(img)
    f_head = font("BebasNeue-Regular.ttf", 96)
    f_moral = font("ArchivoBlack-Regular.ttf", 76)
    f_foot = font("ArchivoBlack-Regular.ttf", 34)

    draw_tracked(d, (w / 2, 640), "MORAL OF THE STORY", f_head, (232, 179, 75, 255), tracking=14)
    d.rectangle([w / 2 - 180, 800, w / 2 + 180, 805], fill=(232, 179, 75, 255))

    # wrapped moral text
    words = "Honesty planted today becomes tomorrow's harvest."
    lines, cur = [], ""
    for wd in words.split():
        trial = (cur + " " + wd).strip()
        if d.textlength(trial, font=f_moral) > w - 220:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    lines.append(cur)
    y = 900
    for ln in lines:
        tw = d.textlength(ln, font=f_moral)
        d.text(((w - tw) / 2, y), ln, font=f_moral, fill=(255, 246, 232, 255))
        y += 112

    # small fish icon substitute: gold dot trio divider
    for i, dx in enumerate((-60, 0, 60)):
        d.ellipse([w / 2 + dx - 7, 1500 - 7, w / 2 + dx + 7, 1500 + 7],
                  fill=(232, 179, 75, 255))
    draw_tracked(d, (w / 2, 1930), "SUBSCRIBE FOR MORE AFRICAN MORAL STORIES", f_foot,
                 (160, 139, 111, 255), tracking=6)
    img.convert("RGB").save(BASE / "cards" / "moral.png")
    print("moral.png done")


if __name__ == "__main__":
    (BASE / "cards").mkdir(exist_ok=True)
    make_title()
    make_moral()
