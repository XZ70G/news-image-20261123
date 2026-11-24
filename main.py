#!/usr/bin/env python3
"""Front page of THE WORLD TODAY for Monday 23 November 2026.

The program draws a one-page newspaper front page in pure Python
(standard library only) and writes a deterministic 1024x1024 PNG to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
No network access, no timestamps, no randomness: the same bytes
come out on every run.

Stories covered, all first reported on 23 November 2026:
  * Ukraine says its sea drones sank the Russian corvette Merkury
    off Libya, and struck the cargo ship Angara
  * the COP31 climate talks in Antalya end with no deal
  * Nvidia brings Jensen Huang back as chief executive
  * Israeli strikes in Gaza kill three people, including an
    UNRWA worker
  * the United States imposes new sanctions on Iran's shadow
    banking network
  * a national strike in Belgium grounds flights
Plus a ticker of the day's other news.
"""

import sys
import zlib
import struct
import os

W = 1024
H = 1024

CREAM = (247, 242, 228)
INK = (24, 24, 24)
NAVY = (16, 36, 72)
RED = (178, 36, 28)
GOLD = (198, 158, 38)
WHITE = (255, 255, 255)
GREY = (96, 96, 96)
LIGHT = (233, 227, 209)
SEA = (168, 205, 225)
SKY = (122, 178, 205)
GREEN = (34, 128, 74)
PANEL = (255, 255, 255)

# Tiny 3x5 capital-letter font. Each glyph is one 15-character
# string, five rows of three cells read left to right, top to
# bottom; '1' is a filled cell.
GLYPHS = {
    "A": "010101111101101",
    "B": "110101110101110",
    "C": "011100100100011",
    "D": "110101101101110",
    "E": "111100110100111",
    "F": "111100110100100",
    "G": "011100101101011",
    "H": "101101111101101",
    "I": "111010010010111",
    "J": "001001001101010",
    "K": "101101110101101",
    "L": "100100100100111",
    "M": "101111111101101",
    "N": "101111101101101",
    "O": "010101101101010",
    "P": "110101110100100",
    "Q": "010101101110011",
    "R": "110101110101101",
    "S": "011100010001110",
    "T": "111010010010010",
    "U": "101101101101111",
    "V": "101101101101010",
    "W": "101101111111101",
    "X": "101101010101101",
    "Y": "101101010010010",
    "Z": "111001010100111",
    "0": "111101101101111",
    "1": "010110010010111",
    "2": "110001010100111",
    "3": "110001010001110",
    "4": "101101111001001",
    "5": "111100110001110",
    "6": "011100110101010",
    "7": "111001010010010",
    "8": "010101010101010",
    "9": "010101011001110",
    ".": "000000000000010",
    ",": "000000000010100",
    ":": "000010000010000",
    ";": "000010000010100",
    "'": "010010000000000",
    "-": "000000111000000",
    "/": "001001010100100",
    "&": "010101010101101",
    "!": "010010010000010",
    "?": "110001010000010",
    "(": "001010010010001",
    ")": "100010010010100",
    "%": "101001010100101",
    "$": "010111010111010",
    "+": "000010111010000",
    "=": "000111000111000",
    "*": "000101010101000",
    '"': "101101000000000",
    " ": "000000000000000",
}

buf = bytearray(CREAM * (W * H))


def put(x, y, colour):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = colour[0]
        buf[i + 1] = colour[1]
        buf[i + 2] = colour[2]


def box(x, y, w, h, colour):
    for yy in range(y, y + h):
        if 0 <= yy < H:
            xa = max(x, 0)
            xb = min(x + w, W)
            if xb > xa:
                i = (yy * W + xa) * 3
                buf[i:i + (xb - xa) * 3] = colour * (xb - xa)


def disc(cx, cy, r, colour):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        for xx in range(cx - dx, cx + dx + 1):
            put(xx, cy + dy, colour)


def rule(x, y, w, colour, thick=2):
    box(x, y, w, thick, colour)


def text_width(s, scale):
    if not s:
        return 0
    return len(s) * 4 * scale - scale


def draw_text(x, y, s, scale, colour):
    s = s.upper()
    cx = x
    for ch in s:
        glyph = GLYPHS.get(ch, GLYPHS[" "])
        for r in range(5):
            for c in range(3):
                if glyph[r * 3 + c] == "1":
                    box(cx + c * scale, y + r * scale, scale, scale, colour)
        cx += 4 * scale
    return cx


def centred(y, s, scale, colour):
    draw_text((W - text_width(s, scale)) // 2, y, s, scale, colour)


def wrap(s, max_w, scale):
    lines = []
    for chunk in s.split("\n"):
        words = chunk.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
    return lines


def para(x, y, s, max_w, scale, colour, gap=6):
    step = 5 * scale + gap
    lines = wrap(s, max_w, scale)
    for i, line in enumerate(lines):
        draw_text(x, y + i * step, line, scale, colour)
    return y + len(lines) * step


def kicker(x, y, s, colour):
    rule(x, y + 2, 34, colour, 5)
    draw_text(x + 44, y, s, 3, colour)
    return y + 22


def png_bytes():
    raw = bytearray()
    for yy in range(H):
        raw.append(0)
        raw += buf[yy * W * 3:(yy + 1) * W * 3]
    data = zlib.compress(bytes(raw), 9)

    def chunk(kind, payload):
        out = struct.pack(">I", len(payload)) + kind + payload
        out += struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", data)
        + chunk(b"IEND", b"")
    )


def draw_ship_scene():
    box(36, 330, 624, 140, SKY)
    box(36, 470, 624, 50, SEA)
    box(120, 448, 420, 34, NAVY)
    box(540, 456, 80, 26, NAVY)
    box(220, 420, 160, 28, WHITE)
    for wx in (232, 268, 304, 340):
        box(wx, 430, 24, 10, NAVY)
    box(400, 404, 40, 44, RED)
    box(300, 396, 5, 24, INK)
    box(305, 396, 16, 8, RED)
    disc(560, 412, 6, INK)
    disc(606, 394, 6, INK)
    box(60, 490, 90, 4, WHITE)
    box(200, 502, 120, 4, WHITE)
    box(380, 490, 100, 4, WHITE)
    box(520, 506, 90, 4, WHITE)


def draw_globe():
    disc(836, 306, 32, SKY)
    box(818, 292, 18, 10, GREEN)
    box(836, 312, 22, 12, GREEN)
    for i in range(-26, 27):
        box(836 + i, 306 + i, 3, 3, RED)


def build():
    box(0, 0, W, 150, NAVY)
    centred(26, "THE WORLD TODAY", 9, WHITE)
    centred(96, "MONDAY 23 NOVEMBER 2026", 4, GOLD)
    rule(0, 146, W, GOLD, 4)

    # Lead story: Ukraine's sea drones off Libya.
    kicker(36, 178, "UKRAINE - WAR AT SEA", RED)
    para(36, 206, "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA", 624, 5, INK)
    para(36, 276, "ZELENSKYY SAYS SEA DRONES SANK THE CORVETTE "
         "MERKURY NEAR BENGHAZI", 624, 3, GREY)
    draw_ship_scene()
    para(36, 534, "SEVEN NAVAL DRONES STRUCK TWO RUSSIAN SHIPS, KYIV "
         "SAYS, TAKING THE WAR INTO THE MEDITERRANEAN. NATO MET AFTER "
         "RUSSIAN MISSILES CAME DOWN IN POLAND.", 624, 3, INK)

    box(668, 172, 2, 440, LIGHT)

    # Right column: COP31, then Nvidia.
    kicker(684, 178, "CLIMATE", NAVY)
    para(684, 206, "COP31 ENDS WITH NO DEAL", 304, 4, INK)
    draw_globe()
    para(684, 352, "ANTALYA TALKS COLLAPSE AS THE EU REJECTS A TEXT "
         "SILENT ON FOSSIL FUELS.", 304, 3, INK)
    rule(684, 436, 304, LIGHT, 2)
    kicker(684, 452, "TECH", GREEN)
    para(684, 480, "HUANG BACK AT NVIDIA", 304, 4, INK)
    para(684, 540, "HUANG IS BACK AS CEO AFTER TRUMP INTERVENED. "
         "SHARES JUMP ABOUT 30 PER CENT.", 304, 3, INK)

    rule(36, 616, 952, INK, 2)

    # Second row: Gaza, Iran, Belgium.
    box(350, 640, 2, 220, LIGHT)
    box(676, 640, 2, 220, LIGHT)
    kicker(36, 646, "GAZA", RED)
    para(36, 676, "THREE KILLED IN GAZA STRIKES", 300, 4, INK)
    para(36, 740, "ISRAELI STRIKES KILL AN UNRWA WORKER IN THE JABALIA "
         "CAMP. THREE PEOPLE DIED IN SEPARATE STRIKES ON MONDAY.",
         300, 3, INK)
    kicker(362, 646, "IRAN - SANCTIONS", NAVY)
    para(362, 676, "US HITS IRAN WITH NEW SANCTIONS", 300, 4, INK)
    para(362, 740, "THE TREASURY TARGETS MORE THAN TWO DOZEN EXCHANGE "
         "HOUSES AND FRONT FIRMS IN IRAN'S SHADOW BANKING NETWORK.",
         300, 3, INK)
    kicker(688, 646, "BELGIUM", GREEN)
    para(688, 676, "STRIKE GROUNDS BELGIAN FLIGHTS", 300, 4, INK)
    para(688, 740, "AIR TRAFFIC CONTROLLERS JOIN A NATIONAL STRIKE "
         "AGAINST AUSTERITY. NEARLY ALL FLIGHTS AT BRUSSELS AND "
         "CHARLEROI ARE CANCELLED.", 300, 3, INK)

    # Ticker of the day's other news.
    box(0, 880, W, 100, NAVY)
    draw_text(36, 894, "ALSO TODAY", 3, GOLD)
    para(36, 918, "INDONESIA FACTORY FIRE KILLS 24 - EU PROPOSES NEW "
         "SANCTIONS ON 60 RUSSIAN BANKS - MEXICO CAPTURES DRUG LORD "
         "CHAPO ISIDRO - RUSSIAN STRIKES KILL AT LEAST 15 IN KYIV "
         "REGION", 952, 3, WHITE, gap=4)

    centred(996, "DRAWN ENTIRELY IN CODE - THE WORLD TODAY - "
            "23 NOVEMBER 2026", 2, GREY)


def main():
    build()
    out = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "entry.png")
    data = png_bytes()
    with open(path, "wb") as fh:
        fh.write(data)
    sys.stdout.write("wrote %s (%d bytes)\n" % (path, len(data)))


if __name__ == "__main__":
    main()
