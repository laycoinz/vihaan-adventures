import os
import sys
import math
import random

import pygame

import generate_audio

pygame.mixer.pre_init(44100, -16, 2, 512)

TILE = 40
W = 960
H = 640
FPS = 60
GRID_H = H // TILE

GRAVITY = 0.9
MAX_FALL = 17.0

# --- Super Mario Bros. 1 (NES) physics -------------------------------------
# All values below are the exact SMB1 constants. Player_X_Speed is measured in
# subpixels/frame (16 subpixels = 1 SMB pixel); vertical speed is in SMB
# pixels/frame and the *MForce tables are gravity in 1/256 px/frame^2. Our
# world uses 40px tiles versus SMB's 16px, so world positions/velocities are
# converted with SMB_SCALE to keep the exact tile-relative behaviour.
SMB_SCALE = TILE / 16.0
X_MAX_WALK = 24.0                        # soft cap  (1.5 px/f)
X_MAX_RUN = 40.0                         # hard cap  (2.5 px/f)
FRICTION_DATA = (0xE4, 0x98, 0xD0)       # accel/256 subpx per frame^2
JUMP_SPEED = (-4, -4, -4, -5, -5, -2, -1)
JUMP_UP_GRAV = (0x20, 0x20, 0x1E, 0x28, 0x28, 0x0D, 0x04)
JUMP_DOWN_GRAV = (0x70, 0x70, 0x60, 0x90, 0x90, 0x0A, 0x09)
JUMP_SPEED_THRESH = (9, 16, 25, 28)
FALL_CAP = 4.5                           # SMB px/f
STOMP_BOUNCE = -4 * SMB_SCALE
BOSS_BOUNCE_X = 30.0                     # SMB subpx/f, knocked away from a boss
PARRY_WINDOW = 10                        # frames a jump press can parry a projectile
PARRY_FLIP_FRAMES = 26                   # backflip animation length after a parry
HARVEY_ATTACK_DELAY = 42                 # 0.7s at 60 fps
ESMEE_COOLDOWN = 348                     # 5.8s at 60 fps
GILBERT_BAT_INTERVAL = 420               # 7.0s at 60 fps
MECH_REGEN_INTERVAL = 900                # 15.0s at 60 fps
MECH_REGEN_AMOUNT = 20
PLAYER_START_HEARTS = 3
BAT_HOME_RANGE = 8 * TILE                # frost bats home within 8 tiles
ENEMY_SPEED = 1.2
START_LIVES = 5
RAMEN_SHOOT_COOLDOWN = 18
PAD_BTN_RECALL = 5
PW, PH = 26, 38
BIGW, BIGH = 30, 56

SOLID = set("#B?M=XRp")

_ASSETS = generate_audio.ASSETS

THEMES = {
    0: {
        "sky_top": (104, 190, 255), "sky_bot": (200, 236, 255),
        "hill": (92, 196, 120), "hill2": (66, 164, 100),
        "ground": (150, 96, 54), "ground_d": (116, 70, 40),
        "grass": (92, 200, 92), "grass_d": (60, 156, 66),
        "brick": (196, 118, 70), "brick_d": (150, 84, 48),
        "block": (244, 196, 66), "block_d": (188, 140, 36),
        "plat": (196, 150, 84), "plat_d": (150, 110, 60),
        "pipe": (72, 190, 84), "pipe_d": (44, 138, 58),
        "spike": (188, 196, 208), "accent": (255, 255, 255),
        "coin": (255, 208, 56), "coin_hi": (255, 244, 170),
    },
    1: {
        "sky_top": (22, 20, 48), "sky_bot": (58, 40, 92),
        "hill": (44, 34, 78), "hill2": (32, 24, 60),
        "ground": (78, 64, 104), "ground_d": (56, 44, 78),
        "grass": (128, 92, 188), "grass_d": (92, 62, 146),
        "brick": (96, 84, 130), "brick_d": (70, 60, 100),
        "block": (224, 184, 92), "block_d": (170, 132, 48),
        "plat": (96, 86, 132), "plat_d": (70, 62, 100),
        "pipe": (108, 76, 152), "pipe_d": (76, 50, 116),
        "spike": (210, 214, 230), "accent": (222, 200, 255),
        "coin": (255, 208, 56), "coin_hi": (255, 244, 170),
    },
    2: {
        "sky_top": (255, 148, 92), "sky_bot": (255, 224, 158),
        "hill": (212, 116, 156), "hill2": (180, 84, 132),
        "ground": (150, 96, 54), "ground_d": (116, 70, 40),
        "grass": (236, 142, 174), "grass_d": (200, 104, 142),
        "brick": (208, 130, 96), "brick_d": (162, 94, 68),
        "block": (250, 202, 96), "block_d": (196, 148, 52),
        "plat": (220, 150, 110), "plat_d": (172, 108, 78),
        "pipe": (232, 128, 110), "pipe_d": (186, 88, 78),
        "spike": (232, 224, 210), "accent": (255, 255, 255),
        "coin": (255, 214, 80), "coin_hi": (255, 248, 190),
    },
    3: {
        "sky_top": (150, 198, 236), "sky_bot": (232, 244, 252),
        "hill": (222, 236, 248), "hill2": (196, 216, 238),
        "ground": (176, 200, 224), "ground_d": (138, 166, 196),
        "grass": (246, 251, 255), "grass_d": (206, 224, 240),
        "brick": (168, 198, 226), "brick_d": (126, 156, 190),
        "block": (150, 214, 246), "block_d": (92, 166, 214),
        "plat": (196, 220, 240), "plat_d": (150, 182, 210),
        "pipe": (140, 196, 226), "pipe_d": (100, 156, 190),
        "spike": (150, 214, 246), "accent": (255, 255, 255),
        "coin": (255, 214, 90), "coin_hi": (255, 248, 190),
    },
    4: {
        "sky_top": (44, 16, 30), "sky_bot": (128, 34, 26),
        "hill": (74, 26, 30), "hill2": (54, 18, 24),
        "ground": (96, 62, 62), "ground_d": (66, 40, 42),
        "grass": (208, 84, 40), "grass_d": (150, 54, 28),
        "brick": (128, 64, 58), "brick_d": (90, 42, 40),
        "block": (244, 152, 60), "block_d": (192, 100, 34),
        "plat": (124, 72, 66), "plat_d": (86, 48, 46),
        "pipe": (124, 58, 52), "pipe_d": (86, 36, 34),
        "spike": (236, 130, 60), "accent": (255, 226, 170),
        "coin": (255, 200, 70), "coin_hi": (255, 244, 180),
        "lava": (236, 94, 30), "lava_d": (170, 48, 14),
    },
    5: {
        "sky_top": (8, 8, 8), "sky_bot": (66, 66, 66),
        "hill": (42, 42, 42), "hill2": (26, 26, 26),
        "ground": (92, 92, 92), "ground_d": (58, 58, 58),
        "grass": (208, 208, 208), "grass_d": (140, 140, 140),
        "brick": (114, 114, 114), "brick_d": (72, 72, 72),
        "block": (208, 208, 208), "block_d": (130, 130, 130),
        "plat": (126, 126, 126), "plat_d": (82, 82, 82),
        "pipe": (140, 140, 140), "pipe_d": (92, 92, 92),
        "spike": (224, 224, 224), "accent": (255, 255, 255),
        "coin": (220, 220, 220), "coin_hi": (255, 255, 255),
        "lava": (70, 70, 70), "lava_d": (34, 34, 34),
    },
    6: {
        "sky_top": (146, 198, 244), "sky_bot": (228, 244, 255),
        "hill": (244, 250, 255), "hill2": (216, 234, 250),
        "ground": (228, 240, 252), "ground_d": (184, 206, 230),
        "grass": (255, 255, 255), "grass_d": (212, 228, 246),
        "brick": (208, 226, 246), "brick_d": (166, 192, 220),
        "block": (150, 210, 250), "block_d": (94, 164, 214),
        "plat": (238, 246, 255), "plat_d": (194, 214, 238),
        "pipe": (198, 222, 246), "pipe_d": (156, 188, 222),
        "spike": (120, 176, 222), "accent": (255, 255, 255),
        "coin": (255, 214, 90), "coin_hi": (255, 248, 190),
    },
}


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def make_gradient(top, bottom, w, h):
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / float(h - 1)
        c = (int(top[0] + (bottom[0] - top[0]) * t),
             int(top[1] + (bottom[1] - top[1]) * t),
             int(top[2] + (bottom[2] - top[2]) * t))
        pygame.draw.line(surf, c, (0, y), (w, y))
    return surf


def make_tile(ch, pal, top=False):
    s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    if ch == "#":
        pygame.draw.rect(s, pal["ground"], (0, 0, TILE, TILE))
        pygame.draw.rect(s, pal["ground_d"], (0, 0, TILE, TILE), 3)
        for (dx, dy) in ((9, 12), (24, 20), (14, 30), (30, 33)):
            pygame.draw.circle(s, pal["ground_d"], (dx, dy), 2)
        if top:
            pygame.draw.rect(s, pal["grass"], (0, 0, TILE, 12))
            pygame.draw.rect(s, pal["grass_d"], (0, 10, TILE, 4))
            pygame.draw.line(s, pal["grass"], (0, 0), (TILE, 0), 3)
    elif ch == "B":
        pygame.draw.rect(s, pal["brick"], (0, 0, TILE, TILE))
        pygame.draw.rect(s, pal["brick_d"], (0, 0, TILE, TILE), 3)
        pygame.draw.line(s, pal["brick_d"], (0, TILE // 2), (TILE, TILE // 2), 3)
        pygame.draw.line(s, pal["brick_d"], (TILE // 2, 0), (TILE // 2, TILE // 2), 2)
        pygame.draw.line(s, pal["brick_d"], (TILE // 2, TILE // 2), (TILE // 2, TILE), 2)
    elif ch in ("?", "M"):
        pygame.draw.rect(s, pal["block"], (0, 0, TILE, TILE), border_radius=6)
        pygame.draw.rect(s, pal["block_d"], (0, 0, TILE, TILE), 3, border_radius=6)
        for (dx, dy) in ((6, 6), (TILE - 6, 6), (6, TILE - 6), (TILE - 6, TILE - 6)):
            pygame.draw.circle(s, pal["block_d"], (dx, dy), 2)
        f = pygame.font.SysFont("consolas", 24, bold=True)
        glyph = f.render("?", True, pal["accent"])
        s.blit(glyph, glyph.get_rect(center=(TILE // 2, TILE // 2 + 1)))
    elif ch == "X":
        pygame.draw.rect(s, pal["block_d"], (0, 0, TILE, TILE), border_radius=6)
        pygame.draw.rect(s, pal["ground_d"], (0, 0, TILE, TILE), 3, border_radius=6)
    elif ch == "=":
        pygame.draw.rect(s, pal["plat"], (0, 0, TILE, TILE))
        pygame.draw.rect(s, pal["plat_d"], (0, 0, TILE, TILE), 3)
        pygame.draw.line(s, pal["accent"], (3, 3), (TILE - 3, 3), 2)
        pygame.draw.line(s, pal["plat_d"], (3, TILE - 4), (TILE - 3, TILE - 4), 2)
    elif ch == "p":
        pygame.draw.rect(s, pal["pipe"], (4, 0, TILE - 8, TILE))
        pygame.draw.rect(s, pal["pipe_d"], (4, 0, TILE - 8, TILE), 3)
        pygame.draw.rect(s, pal["pipe"], (0, 0, TILE, 10))
        pygame.draw.rect(s, pal["pipe_d"], (0, 0, TILE, 10), 3)
        pygame.draw.line(s, pal["accent"], (8, 3), (12, 3), 2)
    elif ch == "^":
        base = TILE - 10
        pygame.draw.rect(s, pal["ground_d"], (0, base, TILE, 10))
        for i in range(4):
            x = i * (TILE // 4)
            pygame.draw.polygon(s, pal["spike"], [
                (x, TILE), (x + TILE // 8, base), (x + TILE // 4, TILE)])
    elif ch == "L":
        lava = pal.get("lava", (236, 94, 30))
        lava_d = pal.get("lava_d", (170, 48, 14))
        pygame.draw.rect(s, lava_d, (0, 0, TILE, TILE))
        pygame.draw.rect(s, lava, (0, 0, TILE, TILE // 2))
        pygame.draw.rect(s, (255, 170, 70), (0, 0, TILE, 6))
        for (dx, dy, r) in ((10, 20, 4), (26, 14, 3), (18, 30, 3), (32, 28, 3)):
            pygame.draw.circle(s, (255, 200, 110), (dx, dy), r)
        return s
    return s


SKINS = {
    0: {},
    1: {"shirt": (126, 96, 196), "shirt_d": (92, 64, 150), "overall": (74, 52, 132),
        "strap": (214, 186, 255), "strap_d": (166, 138, 210),
        "shoe": (78, 54, 96), "shoe_d": (50, 34, 64)},
    2: {"shirt": (232, 138, 58), "shirt_d": (188, 94, 30), "overall": (162, 80, 38),
        "strap": (255, 226, 150), "strap_d": (208, 170, 96),
        "shoe": (120, 70, 40), "shoe_d": (82, 46, 26)},
    3: {"shirt": (206, 224, 236), "shirt_d": (162, 188, 206), "overall": (122, 162, 200),
        "strap": (255, 255, 255), "strap_d": (206, 214, 222),
        "shoe": (92, 72, 62), "shoe_d": (58, 44, 36), "coat": True},
    4: {"shirt": (150, 156, 172), "shirt_d": (108, 114, 130), "overall": (96, 102, 120),
        "strap": (255, 182, 60), "strap_d": (206, 140, 40),
        "shoe": (66, 70, 80), "shoe_d": (40, 44, 52), "armor": True},
    5: {"skin": (178, 178, 178), "skin_hi": (212, 212, 212), "skin_sh": (126, 126, 126),
        "hair": (24, 24, 24), "hair_hi": (66, 66, 66),
        "shirt": (216, 216, 216), "shirt_d": (168, 168, 168), "overall": (108, 108, 108),
        "strap": (246, 246, 246), "strap_d": (188, 188, 188),
        "shoe": (40, 40, 40), "shoe_d": (18, 18, 18), "bw": True},
}


def render_vihaan(w, h, facing, big, walk_t, moving, on_ground, vy, speed=0.0, t=0, outfit=0):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    OL = (40, 28, 24)
    out = SKINS.get(outfit, {})
    skin = out.get("skin", (152, 98, 60))
    skin_hi = out.get("skin_hi", (184, 132, 92))
    skin_sh = out.get("skin_sh", (116, 70, 42))
    hair = out.get("hair", (50, 35, 28))
    hair_hi = out.get("hair_hi", (88, 64, 48))
    shirt = out.get("shirt", (70, 138, 228))
    shirt_d = out.get("shirt_d", (44, 100, 182))
    overall = out.get("overall", (42, 68, 154))
    strap = out.get("strap", (255, 206, 74))
    strap_d = out.get("strap_d", (206, 156, 40))
    shoe = out.get("shoe", (94, 60, 40))
    shoe_d = out.get("shoe_d", (58, 36, 24))
    white = (255, 255, 255)
    pup = (30, 24, 30)
    blush = (150, 150, 150) if out.get("bw") else (224, 128, 100)
    mouth = (60, 60, 60) if out.get("bw") else (128, 56, 48)

    cx = w // 2

    if not on_ground:
        state = "air"
    elif moving and ((speed > 0.4 and facing < 0) or (speed < -0.4 and facing > 0)):
        state = "skid"
    elif moving:
        state = "run" if speed > 4.0 else "walk"
    else:
        state = "idle"

    if state == "idle":
        step = 0.0
        bob = math.sin(t * 0.07) * 1.4
        arm = math.sin(t * 0.07) * 0.35
        lean = 0.0
    elif state == "walk":
        step = math.sin(walk_t * 0.30)
        bob = -abs(math.sin(walk_t * 0.30)) * 1.3
        arm = step
        lean = 0.0
    elif state == "run":
        step = math.sin(walk_t * 0.46)
        bob = -abs(math.sin(walk_t * 0.46)) * 2.0 - 1.0
        arm = step * 1.3
        lean = 1.0
    elif state == "skid":
        step = 0.0
        bob = -1.0
        arm = -facing * 0.6
        lean = -0.8
    else:
        step = 0.0
        arm = 0.6 if vy < 0 else -0.4
        bob = 0.0
        lean = 0.5 if vy < 0 else 0.1

    bob = int(round(bob))
    lean_off = int(lean * w * 0.07)

    head_h = int(h * 0.40)
    head_w = w - 2
    head_top = max(3, int(h * 0.06)) + bob
    if head_top < 2:
        bob += 2 - head_top
        head_top = 2
    body_top = head_top + head_h - int(h * 0.05)
    body_bot = int(h * 0.74) + bob
    if body_bot <= body_top:
        body_bot = body_top + 6
    shoe_h = max(6, int(h * 0.10))
    leg_w = max(6, int(w * 0.20))
    gap = max(2, int(w * 0.06))
    foot_y = h - shoe_h

    # ---- legs + shoes ----
    leg_swing = int(step * leg_w * 1.25)
    leg_lift = max(2, int((foot_y - body_bot) * 0.45))
    for idx, lx_ in enumerate((cx - gap - leg_w, cx + gap)):
        off = -leg_swing if idx == 0 else leg_swing
        lx2 = lx_ + off
        lift = state == "air" or (idx == 1 and step > 0.3) or (idx == 0 and step < -0.3)
        bottom = foot_y - (leg_lift if lift else 0)
        pygame.draw.rect(s, OL, (lx2 - 1, body_bot - 1, leg_w + 2, bottom - body_bot + 2), border_radius=3)
        pygame.draw.rect(s, overall, (lx2, body_bot, leg_w, bottom - body_bot + 1), border_radius=3)
        pygame.draw.rect(s, OL, (lx2 - 2, bottom - 1, leg_w + 6, shoe_h + 2), border_radius=4)
        pygame.draw.rect(s, shoe, (lx2 - 1, bottom, leg_w + 4, shoe_h), border_radius=4)
        pygame.draw.rect(s, shoe_d, (lx2 - 1, bottom + shoe_h - 2, leg_w + 4, 2), border_radius=2)

    # ---- body ----
    bx = cx - w // 2 + lean_off
    bw = w - 1
    pygame.draw.rect(s, OL, (bx - 1, body_top - 1, bw + 2, body_bot - body_top + 2), border_radius=6)
    pygame.draw.rect(s, shirt, (bx, body_top, bw, body_bot - body_top), border_radius=6)
    pygame.draw.rect(s, shirt_d, (bx + bw - 3, body_top + 2, 3, max(1, body_bot - body_top - 4)), border_radius=2)
    oy = body_top + int((body_bot - body_top) * 0.42)
    pygame.draw.rect(s, overall, (bx, oy, bw, body_bot - oy), border_radius=5)
    pygame.draw.line(s, OL, (cx - 5 + lean_off, body_top + 1), (cx - 3 + lean_off, oy + 2), 4)
    pygame.draw.line(s, strap, (cx - 5 + lean_off, body_top + 1), (cx - 3 + lean_off, oy + 2), 2)
    pygame.draw.line(s, OL, (cx + 5 + lean_off, body_top + 1), (cx + 3 + lean_off, oy + 2), 4)
    pygame.draw.line(s, strap, (cx + 5 + lean_off, body_top + 1), (cx + 3 + lean_off, oy + 2), 2)
    pygame.draw.circle(s, strap, (cx - 4 + lean_off, oy - 1), max(2, int(w * 0.07)))
    pygame.draw.circle(s, strap, (cx + 4 + lean_off, oy - 1), max(2, int(w * 0.07)))
    pygame.draw.circle(s, strap_d, (cx - 4 + lean_off, oy - 1), max(1, int(w * 0.03)))
    pygame.draw.circle(s, strap_d, (cx + 4 + lean_off, oy - 1), max(1, int(w * 0.03)))
    if out.get("coat"):
        pygame.draw.rect(s, (242, 247, 252), (bx - 1, body_top - 1, bw + 2, 6), border_radius=3)
        pygame.draw.rect(s, (224, 234, 242), (bx, body_bot - 6, bw, 6), border_radius=3)
        pygame.draw.rect(s, (206, 214, 224), (bx, body_top - 1, bw + 2, 6), 1, border_radius=3)
        pygame.draw.rect(s, strap_d, (bx, oy - 3, bw, 3))
    if out.get("armor"):
        pygame.draw.rect(s, (188, 194, 210), (bx + 2, body_top + 2, bw - 4, int((body_bot - body_top) * 0.52)),
                         border_radius=4)
        pygame.draw.rect(s, (116, 122, 138), (bx + 2, body_top + 2, bw - 4, int((body_bot - body_top) * 0.52)),
                         2, border_radius=4)
        pygame.draw.ellipse(s, (172, 178, 194), (bx - 4, body_top - 3, 12, 12))
        pygame.draw.ellipse(s, (172, 178, 194), (bx + bw - 8, body_top - 3, 12, 12))

    # ---- head ----
    hx = cx - head_w // 2 + lean_off
    hy = head_top
    pygame.draw.rect(s, OL, (hx - 1, hy - 1, head_w + 2, head_h + 2), border_radius=int(head_w * 0.34))
    pygame.draw.rect(s, skin, (hx, hy, head_w, head_h), border_radius=int(head_w * 0.32))
    pygame.draw.rect(s, skin_sh, (hx, hy + int(head_h * 0.5), 2, max(1, int(head_h * 0.5))))
    pygame.draw.rect(s, hair, (hx, hy, head_w, int(head_h * 0.30)), border_radius=int(head_w * 0.3))
    pygame.draw.rect(s, hair, (hx, hy, int(head_w * 0.30), int(head_h * 0.72)), border_radius=5)
    pygame.draw.rect(s, hair, (hx + head_w - int(head_w * 0.14), hy + int(head_h * 0.20),
                               int(head_w * 0.14), max(2, int(head_h * 0.26))), border_radius=3)
    pygame.draw.rect(s, hair_hi, (hx + int(head_w * 0.06), hy + 1, int(head_w * 0.5), 2))

    eye_y = hy + int(head_h * 0.52)
    eye_r = max(3, int(w * 0.13))
    ex1 = hx + int(head_w * 0.36)
    ex2 = hx + int(head_w * 0.70)
    blink = (state != "air") and (((t + 23) % 210) < 6)
    for ex in (ex1, ex2):
        if blink:
            pygame.draw.line(s, pup, (ex - eye_r, eye_y), (ex + eye_r, eye_y), 2)
        else:
            pygame.draw.circle(s, white, (ex, eye_y), eye_r)
            pygame.draw.circle(s, pup, (ex + max(1, eye_r // 3), eye_y), max(1, int(eye_r * 0.55)))
            pygame.draw.circle(s, white, (ex + max(1, eye_r // 3) - 1, eye_y - eye_r // 2), 1)
    pygame.draw.circle(s, blush, (ex1 - eye_r - 1, eye_y + eye_r), max(2, int(w * 0.07)))
    pygame.draw.circle(s, skin_sh, (hx + head_w - 2, hy + int(head_h * 0.66)), max(1, int(w * 0.05)))
    pygame.draw.arc(s, mouth, (hx + int(head_w * 0.42), hy + int(head_h * 0.68),
                               int(head_w * 0.36), int(head_h * 0.22)),
                    math.pi * 1.05, math.pi * 1.95, 2)

    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return s


def render_grump(w, h, walk_t, squashed=False, green=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    if green:
        body = (96, 186, 96)
        body_d = (58, 134, 62)
        belly = (170, 226, 160)
        pup = (24, 44, 26)
        brow = (40, 78, 44)
        foot = (58, 120, 62)
    else:
        body = (152, 88, 198)
        body_d = (108, 56, 146)
        belly = (198, 152, 226)
        pup = (32, 22, 44)
        brow = (54, 28, 74)
        foot = (74, 46, 100)
    white = (255, 255, 255)

    if squashed:
        pygame.draw.ellipse(s, body, (0, h - 12, w, 12))
        pygame.draw.ellipse(s, body_d, (0, h - 12, w, 12), 2)
        return s

    feet = math.sin(walk_t * 0.3) * 2.0
    pygame.draw.ellipse(s, foot, (int(w * 0.10), h - 9 + feet, int(w * 0.34), 8))
    pygame.draw.ellipse(s, foot, (int(w * 0.56), h - 9 - feet, int(w * 0.34), 8))
    pygame.draw.ellipse(s, body, (0, 2, w, h - 6))
    pygame.draw.ellipse(s, body_d, (0, 2, w, h - 6), 3)
    pygame.draw.ellipse(s, belly, (int(w * 0.22), int(h * 0.48), int(w * 0.56), int(h * 0.42)))

    for ex in (int(w * 0.24), int(w * 0.58)):
        pygame.draw.ellipse(s, white, (ex, int(h * 0.24), int(w * 0.18), int(h * 0.24)))
        pygame.draw.ellipse(s, pup, (ex + 2, int(h * 0.28), int(w * 0.10), int(h * 0.16)))
    pygame.draw.line(s, brow, (int(w * 0.22), int(h * 0.20)), (int(w * 0.40), int(h * 0.30)), 3)
    pygame.draw.line(s, brow, (int(w * 0.78), int(h * 0.20)), (int(w * 0.60), int(h * 0.30)), 3)
    pygame.draw.arc(s, brow, (int(w * 0.32), int(h * 0.52), int(w * 0.36), int(h * 0.22)),
                    math.pi * 1.15, math.pi * 1.85, 2)
    return s


def render_ramen(size, steam=0.0):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    bowl = (240, 244, 250)
    bowl_d = (196, 204, 214)
    rim = (214, 66, 62)
    rim_d = (166, 42, 40)
    broth = (236, 196, 120)
    noodle = (244, 224, 150)
    egg = (250, 246, 234)
    yolk = (250, 196, 70)
    green = (108, 190, 96)
    pygame.draw.arc(s, bowl_d, (int(size * 0.10), int(size * 0.40), int(size * 0.80), int(size * 0.55)),
                    0, math.pi, 6)
    pygame.draw.rect(s, bowl, (int(size * 0.10), int(size * 0.52), int(size * 0.80), int(size * 0.34)),
                     border_radius=int(size * 0.10))
    pygame.draw.rect(s, rim, (int(size * 0.06), int(size * 0.46), int(size * 0.88), int(size * 0.12)),
                     border_radius=int(size * 0.06))
    pygame.draw.rect(s, rim_d, (int(size * 0.06), int(size * 0.54), int(size * 0.88), 2))
    pygame.draw.ellipse(s, broth, (int(size * 0.12), int(size * 0.40), int(size * 0.76), int(size * 0.18)))
    for dx in (0.30, 0.46, 0.62):
        pygame.draw.arc(s, noodle, (int(size * dx), int(size * 0.38), int(size * 0.16), int(size * 0.14)),
                        math.pi * 1.1, math.pi * 1.9, 2)
    pygame.draw.circle(s, egg, (int(size * 0.34), int(size * 0.46)), max(2, int(size * 0.10)))
    pygame.draw.circle(s, yolk, (int(size * 0.34), int(size * 0.46)), max(1, int(size * 0.05)))
    pygame.draw.circle(s, green, (int(size * 0.70), int(size * 0.46)), max(1, int(size * 0.05)))
    for i, dx in enumerate((0.34, 0.50, 0.66)):
        y = int(size * (0.30 - 0.05 * i)) + int(math.sin(steam + i) * 2)
        pygame.draw.arc(s, (255, 255, 255), (int(size * dx), y, int(size * 0.12), int(size * 0.16)),
                        math.pi * 1.1, math.pi * 1.9, 2)
    return s


def render_mushroom(size):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    red = (226, 68, 68)
    red_d = (176, 40, 40)
    cream = (250, 236, 210)
    spot = (255, 246, 236)
    pygame.draw.ellipse(s, cream, (int(size * 0.20), int(size * 0.45), int(size * 0.60), int(size * 0.55)))
    pygame.draw.ellipse(s, (210, 190, 160), (int(size * 0.20), int(size * 0.45), int(size * 0.60), int(size * 0.55)), 2)
    pygame.draw.ellipse(s, red, (0, 0, size, int(size * 0.58)))
    pygame.draw.ellipse(s, red_d, (0, 0, size, int(size * 0.58)), 3)
    for (dx, dy, r) in ((0.26, 0.22, 0.10), (0.52, 0.12, 0.09), (0.72, 0.26, 0.10)):
        pygame.draw.circle(s, spot, (int(size * dx), int(size * dy)), max(1, int(size * r)))
    return s


def render_bat(w, h, walk_t, squashed=False, fire=False, sky=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    if fire:
        body = (196, 84, 44)
        body_d = (132, 44, 24)
        belly = (250, 190, 90)
        wing = (232, 128, 48)
        wing_d = (166, 70, 28)
    elif sky:
        body = (238, 244, 252)
        body_d = (176, 194, 214)
        belly = (255, 255, 255)
        wing = (216, 230, 246)
        wing_d = (158, 180, 206)
    else:
        body = (96, 112, 172)
        body_d = (58, 72, 122)
        belly = (176, 196, 236)
        wing = (126, 148, 208)
        wing_d = (74, 92, 148)
    white = (255, 255, 255)
    pup = (24, 24, 40)
    if squashed:
        pygame.draw.ellipse(s, body, (0, h - 10, w, 10))
        pygame.draw.ellipse(s, body_d, (0, h - 10, w, 10), 2)
        return s
    flap = math.sin(walk_t * 0.6) * 0.5
    cx = w // 2
    span = int(w * 0.42)
    top = int(h * 0.08 - flap * h * 0.30)
    bot = int(h * 0.56 + flap * h * 0.20)
    for direction in (-1, 1):
        bx = cx + direction * int(w * 0.13)
        tip = bx + direction * span
        pygame.draw.polygon(s, wing, [(bx, int(h * 0.30)), (tip, top), (tip, bot), (bx, h - 4)])
        pygame.draw.polygon(s, wing_d, [(bx, int(h * 0.30)), (tip, top), (tip, bot), (bx, h - 4)], 2)
    pygame.draw.ellipse(s, body, (int(w * 0.30), int(h * 0.16), int(w * 0.40), int(h * 0.78)))
    pygame.draw.ellipse(s, body_d, (int(w * 0.30), int(h * 0.16), int(w * 0.40), int(h * 0.78)), 2)
    pygame.draw.ellipse(s, belly, (int(w * 0.38), int(h * 0.46), int(w * 0.24), int(h * 0.42)))
    pygame.draw.polygon(s, body_d, [(cx - 7, int(h * 0.20)), (cx - 2, int(h * 0.02)), (cx + 1, int(h * 0.20))])
    pygame.draw.polygon(s, body_d, [(cx + 7, int(h * 0.20)), (cx + 2, int(h * 0.02)), (cx - 1, int(h * 0.20))])
    for ex in (cx - 8, cx + 2):
        pygame.draw.circle(s, white, (ex + 3, int(h * 0.36)), 4)
        pygame.draw.circle(s, pup, (ex + 4, int(h * 0.36)), 2)
    return s


def render_ice_zombie(w, h, walk_t, hp=2, flash=False, squashed=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    ice = (176, 224, 244)
    ice_d = (108, 168, 208)
    ice_hi = (226, 246, 255)
    dark = (60, 96, 132)
    if hp <= 1:
        ice = (140, 196, 224)
        ice_d = (86, 138, 180)
    if flash:
        ice = (240, 250, 255)
        ice_d = (196, 220, 236)
    if squashed:
        pygame.draw.ellipse(s, ice, (2, h - 12, w - 4, 12))
        pygame.draw.ellipse(s, ice_d, (2, h - 12, w - 4, 12), 2)
        return s
    sway = math.sin(walk_t * 0.25) * 2.0
    cx = w // 2
    # legs
    pygame.draw.rect(s, ice_d, (cx - 10, h - 12, 7, 12), border_radius=2)
    pygame.draw.rect(s, ice_d, (cx + 3, h - 12, 7, 12), border_radius=2)
    # body
    pygame.draw.rect(s, ice_d, (cx - 13, int(h * 0.30) + int(sway), 26, int(h * 0.58)), border_radius=6)
    pygame.draw.rect(s, ice, (cx - 11, int(h * 0.32) + int(sway), 22, int(h * 0.52)), border_radius=6)
    # ice shards on head/shoulders
    for (ox, oy, s2) in ((-13, 0.24, 9), (0, 0.16, 11), (12, 0.24, 9)):
        pygame.draw.polygon(s, ice_hi, [
            (cx + ox - s2 // 2, int(h * (oy + 0.12)) + int(sway)),
            (cx + ox, int(h * oy) + int(sway)),
            (cx + ox + s2 // 2, int(h * (oy + 0.12)) + int(sway))])
    # arms out front (zombie pose)
    pygame.draw.rect(s, ice, (cx - 20, int(h * 0.42) + int(sway), 8, 12), border_radius=3)
    pygame.draw.rect(s, ice, (cx + 12, int(h * 0.42) + int(sway), 8, 12), border_radius=3)
    # face
    ey = int(h * 0.44) + int(sway)
    for ex in (cx - 6, cx + 6):
        pygame.draw.circle(s, dark, (ex, ey), 3)
        if hp <= 1:
            pygame.draw.line(s, dark, (ex - 3, ey - 5), (ex + 3, ey - 1), 2)
    pygame.draw.rect(s, dark, (cx - 5, ey + 8, 10, 2))
    if hp <= 1:
        pygame.draw.line(s, ice_d, (cx - 9, int(h * 0.40) + int(sway)),
                         (cx + 4, int(h * 0.62) + int(sway)), 2)
    return s


def render_dark(w, h, t=0):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(s, (12, 12, 16), (w // 2, h // 2), w // 2)
    pygame.draw.circle(s, (70, 70, 92), (w // 2, h // 2), w // 2, 2)
    wob = int(math.sin(t * 0.5) * 2)
    pygame.draw.circle(s, (208, 208, 226), (w // 2 + wob, h // 2 - 2), max(1, w // 6))
    return s


def render_slime(w, h, walk_t, squashed=False, cloud=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    if cloud:
        body = (244, 250, 255)
        body_d = (186, 210, 236)
        eye = (110, 140, 180)
        shine = (255, 255, 255)
    else:
        body = (188, 188, 188)
        body_d = (112, 112, 112)
        eye = (18, 18, 18)
        shine = (240, 240, 240)
    if squashed:
        pygame.draw.ellipse(s, body, (0, h - 14, w, 14))
        pygame.draw.ellipse(s, body_d, (0, h - 14, w, 14), 2)
        return s
    squash = abs(math.sin(walk_t * 0.4))
    bh = int(h * (0.72 + 0.20 * squash))
    by = h - bh
    pygame.draw.ellipse(s, body_d, (0, by, w, bh + 2))
    pygame.draw.ellipse(s, body, (2, by + 2, w - 4, max(2, bh - 2)))
    pygame.draw.circle(s, eye, (w // 2 - 7, by + bh // 2 - 2), 3)
    pygame.draw.circle(s, eye, (w // 2 + 7, by + bh // 2 - 2), 3)
    pygame.draw.circle(s, shine, (w // 2 - 10, by + 7), 3)
    return s


def render_knight(w, h, facing, walk_t, hp=2, flash=False, state="walk"):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    OL = (18, 18, 18)
    armor = (208, 208, 208)
    armor_d = (140, 140, 140)
    armor_hi = (244, 244, 244)
    cloth = (58, 58, 58)
    if hp <= 1:
        armor = (162, 162, 162)
        armor_d = (104, 104, 104)
    if flash:
        armor = (255, 255, 255)
        armor_d = (210, 210, 210)
    cx = w // 2
    sway = math.sin(walk_t * 0.25) * 2.0
    pygame.draw.rect(s, armor_d, (cx - 10, h - 14, 8, 14), border_radius=2)
    pygame.draw.rect(s, armor_d, (cx + 2, h - 14, 8, 14), border_radius=2)
    by = int(h * 0.34) + int(sway)
    pygame.draw.rect(s, OL, (cx - 12, by - 1, 24, int(h * 0.46) + 2), border_radius=5)
    pygame.draw.rect(s, armor, (cx - 11, by, 22, int(h * 0.44)), border_radius=5)
    pygame.draw.line(s, armor_hi, (cx - 11, by + 1), (cx + 11, by + 1), 2)
    hy = int(h * 0.08) + int(sway)
    pygame.draw.rect(s, OL, (cx - 11, hy - 1, 22, int(h * 0.27) + 2), border_radius=6)
    pygame.draw.rect(s, armor, (cx - 10, hy, 20, int(h * 0.26)), border_radius=6)
    pygame.draw.rect(s, cloth, (cx - 8, hy + int(h * 0.10), 16, max(3, int(h * 0.05))), border_radius=2)
    pygame.draw.circle(s, (225, 225, 225), (cx - 3, hy + int(h * 0.12)), 2)
    pygame.draw.polygon(s, cloth, [(cx, hy), (cx - 3, hy - 7), (cx + 4, hy - 2)])
    if state == "windup":
        pygame.draw.rect(s, armor, (cx + 11, hy - 8, 4, 28))
        pygame.draw.polygon(s, armor_hi, [(cx + 12, hy - 26), (cx + 18, hy - 26), (cx + 15, hy - 8)])
    elif state == "swing":
        pygame.draw.rect(s, armor, (cx + 10, hy + int(h * 0.16), 28, 4))
        pygame.draw.polygon(s, armor_hi, [(cx + 36, hy + int(h * 0.13)),
                                          (cx + 36, hy + int(h * 0.22)),
                                          (cx + 46, hy + int(h * 0.175))])
    else:
        pygame.draw.rect(s, armor, (cx + 10, by + 6, 4, 20))
    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return s


def render_necromancer(w, h, facing, walk_t, hp=2, flash=False, cloud=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    if cloud:
        robe = (238, 244, 252)
        robe_d = (176, 198, 224)
        trim = (150, 178, 210)
        face = (86, 116, 156)
        eye = (255, 255, 255)
        if hp <= 1:
            robe = (206, 220, 236)
    else:
        robe = (44, 44, 44)
        robe_d = (22, 22, 22)
        trim = (150, 150, 150)
        face = (8, 8, 8)
        eye = (240, 240, 240)
        if hp <= 1:
            robe = (74, 74, 74)
    if flash:
        robe = (255, 255, 255)
        robe_d = (210, 210, 210)
    cx = w // 2
    sway = math.sin(walk_t * 0.2) * 1.5
    top = int(h * 0.30) + int(sway)
    pygame.draw.polygon(s, robe_d, [(cx, top), (cx - 17, h - 1), (cx + 17, h - 1)])
    pygame.draw.polygon(s, robe, [(cx, top + 2), (cx - 14, h - 3), (cx + 14, h - 3)])
    pygame.draw.circle(s, robe_d, (cx, int(h * 0.24) + int(sway)), 14)
    pygame.draw.circle(s, robe, (cx, int(h * 0.23) + int(sway)), 12)
    pygame.draw.circle(s, face, (cx, int(h * 0.26) + int(sway)), 8)
    pygame.draw.circle(s, eye, (cx - 3, int(h * 0.25) + int(sway)), 2)
    pygame.draw.circle(s, eye, (cx + 3, int(h * 0.25) + int(sway)), 2)
    pygame.draw.line(s, trim, (cx + 15, int(h * 0.20)), (cx + 20, h - 6), 3)
    pygame.draw.circle(s, eye, (cx + 15, int(h * 0.18)), 5)
    pygame.draw.line(s, robe, (cx - 10, int(h * 0.55)), (cx - 19, int(h * 0.66)), 5)
    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return s


def render_bob(w, h, facing, walk_t, flash=0, dead=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    bone = (236, 236, 236)
    bone_d = (162, 162, 162)
    cloth = (72, 72, 72)
    cloth_d = (40, 40, 40)
    eye = (10, 10, 10)
    glow = (255, 255, 255)
    if flash:
        bone = (255, 255, 255)
        cloth = (150, 150, 150)
    cx = w // 2
    sway = math.sin(walk_t * 0.15) * 2
    pygame.draw.rect(s, cloth_d, (cx - 14, h - 24, 10, 24), border_radius=3)
    pygame.draw.rect(s, cloth_d, (cx + 4, h - 24, 10, 24), border_radius=3)
    pygame.draw.rect(s, cloth, (cx - 16, h - 36, 32, 16), border_radius=4)
    pygame.draw.rect(s, cloth, (cx - 20, int(h * 0.42) + int(sway), 40, int(h * 0.28)), border_radius=8)
    hy = int(h * 0.10) + int(sway)
    pygame.draw.ellipse(s, bone_d, (cx - 24, hy - 2, 48, int(h * 0.40) + 4))
    pygame.draw.ellipse(s, bone, (cx - 22, hy, 44, int(h * 0.38)))
    for ex in (cx - 11, cx + 11):
        pygame.draw.ellipse(s, eye, (ex - 7, hy + int(h * 0.12), 14, int(h * 0.10)))
        if dead:
            pygame.draw.line(s, bone, (ex - 6, hy + int(h * 0.12)), (ex + 6, hy + int(h * 0.22)), 2)
            pygame.draw.line(s, bone, (ex - 6, hy + int(h * 0.22)), (ex + 6, hy + int(h * 0.12)), 2)
        elif ex < cx:
            pygame.draw.circle(s, glow, (ex, hy + int(h * 0.17)), 4)
    pygame.draw.arc(s, bone_d, (cx - 16, hy + int(h * 0.24), 32, int(h * 0.10)),
                    math.pi * 1.05, math.pi * 1.95, 2)
    pygame.draw.arc(s, cloth, (cx - 27, hy - 6, 54, int(h * 0.32)), math.pi, math.tau, 6)
    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return s


def render_snowball(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(s, (240, 248, 255), (w // 2, h // 2), w // 2)
    pygame.draw.circle(s, (196, 220, 244), (w // 2, h // 2), w // 2, 2)
    pygame.draw.circle(s, (255, 255, 255), (w // 2 - 2, h // 2 - 2), max(1, w // 6))
    return s


def render_feather(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    feather = (238, 236, 228)
    quill = (176, 150, 110)
    pygame.draw.ellipse(s, feather, (0, 2, w, h - 4))
    pygame.draw.ellipse(s, quill, (0, 2, w, h - 4), 1)
    pygame.draw.line(s, quill, (int(w * 0.85), h - 3), (int(w * 0.15), 3), 1)
    return s


def render_spit(w, h):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.circle(s, (150, 210, 120), (w // 2, h // 2), w // 2)
    pygame.draw.circle(s, (96, 168, 78), (w // 2, h // 2), w // 2, 2)
    pygame.draw.circle(s, (210, 240, 190), (w // 2 - 2, h // 2 - 2), max(1, w // 6))
    return s


def render_fireball(w, h, t=0):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    wob = int(math.sin(t * 0.6) * 2)
    pygame.draw.circle(s, (232, 90, 34), (cx, cy), w // 2)
    pygame.draw.circle(s, (250, 158, 40), (cx, cy), max(2, w // 2 - 3))
    pygame.draw.circle(s, (255, 224, 120), (cx + wob, cy + 2), max(1, w // 5))
    flame = int(max(2, w // 5))
    pygame.draw.polygon(s, (250, 158, 40), [
        (cx - flame, cy - w // 3), (cx, cy - w // 2 - flame + wob), (cx + flame, cy - w // 3)])
    return s


def render_boss(w, h, facing, walk_t, flash=0, dead=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    black = (34, 40, 54)
    black_d = (18, 22, 32)
    belly = (246, 248, 252)
    beak = (248, 168, 48)
    beak_d = (200, 120, 24)
    foot = (248, 168, 48)
    white = (255, 255, 255)
    pup = (24, 24, 32)
    crown = (255, 214, 84)
    crown_d = (202, 154, 38)
    if flash > 0:
        black = (250, 250, 255)
        black_d = (206, 212, 228)

    sway = math.sin(walk_t * 0.12) * 3.0
    cx = w // 2
    pygame.draw.ellipse(s, foot, (int(w * 0.14), h - 16, int(w * 0.36), 16))
    pygame.draw.ellipse(s, foot, (int(w * 0.50), h - 16, int(w * 0.36), 16))
    pygame.draw.ellipse(s, black, (int(w * 0.06), int(h * 0.10) + int(sway), int(w * 0.88), int(h * 0.90)))
    pygame.draw.ellipse(s, black_d, (int(w * 0.06), int(h * 0.10) + int(sway), int(w * 0.88), int(h * 0.90)), 3)
    pygame.draw.ellipse(s, belly, (int(w * 0.26), int(h * 0.34) + int(sway), int(w * 0.48), int(h * 0.60)))
    for direction in (-1, 1):
        ax = cx + direction * int(w * 0.40)
        pygame.draw.ellipse(s, black, (ax - 8, int(h * 0.36) + int(sway), 18, int(h * 0.42)))
    ey = int(h * 0.25) + int(sway)
    for ex in (cx - int(w * 0.18), cx + int(w * 0.05)):
        pygame.draw.circle(s, white, (ex + 7, ey), 9)
        if dead:
            pygame.draw.line(s, pup, (ex, ey - 8), (ex + 14, ey + 8), 3)
            pygame.draw.line(s, pup, (ex + 14, ey - 8), (ex, ey + 8), 3)
        else:
            pygame.draw.circle(s, pup, (ex + 8, ey), 4)
    beak_y = int(h * 0.34) + int(sway)
    sign = 1 if facing >= 0 else -1
    bx = cx + sign * 2
    pygame.draw.polygon(s, beak, [(bx, beak_y), (bx + sign * 26, beak_y + 8), (bx, beak_y + 16)])
    pygame.draw.polygon(s, beak_d, [(bx, beak_y), (bx + sign * 26, beak_y + 8), (bx, beak_y + 16)], 2)
    bt = int(h * 0.54) + int(sway)
    pygame.draw.polygon(s, (222, 62, 72), [(cx, bt), (cx - 15, bt - 5), (cx - 15, bt + 5)])
    pygame.draw.polygon(s, (222, 62, 72), [(cx, bt), (cx + 15, bt - 5), (cx + 15, bt + 5)])
    ct = int(h * 0.11) + int(sway)
    pts = [(cx - 20, ct), (cx - 20, ct - 16), (cx - 12, ct - 6), (cx, ct - 20),
           (cx + 12, ct - 6), (cx + 20, ct - 16), (cx + 20, ct)]
    pygame.draw.polygon(s, crown, pts)
    pygame.draw.polygon(s, crown_d, pts, 2)
    return s


def render_harvey(w, h, facing, walk_t, flash=0, dead=False, curled=False, charging=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    body = (176, 130, 82)
    body_d = (128, 88, 50)
    belly = (226, 200, 160)
    spike = (154, 104, 58)
    spike_d = (112, 72, 40)
    hair = (44, 30, 22)
    hair_hi = (76, 54, 38)
    nose = (38, 26, 22)
    white = (255, 255, 255)
    pup = (28, 22, 20)
    if flash > 0:
        body = (250, 250, 255)
        body_d = (206, 210, 226)
        spike = (168, 174, 194)
        spike_d = (140, 148, 170)

    cx = w // 2
    if curled:
        r = min(w, h) // 2 - 4
        c = (cx, h // 2)
        for a in range(0, 360, 24):
            ang = math.radians(a)
            pygame.draw.polygon(s, spike, [
                (c[0] + math.cos(ang - 0.20) * r, c[1] + math.sin(ang - 0.20) * r),
                (c[0] + math.cos(ang + 0.20) * r, c[1] + math.sin(ang + 0.20) * r),
                (c[0] + math.cos(ang) * (r + 15), c[1] + math.sin(ang) * (r + 15))])
        pygame.draw.circle(s, body, c, r)
        pygame.draw.circle(s, body_d, c, r, 3)
        pygame.draw.circle(s, belly, (c[0] - r // 3, c[1] - r // 4), max(4, r // 3))
        return s

    # wind-up telegraph: rear back, crouch, bristle the spikes and tremble
    dx = 0
    dy = 0
    jx = 0
    jy = 0
    spike_extra = 0
    if charging:
        dx = -int(w * 0.09)
        dy = int(h * 0.11)
        tremble = math.sin(walk_t * 1.9) * 2.2
        jx = int(tremble)
        jy = int(abs(tremble) * 0.5)
        spike_extra = 8
        body = (200, 116, 76)
        belly = (238, 206, 158)
        spike = (182, 96, 46)
        spike_d = (132, 70, 30)

    sway = math.sin(walk_t * 0.35) * 2.0 if not charging else 0.0
    feet_y = h - 12 + dy
    pygame.draw.ellipse(s, body_d, (int(w * 0.16) + dx, feet_y, int(w * 0.24), 10))
    pygame.draw.ellipse(s, body_d, (int(w * 0.58) + dx, feet_y, int(w * 0.24), 10))
    for i in range(7):
        fx = int(w * 0.14 + i * 0.105 * w) + dx + jx
        top = int(h * 0.14) + int(abs(i - 3) * 4) + dy + jy - spike_extra
        base = int(h * 0.46) + int(sway) + dy
        pygame.draw.polygon(s, spike, [(fx - 9, base), (fx, top), (fx + 9, base)])
        pygame.draw.polygon(s, spike_d, [(fx - 9, base), (fx, top), (fx + 9, base)], 1)
    byy = int(h * 0.34) + int(sway) + dy
    pygame.draw.ellipse(s, body, (int(w * 0.06) + dx, byy, int(w * 0.84), int(h * 0.60)))
    pygame.draw.ellipse(s, body_d, (int(w * 0.06) + dx, byy, int(w * 0.84), int(h * 0.60)), 3)
    pygame.draw.ellipse(s, belly, (int(w * 0.30) + dx, int(h * 0.58) + int(sway) + dy,
                                   int(w * 0.42), int(h * 0.32)))
    hx = int(w * 0.64) + dx + jx
    hy = int(h * 0.40) + int(sway) + dy + jy
    pygame.draw.ellipse(s, body, (hx - 16, hy, 42, int(h * 0.46)))
    pygame.draw.ellipse(s, belly, (hx + 18, hy + int(h * 0.18), 22, 16))
    pygame.draw.circle(s, nose, (hx + 38, hy + int(h * 0.22)), 5)
    ey = hy + 10
    for ex in (hx + 4, hx + 18):
        pygame.draw.circle(s, white, (ex, ey), 5)
        if dead:
            pygame.draw.line(s, pup, (ex - 4, ey - 4), (ex + 4, ey + 4), 2)
            pygame.draw.line(s, pup, (ex - 4, ey + 4), (ex + 4, ey - 4), 2)
        else:
            pygame.draw.circle(s, pup, (ex + 1, ey), 2)
    if charging and not dead:
        pygame.draw.line(s, hair, (hx + 1, ey - 8), (hx + 11, ey - 5), 3)
        pygame.draw.line(s, hair, (hx + 15, ey - 8), (hx + 25, ey - 5), 3)
    bxc = hx + 6
    by = hy - 8
    pygame.draw.ellipse(s, hair, (bxc - 27, by - 8, 54, 32))
    pygame.draw.ellipse(s, hair_hi, (bxc - 20, by - 4, 40, 14))
    pygame.draw.rect(s, hair, (bxc - 27, by + 2, 54, 12), border_radius=6)

    # big red "!" warning above his head while winding up
    if charging and not dead:
        ex = cx + dx
        ey0 = max(6, int(h * 0.07) + dy)
        pygame.draw.rect(s, (255, 255, 255), (ex - 4, ey0 - 9, 8, 16), border_radius=2)
        pygame.draw.rect(s, (230, 66, 58), (ex - 3, ey0 - 8, 6, 14), border_radius=2)
        pygame.draw.circle(s, (255, 255, 255), (ex, ey0 + 10), 4)
        pygame.draw.circle(s, (230, 66, 58), (ex, ey0 + 10), 3)

    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return s


def render_esmee(w, h, facing, walk_t, flash=0, dead=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    body = (152, 134, 118)
    body_d = (108, 92, 78)
    belly = (210, 196, 180)
    leg = (124, 108, 92)
    beak = (234, 170, 74)
    beak_d = (188, 122, 40)
    hair = (92, 62, 40)
    hair_hi = (126, 90, 60)
    white = (255, 255, 255)
    pup = (30, 24, 20)
    if flash > 0:
        body = (250, 250, 255)
        body_d = (206, 210, 226)
    sway = math.sin(walk_t * 0.18) * 3.0
    cx = w // 2
    sign = 1 if facing >= 0 else -1
    stride = math.sin(walk_t * 0.3) * 6.0
    pygame.draw.line(s, leg, (cx - 10, int(h * 0.62)), (cx - 14 + stride, h - 6), 7)
    pygame.draw.line(s, leg, (cx + 10, int(h * 0.62)), (cx + 14 - stride, h - 6), 7)
    pygame.draw.ellipse(s, leg, (cx - 22 + stride, h - 10, 18, 8))
    pygame.draw.ellipse(s, leg, (cx + 4 - stride, h - 10, 18, 8))
    pygame.draw.polygon(s, body_d, [(cx - 24, int(h * 0.42)), (cx - 44, int(h * 0.34)), (cx - 26, int(h * 0.58))])
    pygame.draw.ellipse(s, body, (cx - int(w * 0.34), int(h * 0.36) + int(sway), int(w * 0.68), int(h * 0.40)))
    pygame.draw.ellipse(s, body_d, (cx - int(w * 0.34), int(h * 0.36) + int(sway), int(w * 0.68), int(h * 0.40)), 3)
    pygame.draw.ellipse(s, belly, (cx - int(w * 0.22), int(h * 0.50) + int(sway), int(w * 0.40), int(h * 0.22)))
    necy = int(h * 0.13) + int(sway)
    pygame.draw.line(s, body, (cx, int(h * 0.42)), (cx + 6, necy + 14), 16)
    hx = cx + 6
    hy = necy
    pygame.draw.ellipse(s, body, (hx - 16, hy - 6, 33, 28))
    pygame.draw.ellipse(s, body_d, (hx - 16, hy - 6, 33, 28), 2)
    pygame.draw.polygon(s, beak, [(hx + sign * 10, hy + 8), (hx + sign * 30, hy + 15), (hx + sign * 10, hy + 21)])
    pygame.draw.polygon(s, beak_d, [(hx + sign * 10, hy + 8), (hx + sign * 30, hy + 15), (hx + sign * 10, hy + 21)], 2)
    ey = hy + 3
    pygame.draw.circle(s, white, (hx + sign * 4, ey), 6)
    if dead:
        pygame.draw.line(s, pup, (hx + sign * 4 - 4, ey - 4), (hx + sign * 4 + 4, ey + 4), 2)
        pygame.draw.line(s, pup, (hx + sign * 4 - 4, ey + 4), (hx + sign * 4 + 4, ey - 4), 2)
    else:
        pygame.draw.circle(s, pup, (hx + sign * 5, ey), 3)
    for (ox, oy, r) in ((-12, -10, 8), (-2, -15, 9), (10, -11, 8),
                        (-17, 0, 8), (16, -1, 8), (-13, 9, 7), (13, 9, 7), (0, 12, 8),
                        (-6, -18, 7), (5, -18, 7)):
        pygame.draw.circle(s, hair, (hx + ox, hy + oy), r)
        pygame.draw.circle(s, hair_hi, (hx + ox, hy + oy), max(1, r - 2), 2)
    for (ox, oy, r) in ((-20, 16, 7), (-24, 27, 7), (-23, 38, 6), (-19, 49, 6), (-14, 59, 5)):
        pygame.draw.circle(s, hair, (hx + ox, hy + oy), r)
        pygame.draw.circle(s, hair_hi, (hx + ox, hy + oy), max(1, r - 2), 2)
    return s


def render_laycan(w, h, facing, walk_t, flash=0, dead=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    body = (234, 216, 184)
    body_d = (188, 166, 130)
    cream = (250, 242, 224)
    hair = (86, 58, 36)
    hair_hi = (122, 88, 58)
    hoof = (84, 62, 46)
    white = (255, 255, 255)
    pup = (30, 24, 20)
    if flash > 0:
        body = (250, 250, 255)
        body_d = (206, 210, 226)
    cx = w // 2
    sign = 1 if facing >= 0 else -1
    for lx, ph in ((cx - 26, 0.0), (cx - 13, math.pi), (cx + 13, 0.0), (cx + 26, math.pi)):
        off = math.sin(walk_t * 0.3 + ph) * 5.0
        pygame.draw.line(s, body_d, (lx, int(h * 0.62)), (lx + off, h - 7), 8)
        pygame.draw.ellipse(s, hoof, (lx + off - 6, h - 10, 13, 8))
    pygame.draw.ellipse(s, body, (cx - int(w * 0.36), int(h * 0.46), int(w * 0.72), int(h * 0.30)))
    pygame.draw.ellipse(s, body_d, (cx - int(w * 0.36), int(h * 0.46), int(w * 0.72), int(h * 0.30)), 3)
    pygame.draw.ellipse(s, cream, (cx - int(w * 0.40), int(h * 0.44), 16, 24))
    neck_top = int(h * 0.15)
    pygame.draw.rect(s, body, (cx - 12, neck_top, 24, int(h * 0.40)), border_radius=10)
    pygame.draw.rect(s, body_d, (cx - 12, neck_top, 24, int(h * 0.40)), 2, border_radius=10)
    hy = neck_top
    pygame.draw.ellipse(s, body, (cx - 21, hy - 10, 42, 30))
    pygame.draw.ellipse(s, body_d, (cx - 21, hy - 10, 42, 30), 2)
    pygame.draw.ellipse(s, cream, (cx - 14 + sign * 8, hy + 5, 32, 20))
    pygame.draw.ellipse(s, body_d, (cx - 14 + sign * 8, hy + 5, 32, 20), 2)
    pygame.draw.circle(s, body_d, (cx + sign * 14, hy + 14), 2)
    ey = hy + 2
    for ex in (cx - 8, cx + 8):
        pygame.draw.circle(s, white, (ex, ey), 5)
        if dead:
            pygame.draw.line(s, pup, (ex - 4, ey - 4), (ex + 4, ey + 4), 2)
            pygame.draw.line(s, pup, (ex - 4, ey + 4), (ex + 4, ey - 4), 2)
        else:
            pygame.draw.circle(s, pup, (ex + sign, ey), 2)
    pygame.draw.polygon(s, body, [(cx - 16, hy - 8), (cx - 21, hy - 30), (cx - 7, hy - 10)])
    pygame.draw.polygon(s, body_d, [(cx - 16, hy - 8), (cx - 21, hy - 30), (cx - 7, hy - 10)], 2)
    pygame.draw.polygon(s, body, [(cx + 16, hy - 8), (cx + 21, hy - 30), (cx + 7, hy - 10)])
    pygame.draw.polygon(s, body_d, [(cx + 16, hy - 8), (cx + 21, hy - 30), (cx + 7, hy - 10)], 2)
    pygame.draw.ellipse(s, hair, (cx - 24, hy - 25, 48, 27))
    pygame.draw.ellipse(s, hair_hi, (cx - 18, hy - 23, 36, 12))
    pygame.draw.rect(s, hair, (cx - 24, hy - 13, 48, 11), border_radius=6)
    return s


def render_mech(w, h, facing, walk_t, flash=0, dead=False, rolling=False):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    OL = (30, 28, 34)
    metal = (152, 158, 174)
    metal_d = (96, 102, 120)
    metal_hi = (198, 204, 218)
    glow = (255, 128, 56)
    glass = (150, 214, 240)
    if flash > 0:
        metal = (250, 250, 255)
        metal_d = (206, 210, 226)
    cx = w // 2
    sway = math.sin(walk_t * 0.2) * 2.0
    # legs + feet
    pygame.draw.rect(s, metal_d, (cx - 30, int(h * 0.78), 18, int(h * 0.20)), border_radius=4)
    pygame.draw.rect(s, metal_d, (cx + 12, int(h * 0.78), 18, int(h * 0.20)), border_radius=4)
    pygame.draw.rect(s, metal, (cx - 36, h - 10, 28, 10), border_radius=3)
    pygame.draw.rect(s, metal, (cx + 8, h - 10, 28, 10), border_radius=3)
    # body
    pygame.draw.rect(s, OL, (cx - 42, int(h * 0.36), 84, int(h * 0.46)), border_radius=10)
    pygame.draw.rect(s, metal, (cx - 40, int(h * 0.37), 80, int(h * 0.44)), border_radius=10)
    pygame.draw.rect(s, metal_hi, (cx - 38, int(h * 0.38), 76, 7), border_radius=5)
    # chest penguin face (Gilbert motif)
    pygame.draw.circle(s, (34, 40, 54), (cx, int(h * 0.58)), 16)
    pygame.draw.circle(s, (246, 248, 252), (cx, int(h * 0.60)), 12)
    for ex in (cx - 5, cx + 5):
        if dead:
            pygame.draw.line(s, (24, 24, 32), (ex - 3, int(h * 0.56)), (ex + 3, int(h * 0.62)), 2)
            pygame.draw.line(s, (24, 24, 32), (ex - 3, int(h * 0.62)), (ex + 3, int(h * 0.56)), 2)
        else:
            pygame.draw.circle(s, (24, 24, 32), (ex, int(h * 0.59)), 2)
    pygame.draw.polygon(s, (248, 168, 48), [(cx - 4, int(h * 0.62)), (cx + 4, int(h * 0.62)),
                                            (cx, int(h * 0.66))])
    # shoulder spikes (Harvey motif)
    for ox in (-40, 40):
        pygame.draw.polygon(s, (150, 100, 54), [
            (cx + ox - 8, int(h * 0.40)), (cx + ox, int(h * 0.29)), (cx + ox + 8, int(h * 0.40))])
    # cannon arm (fire)
    pygame.draw.rect(s, metal_d, (cx + 38, int(h * 0.48), 22, 14), border_radius=4)
    pygame.draw.circle(s, glow, (cx + 60, int(h * 0.55)), 6)
    # glass dome head with eye
    pygame.draw.circle(s, OL, (cx, int(h * 0.25)), 27)
    pygame.draw.circle(s, glass, (cx, int(h * 0.25)), 24)
    pygame.draw.circle(s, (210, 244, 255), (cx - 9, int(h * 0.21)), 6)
    pygame.draw.circle(s, (60, 150, 210), (cx, int(h * 0.27)), 8)
    pygame.draw.circle(s, (20, 40, 70), (cx, int(h * 0.27)), 3)
    # feather antenna (Esmee motif)
    pygame.draw.line(s, metal_d, (cx, int(h * 0.25) - 24), (cx, int(h * 0.07)), 4)
    pygame.draw.circle(s, (126, 90, 60), (cx, int(h * 0.06)), 7)
    pygame.draw.circle(s, (150, 110, 72), (cx + 8, int(h * 0.10)), 5)
    # llama ears + bowl cut (Laycan motif) on top
    pygame.draw.polygon(s, metal, [(cx - 16, int(h * 0.13)), (cx - 21, int(h * 0.02)), (cx - 8, int(h * 0.11))])
    pygame.draw.polygon(s, metal, [(cx + 16, int(h * 0.13)), (cx + 21, int(h * 0.02)), (cx + 8, int(h * 0.11))])
    # crown
    ct = int(h * 0.03)
    pygame.draw.polygon(s, (255, 214, 84), [
        (cx - 14, ct), (cx - 14, ct - 10), (cx - 7, ct - 4), (cx, ct - 13),
        (cx + 7, ct - 4), (cx + 14, ct - 10), (cx + 14, ct)])
    if facing < 0:
        s = pygame.transform.flip(s, True, False)
    return s


class SoundBank:
    def __init__(self, audio):
        self.ok = audio
        self.muted = False
        self.current = None
        self.sounds = {}
        if not audio:
            return
        for name in ("jump", "coin", "stomp", "bump", "powerup", "hurt", "win", "life", "checkpoint"):
            path = os.path.join(_ASSETS, "sfx_%s.wav" % name)
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except Exception:
                    pass
        for s in self.sounds.values():
            s.set_volume(0.6)
        try:
            pygame.mixer.music.set_volume(0.5)
        except Exception:
            pass

    def play(self, name):
        if not self.ok or self.muted:
            return
        s = self.sounds.get(name)
        if s:
            s.play()

    def music(self, name):
        if not self.ok or self.current == name:
            return
        path = os.path.join(_ASSETS, "music_%s.wav" % name)
        if not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
            self.current = name
        except Exception:
            pass

    def toggle_mute(self):
        self.muted = not self.muted
        vol = 0.0 if self.muted else 0.6
        for s in self.sounds.values():
            s.set_volume(vol)
        if self.ok:
            try:
                pygame.mixer.music.set_volume(0.0 if self.muted else 0.5)
            except Exception:
                pass
        return self.muted


class Coin:
    def __init__(self, tx, ty):
        self.x = tx * TILE + 8
        self.y = ty * TILE + 8
        self.w = 24
        self.h = 24
        self.t = random.randint(0, 20)

    def rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update(self):
        self.t += 1


class Checkpoint:
    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty
        self.active = False

    def rect(self):
        return pygame.Rect(self.tx * TILE + 10, (self.ty - 3) * TILE, TILE - 20, 4 * TILE)

    def spawn(self):
        return (self.tx, self.ty)


class PowerUp:
    def __init__(self, tx, ty, kind="mushroom", sky=False):
        self.w = 28
        self.h = 28
        self.kind = kind
        self.sky = sky
        if sky:
            self.x = tx - self.w // 2
            self.y = -40.0
            self.vx = 0.0
            self.vy = 1.5
            self.emerge = 0.0
        else:
            self.x = tx * TILE + 6
            self.y = (ty + 1) * TILE - self.h
            self.vx = 1.6
            self.vy = 0.0
            self.emerge = 1.0

    @classmethod
    def sky_at(cls, px, kind="mushroom"):
        return cls(px, 0, kind=kind, sky=True)

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def render(self):
        if self.kind == "ramen":
            return render_ramen(self.w)
        return render_mushroom(self.w)

    def update(self, level):
        if self.sky:
            self.y += self.vy
            hits = level.solid_tiles(self.rect())
            if hits:
                self.y = min(ty for tx, ty in hits) * TILE - self.h
                self.sky = False
                self.vx = 1.6
            return
        if self.emerge > 0:
            self.emerge -= 0.06
            self.y -= 1.4
            return
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        r = self.rect()
        for (tx, ty) in level.solid_tiles(r):
            if self.vy > 0:
                self.y = ty * TILE - self.h
                self.vy = 0
            elif self.vy < 0:
                self.y = (ty + 1) * TILE
                self.vy = 0
            r = self.rect()
        self.x += self.vx
        r = self.rect()
        hits = level.solid_tiles(r)
        if hits:
            if self.vx > 0:
                self.x = min(tx for tx, ty in hits) * TILE - self.w
            else:
                self.x = (max(tx for tx, ty in hits) + 1) * TILE
            self.vx *= -1


class Enemy:
    def __init__(self, tx, ty, variant="purple"):
        self.w = 34
        self.h = 30
        self.x = tx * TILE + 3
        self.y = (ty + 1) * TILE - self.h
        self.vx = -ENEMY_SPEED
        self.vy = 0.0
        self.on_ground = False
        self.state = "walk"
        self.timer = 0
        self.walk = random.random() * 6
        self.variant = variant

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def squash(self):
        if self.state == "walk":
            self.state = "squash"
            self.timer = 20
            self.y += self.h - 12
            self.h = 12

    def update(self, level, player=None, game=None):
        if self.state == "squash":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "dead"
            return
        if self.state == "dead":
            return
        self.walk += abs(self.vx)
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        r = self.rect()
        self.on_ground = False
        hits = level.solid_tiles(r)
        if hits:
            if self.vy > 0:
                self.y = min(ty for tx, ty in hits) * TILE - self.h
                self.vy = 0
                self.on_ground = True
            elif self.vy < 0:
                self.y = (max(ty for tx, ty in hits) + 1) * TILE
                self.vy = 0
        self.x += self.vx
        r = self.rect()
        hits = level.solid_tiles(r)
        if hits:
            if self.vx > 0:
                self.x = min(tx for tx, ty in hits) * TILE - self.w
            else:
                self.x = (max(tx for tx, ty in hits) + 1) * TILE
            self.vx *= -1
        if self.on_ground:
            front = self.x - 3 if self.vx < 0 else self.x + self.w + 3
            tx = int(front // TILE)
            ty = int((self.y + self.h + 3) // TILE)
            if not level.is_solid(tx, ty):
                self.vx *= -1

    def render(self):
        return render_grump(self.w, self.h if self.state != "squash" else 14,
                            self.walk, squashed=(self.state == "squash"),
                            green=(self.variant == "green"))


class Bat:
    def __init__(self, tx, ty, variant="frost"):
        self.w = 30
        self.h = 24
        self.x = tx * TILE + 5
        self.y = ty * TILE + 8
        self.base_y = self.y
        self.vx = -1.6
        self.vy = 0.0
        self.state = "walk"
        self.timer = 0
        self.t = random.random() * 6
        self.walk = self.t
        self.emerge = 0
        self.home_speed = 2.3
        self.variant = variant
        self.shoot_cd = random.randint(40, 120)
        self.hp = 2 if variant == "sky" else 1
        self.home_range = 12 * TILE if variant == "sky" else BAT_HOME_RANGE
        self.stun_timer = 0
        self.flash = 0

    def start_ground_spawn(self):
        self.emerge = 42
        self.base_y = self.y

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def squash(self):
        if self.state != "walk":
            return
        self.hp -= 1
        self.flash = 12
        if self.hp <= 0:
            self.state = "squash"
            self.timer = 20
            self.vy = 1.0
        else:
            self.stun_timer = 24

    def update(self, level, player=None, game=None):
        if self.flash > 0:
            self.flash -= 1
        if self.stun_timer > 0:
            self.stun_timer -= 1
            return
        if self.state == "squash":
            self.timer -= 1
            self.vy = min(self.vy + GRAVITY, MAX_FALL)
            self.y += self.vy
            if self.timer <= 0:
                self.state = "dead"
            return
        if self.state == "dead":
            return
        self.walk += 0.16

        if self.emerge > 0:
            self.emerge -= 1
            self.y -= 2.4
            if self.emerge == 0:
                self.base_y = self.y
            return

        pr = player.rect() if player is not None else None
        if pr is not None:
            dx = pr.centerx - self.rect().centerx
            dy = pr.centery - self.rect().centery
            dist = math.hypot(dx, dy)
            if dist <= self.home_range:
                if self.variant == "fire" and game is not None:
                    self.shoot_cd -= 1
                    if self.shoot_cd <= 0 and dist > 1:
                        self.shoot_cd = 110
                        game.enemy_shots.append(
                            Projectile(self.rect().centerx, self.rect().centery,
                                       dx / dist * 4.6, dy / dist * 4.6 - 1.5, "fire"))
                        game.sounds.play("bump")
                    # keep a firing distance instead of sitting on the player
                    if dist > 96 and dist > 0.1:
                        self.x += dx / dist * self.home_speed
                        self.y += dy / dist * self.home_speed
                elif dist > 0.1:
                    self.x += dx / dist * self.home_speed
                    self.y += dy / dist * self.home_speed
                self.x = clamp(self.x, 0, level.pixel_w - self.w)
                self.y = clamp(self.y, 0, level.pixel_h - self.h)
                return

        self.t += 0.08
        self.x += self.vx
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vx > 0:
                self.x = min(tx for tx, ty in hits) * TILE - self.w
            else:
                self.x = (max(tx for tx, ty in hits) + 1) * TILE
            self.vx *= -1
        self.y = self.base_y + math.sin(self.t) * 26

    def render(self):
        return render_bat(self.w, self.h, self.walk, squashed=(self.state == "squash"),
                          fire=(self.variant == "fire"), sky=(self.variant == "sky"))


class IceZombie:
    def __init__(self, tx, ty):
        self.w = 28
        self.h = 40
        self.x = tx * TILE + 3
        self.y = (ty + 1) * TILE - self.h
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.state = "walk"
        self.hp = 2
        self.timer = 0
        self.walk = 0.0
        self.flash = 0
        self.emerge = 0
        self.stun_timer = 0

    def start_ground_spawn(self):
        self.emerge = 38

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def squash(self):
        if self.state != "walk":
            return
        self.hp -= 1
        self.flash = 14
        if self.hp <= 0:
            self.state = "squash"
            self.timer = 20
        else:
            self.stun_timer = 34

    def update(self, level, player=None, game=None):
        if self.flash > 0:
            self.flash -= 1
        if self.state == "squash":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "dead"
            return
        if self.state == "dead":
            return
        if self.emerge > 0:
            self.emerge -= 1
            self.y -= 1.6
            return
        if self.stun_timer > 0:
            self.stun_timer -= 1
            self.vx = 0.0
            return

        if player is not None:
            self.vx = 1.1 if player.rect().centerx > self.rect().centerx else -1.1
        self.walk += abs(self.vx)

        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        self.on_ground = False
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vy > 0:
                self.y = min(ty for tx, ty in hits) * TILE - self.h
                self.vy = 0
                self.on_ground = True
            elif self.vy < 0:
                self.y = (max(ty for tx, ty in hits) + 1) * TILE
                self.vy = 0
        self.x += self.vx
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vx > 0:
                self.x = min(tx for tx, ty in hits) * TILE - self.w
            else:
                self.x = (max(tx for tx, ty in hits) + 1) * TILE

    def render(self):
        return render_ice_zombie(self.w, self.h, self.walk, self.hp, self.flash > 0,
                                 squashed=(self.state == "squash"))


class Slime:
    def __init__(self, tx, ty, cloud=False):
        self.w = 34
        self.h = 26
        self.x = tx * TILE + 3
        self.y = (ty + 1) * TILE - self.h
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.state = "walk"
        self.timer = random.randint(20, 60)
        self.walk = 0.0
        self.cloud = cloud

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def squash(self):
        if self.state == "walk":
            self.state = "squash"
            self.timer = 18

    def update(self, level, player=None, game=None):
        if self.state == "squash":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "dead"
            return
        if self.state == "dead":
            return
        self.walk += 0.15
        direction = 0
        if player is not None:
            direction = 1 if player.rect().centerx > self.rect().centerx else -1
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        self.on_ground = False
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vy > 0:
                self.y = min(ty for tx, ty in hits) * TILE - self.h
                self.vy = 0
                self.on_ground = True
            elif self.vy < 0:
                self.y = (max(ty for tx, ty in hits) + 1) * TILE
                self.vy = 0
        self.timer -= 1
        if self.on_ground and self.timer <= 0:
            self.vy = -9.5
            self.vx = direction * 2.2
            self.timer = random.randint(40, 70)
        self.x += self.vx
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vx > 0:
                self.x = min(tx for tx, ty in hits) * TILE - self.w
            elif self.vx < 0:
                self.x = (max(tx for tx, ty in hits) + 1) * TILE
            self.vx = 0

    def render(self):
        return render_slime(self.w, self.h, self.walk, squashed=(self.state == "squash"),
                            cloud=self.cloud)


class Knight:
    def __init__(self, tx, ty):
        self.w = 30
        self.h = 44
        self.x = tx * TILE + 5
        self.y = (ty + 1) * TILE - self.h
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.state = "walk"
        self.hp = 2
        self.timer = 0
        self.walk = 0.0
        self.flash = 0
        self.facing = 1
        self.attack_cd = random.randint(0, 60)
        self.hit_active = False

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def sword_rect(self):
        r = self.rect()
        if self.facing >= 0:
            return pygame.Rect(r.right, r.top + 8, 30, 24)
        return pygame.Rect(r.left - 30, r.top + 8, 30, 24)

    def squash(self):
        if self.state not in ("walk", "windup", "swing"):
            return
        self.hp -= 1
        self.flash = 12
        if self.hp <= 0:
            self.state = "squash"
            self.timer = 20
        else:
            self.state = "walk"
            self.timer = 0
            self.attack_cd = 40
        self.hit_active = False

    def update(self, level, player=None, game=None):
        if self.flash > 0:
            self.flash -= 1
        self.hit_active = False
        if self.state == "squash":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "dead"
            return
        if self.state == "dead":
            return
        self.walk += 0.2
        if player is not None:
            self.facing = 1 if player.rect().centerx > self.rect().centerx else -1
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        self.on_ground = False
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vy > 0:
                self.y = min(ty for tx, ty in hits) * TILE - self.h
                self.vy = 0
                self.on_ground = True
            elif self.vy < 0:
                self.y = (max(ty for tx, ty in hits) + 1) * TILE
                self.vy = 0
        if self.attack_cd > 0:
            self.attack_cd -= 1
        if self.state == "walk":
            self.vx = 1.3 * self.facing
            if player is not None and self.on_ground and self.attack_cd <= 0:
                if abs(player.rect().centerx - self.rect().centerx) < 54:
                    self.state = "windup"
                    self.timer = 16
                    self.vx = 0.0
        elif self.state == "windup":
            self.vx = 0.0
            self.timer -= 1
            if self.timer <= 0:
                self.state = "swing"
                self.timer = 14
        elif self.state == "swing":
            self.vx = 0.0
            if 3 <= self.timer <= 11:
                self.hit_active = True
            self.timer -= 1
            if self.timer <= 0:
                self.state = "walk"
                self.attack_cd = 70
        self.x += self.vx
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vx > 0:
                self.x = min(tx for tx, ty in hits) * TILE - self.w
            elif self.vx < 0:
                self.x = (max(tx for tx, ty in hits) + 1) * TILE

    def render(self):
        return render_knight(self.w, self.h, self.facing, self.walk, self.hp,
                             self.flash > 0, self.state)


class Necromancer:
    def __init__(self, tx, ty, cloud=False, variant="necro"):
        self.cloud = cloud
        self.variant = variant
        self.w = 40 if cloud else 30
        self.h = 58 if cloud else 46
        self.x = tx * TILE + 5
        self.y = (ty + 1) * TILE - self.h
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.state = "walk"
        self.hp = 4 if cloud else 2
        self.walk = 0.0
        self.flash = 0
        self.facing = 1
        self.action_cd = random.randint(60, 140)

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def squash(self):
        if self.state != "walk":
            return
        self.hp -= 1
        self.flash = 12
        if self.hp <= 0:
            self.state = "squash"
            self.timer = 20
        else:
            self.attack_cd = 40

    def update(self, level, player=None, game=None):
        if self.flash > 0:
            self.flash -= 1
        if self.state == "squash":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "dead"
            return
        if self.state == "dead":
            return
        self.walk += 0.1
        if player is not None:
            self.facing = 1 if player.rect().centerx > self.rect().centerx else -1
        self.vy = min(self.vy + GRAVITY, MAX_FALL)
        self.y += self.vy
        self.on_ground = False
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vy > 0:
                self.y = min(ty for tx, ty in hits) * TILE - self.h
                self.vy = 0
                self.on_ground = True
            elif self.vy < 0:
                self.y = (max(ty for tx, ty in hits) + 1) * TILE
                self.vy = 0
        self.action_cd -= 1
        if self.action_cd <= 0 and player is not None and game is not None and self.on_ground:
            self.action_cd = random.randint(130, 210)
            if random.random() < 0.5:
                b = self.rect()
                bx, by = b.centerx, b.top + 16
                px, py = player.rect().centerx, player.rect().centery
                dx, dy = px - bx, py - by
                dist = max(1.0, math.hypot(dx, dy))
                for off in (-0.28, 0.0, 0.28):
                    game.enemy_shots.append(
                        Projectile(bx, by, dx / dist * 5.0, dy / dist * 5.0 + off * 4, "dark"))
                game.sounds.play("bump")
            else:
                s = Slime(int(self.rect().centerx // TILE) + random.choice((-1, 1)) * random.randint(1, 3),
                          12, cloud=self.cloud)
                level.enemies.append(s)
        # drift to keep ~3 tiles away
        if player is not None:
            d = player.rect().centerx - self.rect().centerx
            self.vx = 0.0 if abs(d) < 100 else (0.7 if d > 0 else -0.7)
        self.x += self.vx
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vx > 0:
                self.x = min(tx for tx, ty in hits) * TILE - self.w
            elif self.vx < 0:
                self.x = (max(tx for tx, ty in hits) + 1) * TILE

    def render(self):
        return render_necromancer(self.w, self.h, self.facing, self.walk,
                                  self.hp, self.flash > 0, self.cloud)


class Projectile:
    def __init__(self, x, y, vx, vy, kind="snow"):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.kind = kind
        self.parryable = kind not in ("fire", "dark")
        self.w = 22 if kind == "feather" else 20
        self.h = 16 if kind == "feather" else 20
        self.life = 320
        self.t = 0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, level):
        self.t += 1
        if self.kind == "feather":
            self.vy += 0.05
            self.x += self.vx
            self.y += self.vy + math.sin(self.t * 0.25) * 1.7
        elif self.kind == "spit":
            self.vy = min(self.vy + 0.32, 12.0)
            self.x += self.vx
            self.y += self.vy
        else:
            self.vy = min(self.vy + 0.5, 12.0)
            self.x += self.vx
            self.y += self.vy
        self.life -= 1
        rect = self.rect()
        if level.solid_tiles(rect):
            self.life = 0
        if rect.right < 0 or rect.left > level.pixel_w or rect.top > level.pixel_h:
            self.life = 0

    def render(self):
        if self.kind == "feather":
            return render_feather(self.w, self.h)
        if self.kind == "spit":
            return render_spit(self.w, self.h)
        if self.kind == "fire":
            return render_fireball(self.w, self.h, self.t)
        if self.kind == "dark":
            return render_dark(self.w, self.h, self.t)
        return render_snowball(self.w, self.h)


class Ramen:
    def __init__(self, x, y, vx, vy):
        self.x = float(x)
        self.y = float(y)
        self.vx = vx
        self.vy = vy
        self.w = 24
        self.h = 20
        self.life = 150
        self.spin = 0.0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, level):
        self.spin += 0.4
        self.vy = min(self.vy + 0.5, 11.0)
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        r = self.rect()
        if level.solid_tiles(r):
            self.life = 0
        if r.right < 0 or r.left > level.pixel_w or r.top > level.pixel_h:
            self.life = 0

    def render(self):
        img = render_ramen(self.w, self.spin)
        return pygame.transform.rotate(img, -self.spin * 24)


BOSS_CONFIG = {
    "harvey": {"name": "Harvey the Hedgehog", "hp": 100, "w": 92, "h": 68,
               "stomp": 12, "speed": 1.9},
    "esmee": {"name": "Esmee the Emu", "hp": 120, "w": 84, "h": 120,
              "stomp": 12, "speed": 1.6},
    "laycan": {"name": "Laycan the Llama", "hp": 130, "w": 96, "h": 124,
               "stomp": 13, "speed": 1.4},
    "gilbert": {"name": "Gilbert the Penguin", "hp": 200, "w": 96, "h": 108,
                "stomp": 15, "speed": 2.1},
    "mech": {"name": "The Mecha-Minions", "hp": 190, "w": 156, "h": 170,
             "stomp": 20, "speed": 0.5, "pad_x": 44, "pad_y": 40},
    "bob": {"name": "Powerful Bob", "hp": 150, "w": 84, "h": 96,
            "stomp": 15, "speed": 1.5, "dmg_mult": 0.75},
}


class Boss:
    def __init__(self, kind, tx, ty, left, right):
        cfg = BOSS_CONFIG.get(kind, BOSS_CONFIG["gilbert"])
        self.kind = kind
        self.name = cfg["name"]
        self.w = cfg["w"]
        self.h = cfg["h"]
        self.max_hp = cfg["hp"]
        self.hp = cfg["hp"]
        self.stomp_damage = cfg["stomp"]
        self.speed = cfg["speed"]
        self.damage_taken_mult = cfg.get("dmg_mult", 1.0)
        self.pad_x = cfg.get("pad_x", 0)
        self.pad_y = cfg.get("pad_y", 0)
        self.x = tx * TILE
        self.y = (ty + 1) * TILE - self.h
        self.arena_left = left
        self.arena_right = right
        self.state = "idle"
        self.timer = 90
        self.facing = -1
        self.flash = 0
        self.dead = False
        self.dead_timer = 150
        self.walk = 0.0
        self.active = False
        self.shots = []
        self.count = 0
        self.vx = 0.0
        self.vy = 0.0
        self.vulnerable = True
        self.attack_delay = 0
        self.stunned = False
        self.warn_next = "walk"
        self.warn_next_timer = 0
        self.walls_built = False
        self.bat_timer = GILBERT_BAT_INTERVAL
        self.regen_timer = MECH_REGEN_INTERVAL

    def rect(self):
        return pygame.Rect(int(self.x + self.pad_x), int(self.y + self.pad_y),
                           self.w - 2 * self.pad_x, self.h - 2 * self.pad_y)

    def sprite_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def _initial_state(self):
        return "sprint" if self.kind == "esmee" else "walk"

    def _face(self, player):
        p = player.rect().centerx
        b = self.rect().centerx
        if p != b:
            self.facing = 1 if p > b else -1

    def _telegraph(self, next_state, delay, next_timer):
        self.state = "warn"
        self.warn_next = next_state
        self.warn_next_timer = next_timer
        self.timer = delay
        self.vx = 0.0

    def damage(self, amount, game=None):
        if self.dead or not self.vulnerable:
            return
        amount = max(1, int(round(amount * self.damage_taken_mult)))
        self.hp = max(0, self.hp - amount)
        self.flash = 14
        if self.hp <= 0:
            self.dead = True
            self.dead_timer = 170
            self.shots = []
            if game:
                game.sounds.play("powerup")
        elif self.kind == "harvey":
            self.attack_delay = HARVEY_ATTACK_DELAY

    def _spawn(self, x, y, vx, vy, kind):
        self.shots.append(Projectile(x, y, vx, vy, kind))

    def shoot_aimed(self, player, game, kind, speed, vy_scale, vy_bias):
        b = self.rect()
        bx = b.centerx
        by = b.top + int(self.h * 0.30)
        p = player.rect()
        dx = p.centerx - bx
        dy = p.centery - by
        dist = max(1.0, math.hypot(dx, dy))
        self._spawn(bx, by, dx / dist * speed, dy / dist * speed * vy_scale + vy_bias, kind)
        game.sounds.play("bump")

    def _fan(self, game):
        b = self.rect()
        bx = b.centerx + self.facing * 30
        by = b.top + int(self.h * 0.30)
        for vy in (-6.0, -1.0, 3.5):
            self._spawn(bx, by, self.facing * 9.5, vy, "feather")
        game.sounds.play("bump")

    def _spawn_zombie(self, game):
        lvl = game.level
        left_tx = int(self.arena_left) // TILE + 1
        right_tx = int(self.arena_right) // TILE - 1
        if right_tx <= left_tx:
            right_tx = left_tx + 1
        tx = random.randint(left_tx, right_tx)
        z = IceZombie(tx, 12)
        z.start_ground_spawn()
        lvl.enemies.append(z)
        game.add_sparks(tx * TILE + TILE // 2, 12 * TILE, (170, 220, 255))
        game.sounds.play("bump")

    def update(self, player, game):
        self.walk += abs(self.vx)
        for s in self.shots:
            s.update(game.level)
        self.shots = [s for s in self.shots if s.life > 0]

        if self.dead:
            self.dead_timer -= 1
            self.vy = min(self.vy + GRAVITY, MAX_FALL)
            self.y += self.vy
            return

        if not self.active:
            if player.rect().centerx > self.arena_left + 120:
                self.active = True
                self.state = self._initial_state()
                self.timer = 70
                self._face(player)
            return

        if self.flash > 0:
            self.flash -= 1

        if self.kind == "gilbert" and self.hp < 100:
            self.bat_timer -= 1
            if self.bat_timer <= 0:
                self.bat_timer = GILBERT_BAT_INTERVAL
                self._spawn_zombie(game)

        if self.attack_delay > 0:
            self.attack_delay -= 1
            self.stunned = True
            self.vx = 0.0
            self.vulnerable = self.state != "curl"
        else:
            self.stunned = False
            self.timer -= 1

            if self.state == "warn":
                self.vx = 0.0
                self.vulnerable = True
                self._face(player)
                if self.timer <= 0:
                    self.state = self.warn_next
                    self.timer = self.warn_next_timer
            elif self.kind == "harvey":
                self._ai_harvey(player, game)
                self.vulnerable = self.state != "curl"
            elif self.kind == "esmee":
                self._ai_esmee(player, game)
                self.vulnerable = True
            elif self.kind == "laycan":
                self._ai_laycan(player, game)
                self.vulnerable = True
            elif self.kind == "mech":
                self._ai_mech(player, game)
                self.vulnerable = self.state != "roll"
            elif self.kind == "bob":
                self._ai_bob(player, game)
                self.vulnerable = True
            else:
                self._ai_gilbert(player, game)
                self.vulnerable = True

        nx = self.x + self.vx
        bounce = False
        if nx <= self.arena_left:
            nx = self.arena_left
            bounce = True
        elif nx >= self.arena_right - self.w:
            nx = self.arena_right - self.w
            bounce = True
        self.x = nx
        if bounce and self.kind == "harvey" and self.state == "curl":
            self.facing *= -1

    def _ai_gilbert(self, player, game):
        self._face(player)
        if self.state == "walk":
            self.vx = self.speed * self.facing
            if self.timer <= 0:
                if random.random() < 0.5:
                    self.count = 0
                    self._telegraph("throw", 30, 24)
                else:
                    self._telegraph("slide", 30, 46)
        elif self.state == "slide":
            self.vx = self.speed * 3.0 * self.facing
            if self.timer <= 0:
                self.state = "walk"
                self.timer = 95
        elif self.state == "throw":
            self.vx = 0.0
            if self.timer <= 0:
                if self.count < 3:
                    self.shoot_aimed(player, game, "snow",
                                    8.0 if self.hp > 75 else 9.5, 4.0, -4.0)
                    self.count += 1
                    self.timer = 24
                else:
                    self.state = "walk"
                    self.timer = 105
        else:
            self.vx = 0.0

    def _ai_harvey(self, player, game):
        if self.state == "walk":
            self._face(player)
            self.vx = self.speed * self.facing
            if self.timer <= 0:
                self.state = "charge"
                self.timer = 36
                self.vx = 0.0
        elif self.state == "charge":
            self.vx = 0.0
            self.walk += 3.0          # drive the wind-up tremble animation
            self._face(player)
            if self.timer <= 0:
                self.state = "curl"
                self.timer = 115
        elif self.state == "curl":
            self.vx = self.speed * 3.8 * self.facing
            if self.timer <= 0:
                self.state = "recover"
                self.timer = 85
                self.vx = 0.0
        elif self.state == "recover":
            self.vx = 0.0
            if self.timer <= 0:
                self.state = "walk"
                self.timer = 70
        else:
            self.vx = 0.0

    def _ai_esmee(self, player, game):
        if self.state == "sprint":
            self.vx = self.speed * 2.6 * self.facing
            if self.timer <= 0:
                self.count = 0
                self._face(player)
                self._telegraph("peck", 30, 34)
        elif self.state == "peck":
            self.vx = 0.0
            self._face(player)
            if self.timer <= 0:
                if self.count < 3:
                    self._fan(game)
                    self.count += 1
                    self.timer = 26
                else:
                    self.state = "cooldown"
                    self.timer = ESMEE_COOLDOWN
        elif self.state == "cooldown":
            self.vx = self.speed * 0.7 * self.facing
            self._face(player)
            if self.timer <= 0:
                self.state = "sprint"
                self.timer = 55
        else:
            self.state = "sprint"
            self.vx = 0.0

    def _ai_laycan(self, player, game):
        if self.state == "walk":
            self._face(player)
            self.vx = self.speed * self.facing
            if self.timer <= 0:
                if random.random() < 0.55:
                    self.count = 0
                    self._telegraph("spit", 30, 20)
                else:
                    self._telegraph("lunge", 30, 34)
        elif self.state == "spit":
            self.vx = 0.0
            self._face(player)
            if self.timer <= 0:
                if self.count < 5:
                    self.shoot_aimed(player, game, "spit", 10.5, 2.0, -2.0)
                    self.count += 1
                    self.timer = 12
                else:
                    self.state = "walk"
                    self.timer = 80
        elif self.state == "lunge":
            self.vx = self.speed * 3.5 * self.facing
            if self.timer <= 0:
                self.state = "walk"
                self.timer = 70
        else:
            self.vx = 0.0

    def _ai_mech(self, player, game):
        if self.state == "walk":
            self._face(player)
            self.vx = self.speed * self.facing
            if self.timer <= 0:
                move = random.choice(["feathers", "spit", "snow", "fire", "roll", "zombie"])
                if move == "feathers":
                    self.count = 0
                    self._telegraph("feathers", 50, 60)
                elif move == "spit":
                    self.count = 0
                    self._telegraph("spit", 50, 36)
                elif move == "snow":
                    self.count = 0
                    self._telegraph("snow", 50, 46)
                elif move == "fire":
                    self.count = 0
                    self._telegraph("fire", 50, 40)
                elif move == "roll":
                    self._telegraph("roll", 50, 130)
                else:
                    self._telegraph("zombie", 50, 60)
        elif self.state == "feathers":
            self.vx = 0.0
            self._face(player)
            if self.timer <= 0:
                if self.count < 3:
                    self._fan(game)
                    self.count += 1
                    self.timer = 44
                else:
                    self.state = "walk"
                    self.timer = 150
        elif self.state == "spit":
            self.vx = 0.0
            self._face(player)
            if self.timer <= 0:
                if self.count < 4:
                    self.shoot_aimed(player, game, "spit", 9.0, 2.0, -2.0)
                    self.count += 1
                    self.timer = 24
                else:
                    self.state = "walk"
                    self.timer = 150
        elif self.state == "snow":
            self.vx = 0.0
            if self.timer <= 0:
                if self.count < 4:
                    self.shoot_aimed(player, game, "snow", 7.5, 4.0, -4.0)
                    self.count += 1
                    self.timer = 44
                else:
                    self.state = "walk"
                    self.timer = 150
        elif self.state == "fire":
            self.vx = 0.0
            self._face(player)
            if self.timer <= 0:
                if self.count < 3:
                    self.shoot_aimed(player, game, "fire", 6.5, 3.0, -3.0)
                    self.count += 1
                    self.timer = 40
                else:
                    self.state = "walk"
                    self.timer = 150
        elif self.state == "roll":
            self.vx = self.speed * 4.2 * self.facing
            if self.timer <= 0:
                self.state = "walk"
                self.timer = 160
        elif self.state == "zombie":
            self.vx = 0.0
            if self.timer <= 0:
                self._spawn_zombie(game)
                self.state = "walk"
                self.timer = 160
        else:
            self.vx = 0.0

    def _ai_bob(self, player, game):
        if self.state == "walk":
            self._face(player)
            self.vx = self.speed * self.facing
            if self.timer <= 0:
                self.count = 0
                self._telegraph("bones", 28, 22)
        elif self.state == "bones":
            self.vx = 0.0
            self._face(player)
            if self.timer <= 0:
                if self.count < 4:
                    b = self.rect()
                    bx, by = b.centerx, b.top + int(self.h * 0.34)
                    px, py = player.rect().centerx, player.rect().centery
                    dx, dy = px - bx, py - by
                    dist = max(1.0, math.hypot(dx, dy))
                    for off in (-4.0, -1.5, 1.0, 3.5):
                        self._spawn(bx, by, dx / dist * 7.0,
                                    dy / dist * 7.0 + off, "dark")
                    self.count += 1
                    self.timer = 28
                    game.sounds.play("bump")
                else:
                    self.state = "walk"
                    self.timer = 90
        else:
            self.vx = 0.0

    def render(self):
        if self.kind == "harvey":
            return render_harvey(self.w, self.h, self.facing, self.walk,
                                 self.flash, self.dead, self.state == "curl",
                                 self.state == "charge")
        if self.kind == "esmee":
            return render_esmee(self.w, self.h, self.facing, self.walk,
                                self.flash, self.dead)
        if self.kind == "laycan":
            return render_laycan(self.w, self.h, self.facing, self.walk,
                                 self.flash, self.dead)
        if self.kind == "mech":
            return render_mech(self.w, self.h, self.facing, self.walk,
                               self.flash, self.dead, self.state == "roll")
        if self.kind == "bob":
            return render_bob(self.w, self.h, self.facing, self.walk,
                              self.flash, self.dead)
        return render_boss(self.w, self.h, self.facing, self.walk, self.flash, self.dead)


class Player:
    def __init__(self, tx, ty):
        self.w = PW
        self.h = PH
        self.x = tx * TILE + (TILE - PW) // 2
        self.y = (ty + 1) * TILE - PH
        self.vx = 0.0
        self.vy = 0.0
        self.xs = 0.0                    # SMB horizontal speed (subpixels/frame)
        self.running_timer = 0
        self.running_speed = False
        self.up_grav = JUMP_UP_GRAV[0] / 256.0 * SMB_SCALE
        self.down_grav = JUMP_DOWN_GRAV[0] / 256.0 * SMB_SCALE
        self.on_ground = False
        self.facing = 1
        self.big = False
        self.walk = 0.0
        self.invuln = 0
        self.hearts = PLAYER_START_HEARTS
        self.skin = 0
        self.dying = False
        self.dead_timer = 0
        self.bumped = []
        self.ramen = False
        self.shoot = False
        self.prev_run = False
        self.parry = 0
        self.prev_jump = False
        self.flip = 0
    def rect(self):
        return pygame.Rect(int(round(self.x)), int(round(self.y)), self.w, self.h)

    def grow(self):
        if not self.big:
            bottom = self.y + self.h
            self.big = True
            self.w, self.h = BIGW, BIGH
            self.y = bottom - self.h

    def shrink(self):
        if self.big:
            bottom = self.y + self.h
            self.big = False
            self.w, self.h = PW, PH
            self.y = bottom - self.h

    def double_jump(self):
        y = 0
        xsabs = abs(self.xs)
        for i in range(4):
            if xsabs < JUMP_SPEED_THRESH[i]:
                break
            y += 1
        self.vy = JUMP_SPEED[y] * SMB_SCALE
        self.up_grav = JUMP_UP_GRAV[y] / 256.0 * SMB_SCALE
        self.down_grav = JUMP_DOWN_GRAV[y] / 256.0 * SMB_SCALE
        self.on_ground = False

    def die(self, sounds):
        if not self.dying:
            self.dying = True
            self.dead_timer = 0
            self.vy = -4 * SMB_SCALE
            sounds.play("hurt")

    def hurt(self, sounds):
        if self.invuln > 0 or self.dying:
            return
        self.hearts -= 1
        self.invuln = 90
        sounds.play("hurt")
        if self.hearts <= 0:
            self.die(sounds)

    def _update_horizontal(self, keys):
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        run = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_x]
        on_ground = self.on_ground

        self.shoot = bool(run) and not self.prev_run
        self.prev_run = bool(run)

        if left and not right:
            buttons = -1
        elif right and not left:
            buttons = 1
        else:
            buttons = 0

        if self.xs > 0:
            moving_dir = 1
        elif self.xs < 0:
            moving_dir = -1
        else:
            moving_dir = 0

        # facing is only updated while on the ground (SMB OnGroundStateSub)
        if buttons != 0 and on_ground:
            self.facing = buttons
        facing = self.facing
        xsabs = abs(self.xs)

        # RunningTimer: set on the ground when B is held along the move direction
        if run and on_ground and buttons != 0 and buttons == moving_dir:
            self.running_timer = 10
        elif self.running_timer > 0:
            self.running_timer -= 1

        # RunningSpeed flag (SMB GetPlayerAnimSpeed)
        if xsabs >= 28:
            self.running_speed = True
        elif buttons == moving_dir and xsabs < 28:
            self.running_speed = False

        # max-speed selector Y and friction index ($00) -- SMB PlayerPhysicsSub
        run_in_dir = on_ground and buttons != 0 and buttons == moving_dir and (run or self.running_timer != 0)
        if not on_ground:
            max_speed = X_MAX_RUN if xsabs >= 25 else X_MAX_WALK
        else:
            max_speed = X_MAX_RUN if run_in_dir else X_MAX_WALK

        idx = 0
        if not on_ground:
            if xsabs < 25:
                idx = 2 if self.running_speed else 1
        else:
            if not run_in_dir:
                idx = 2 if self.running_speed else 1

        # friction is imposed on the ground, and in the air only when steering
        if on_ground or buttons != 0:
            adder = FRICTION_DATA[idx]
            if facing != moving_dir:
                adder *= 2
            if buttons != 0:
                sign = buttons
            elif moving_dir != 0:
                sign = -moving_dir
            else:
                sign = 0
            self.xs += (adder / 256.0) * sign
            self.xs = clamp(self.xs, -max_speed, max_speed)

        # skid speed reset while grounded (only when there is existing motion to
        # cancel -- SMB additionally rewrites Player_MovingDir here, which lets
        # you still accelerate from a standstill)
        if on_ground and moving_dir != 0 and buttons != moving_dir and xsabs < 11:
            self.xs = 0.0

        self.vx = self.xs * SMB_SCALE / 16.0

    def _update_vertical(self, keys, sounds):
        jump = (keys[pygame.K_SPACE] or keys[pygame.K_UP]
                or keys[pygame.K_w] or keys[pygame.K_z])
        if self.on_ground:
            if jump:
                y = 0
                xsabs = abs(self.xs)
                for i in range(4):
                    if xsabs < JUMP_SPEED_THRESH[i]:
                        break
                    y += 1
                self.vy = JUMP_SPEED[y] * SMB_SCALE
                self.up_grav = JUMP_UP_GRAV[y] / 256.0 * SMB_SCALE
                self.down_grav = JUMP_DOWN_GRAV[y] / 256.0 * SMB_SCALE
                self.on_ground = False
                sounds.play("jump")
            else:
                self.vy = 1.0
        else:
            if self.vy < 0 and jump:
                self.vy += self.up_grav
            else:
                self.vy += self.down_grav
            cap = FALL_CAP * SMB_SCALE
            if self.vy > cap:
                self.vy = cap

    def move_x(self, level):
        self.vx = self.xs * SMB_SCALE / 16.0
        self.x += self.vx
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vx > 0:
                self.x = min(tx for tx, ty in hits) * TILE - self.w
            elif self.vx < 0:
                self.x = (max(tx for tx, ty in hits) + 1) * TILE
            if self.vx != 0:
                self.xs = 0.0
            self.vx = 0.0

    def move_y(self, level):
        self.y += self.vy
        hits = level.solid_tiles(self.rect())
        if hits:
            if self.vy > 0:
                self.y = min(ty for tx, ty in hits) * TILE - self.h
                self.vy = 0.0
                self.on_ground = True
            elif self.vy < 0:
                self.y = (max(ty for tx, ty in hits) + 1) * TILE
                self.vy = 0.0
                for t in hits:
                    self.bumped.append(t)

    def update(self, keys, level, sounds):
        if self.invuln > 0:
            self.invuln -= 1
        if self.dying:
            self.dead_timer += 1
            self.vy = min(self.vy + GRAVITY, MAX_FALL)
            self.y += self.vy
            return

        self._update_horizontal(keys)
        self._update_vertical(keys, sounds)
        if self.flip > 0:
            self.flip -= 1
        self.on_ground = False
        self.move_x(level)
        self.move_y(level)
        if abs(self.vx) > 0.2 and self.on_ground:
            self.walk += abs(self.vx)


class Camera:
    def __init__(self):
        self.x = 0.0

    def update(self, player, level):
        target = player.rect().centerx - W * 0.42
        target = clamp(target, 0, max(0, level.pixel_w - W))
        self.x += (target - self.x) * 0.12
        self.x = clamp(self.x, 0, max(0, level.pixel_w - W))

    def ix(self):
        return int(self.x)


class Spark:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.0, 4.0)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - 2.0
        self.life = random.randint(18, 34)
        self.color = color
        self.size = random.randint(2, 4)

    def update(self):
        self.vy += 0.35
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, surf, camx):
        pygame.draw.circle(surf, self.color, (int(self.x - camx), int(self.y)), self.size)


class FloatText:
    def __init__(self, text, x, y, color=(255, 255, 255)):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.life = 45

    def update(self):
        self.y -= 1.1
        self.life -= 1

    def draw(self, surf, camx, font):
        img = font.render(self.text, True, self.color)
        surf.blit(img, img.get_rect(center=(int(self.x - camx), int(self.y))))


class Level:
    def __init__(self, data):
        self.name = data["name"]
        self.theme = data["theme"]
        self.w = data["w"]
        self.h = data["h"]
        self.grid = [row[:] for row in data["grid"]]
        self.pixel_w = self.w * TILE
        self.pixel_h = self.h * TILE
        self.coins = []
        self.enemies = []
        self.powerups = []
        self.checkpoints = []
        self.start = (3, 12)
        self.flag_tile = None
        self.boss = None
        for y in range(self.h):
            for x in range(self.w):
                c = self.grid[y][x]
                if c == "o":
                    self.coins.append(Coin(x, y))
                    self.grid[y][x] = " "
                elif c == "E":
                    self.enemies.append(Enemy(x, y))
                    self.grid[y][x] = " "
                elif c == "W":
                    self.enemies.append(Bat(x, y))
                    self.grid[y][x] = " "
                elif c == "w":
                    self.enemies.append(Bat(x, y, variant="fire"))
                    self.grid[y][x] = " "
                elif c == "Z":
                    self.enemies.append(IceZombie(x, y))
                    self.grid[y][x] = " "
                elif c == "G":
                    self.enemies.append(Enemy(x, y, variant="green"))
                    self.grid[y][x] = " "
                elif c == "y":
                    self.enemies.append(Bat(x, y, variant="sky"))
                    self.grid[y][x] = " "
                elif c == "Q":
                    self.enemies.append(Necromancer(x, y, cloud=True))
                    self.grid[y][x] = " "
                elif c == "K":
                    self.enemies.append(Knight(x, y))
                    self.grid[y][x] = " "
                elif c == "N":
                    self.enemies.append(Necromancer(x, y))
                    self.grid[y][x] = " "
                elif c == "S":
                    self.enemies.append(Slime(x, y))
                    self.grid[y][x] = " "
                elif c == "C":
                    self.checkpoints.append(Checkpoint(x, y))
                    self.grid[y][x] = " "
                elif c == "P":
                    self.start = (x, y)
                    self.grid[y][x] = " "
                elif c == "F":
                    self.flag_tile = (x, y)
                    self.grid[y][x] = " "
        if data.get("boss"):
            b = data["boss"]
            self.boss = Boss(b.get("kind", "gilbert"), b["tx"], b["ty"],
                             b["left"] * TILE, b["right"] * TILE)
        self.pal = THEMES[self.theme]
        self.tile_surfs = {}
        for ch in ("#", "B", "?", "=", "p", "^", "L"):
            self.tile_surfs[ch] = make_tile(ch, self.pal)
        self.tile_surfs["#top"] = make_tile("#", self.pal, top=True)
        self.tile_surfs["M"] = self.tile_surfs["?"]
        self.tile_surfs["R"] = self.tile_surfs["?"]
        self.tile_surfs["X"] = make_tile("X", self.pal)

    def is_solid(self, tx, ty):
        if ty < 0 or ty >= self.h:
            return False
        if tx < 0 or tx >= self.w:
            return True
        return self.grid[ty][tx] in SOLID

    def solid_tiles(self, rect):
        out = []
        tx0 = int(rect.left // TILE)
        tx1 = int((rect.right - 1) // TILE)
        ty0 = int(rect.top // TILE)
        ty1 = int((rect.bottom - 1) // TILE)
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if self.is_solid(tx, ty):
                    out.append((tx, ty))
        return out

    def hazard_tiles(self, rect):
        out = []
        tx0 = int(rect.left // TILE)
        tx1 = int((rect.right - 1) // TILE)
        ty0 = int(rect.top // TILE)
        ty1 = int((rect.bottom - 1) // TILE)
        for ty in range(ty0, ty1 + 1):
            for tx in range(tx0, tx1 + 1):
                if 0 <= tx < self.w and 0 <= ty < self.h and self.grid[ty][tx] in ("^", "L"):
                    out.append((tx, ty))
        return out

    def bump(self, tx, ty, game):
        if not (0 <= tx < self.w and 0 <= ty < self.h):
            return
        c = self.grid[ty][tx]
        if c == "?":
            self.grid[ty][tx] = "X"
            game.coins += 1
            game.add_score(200, tx * TILE + TILE // 2, ty * TILE)
            game.sounds.play("coin")
            game.add_sparks(tx * TILE + TILE // 2, ty * TILE, game.pal["coin"])
            if game.coins % 50 == 0:
                game.lives += 1
                game.sounds.play("life")
                game.add_score(0, tx * TILE + TILE // 2, ty * TILE - 20)
        elif c == "M":
            self.grid[ty][tx] = "X"
            self.powerups.append(PowerUp(tx, ty - 1))
            game.sounds.play("powerup")
        elif c == "R":
            self.grid[ty][tx] = "X"
            self.powerups.append(PowerUp(tx, ty - 1, kind="ramen"))
            game.sounds.play("powerup")
        elif c in SOLID:
            game.sounds.play("bump")


def _blank(w, h=GRID_H):
    return [[" "] * w for _ in range(h)]


def _ground(g, x0, x1, top=13):
    for x in range(x0, x1):
        for y in range(top, GRID_H):
            g[y][x] = "#"


def _coins(g, x0, x1, y):
    for x in range(x0, x1):
        g[y][x] = "o"


def _row(g, x0, x1, y, ch):
    for x in range(x0, x1):
        g[y][x] = ch


def build_level_1():
    w = 210
    g = _blank(w)
    _ground(g, 0, 40)
    _ground(g, 44, 78)
    _ground(g, 82, 120)
    _ground(g, 124, 164)
    _ground(g, 168, w)
    g[12][3] = "P"

    _row(g, 10, 13, 9, "?")
    g[9][12] = "M"
    _row(g, 14, 16, 9, "?")
    _coins(g, 9, 16, 7)

    _row(g, 24, 28, 9, "B")
    _row(g, 25, 27, 6, "o")

    g[11][30] = "p"
    g[12][30] = "p"

    g[12][33] = "E"
    g[12][37] = "E"

    _row(g, 46, 52, 9, "=")
    _coins(g, 46, 52, 8)
    g[8][55] = "?"
    g[8][57] = "R"
    g[8][59] = "?"
    g[12][53] = "E"
    g[12][66] = "E"

    _row(g, 62, 68, 6, "B")
    _coins(g, 63, 67, 5)

    g[12][73] = "p"
    g[11][73] = "p"
    g[10][73] = "p"

    _row(g, 84, 92, 9, "=")
    _row(g, 90, 98, 5, "=")
    _coins(g, 90, 98, 4)
    g[12][86] = "E"
    g[12][100] = "E"
    g[12][104] = "E"
    g[8][94] = "?"
    g[8][96] = "M"

    _row(g, 108, 116, 8, "B")
    _coins(g, 108, 116, 7)

    _ground(g, 126, 164)
    g[12][130] = "E"
    g[12][140] = "E"
    _row(g, 134, 142, 6, "=")
    _coins(g, 134, 142, 5)
    g[9][146] = "?"
    g[9][148] = "?"
    g[9][150] = "?"

    g[12][170] = "E"
    g[11][174] = "p"
    g[12][174] = "p"
    _coins(g, 178, 184, 11)

    g[12][110] = "C"
    g[12][181] = "C"
    return {"name": "1-1  Sunny Meadow", "theme": 0, "w": w, "h": GRID_H, "grid": g,
            "boss": {"kind": "harvey", "tx": 196, "ty": 12, "left": 186, "right": 208}}


def build_level_2():
    w = 232
    g = _blank(w)
    _ground(g, 0, 33)
    _ground(g, 36, 62)
    _ground(g, 65, 98)
    _ground(g, 101, 136)
    _ground(g, 139, 174)
    _ground(g, 177, w)
    g[12][3] = "P"

    _row(g, 8, 11, 9, "?")
    g[9][12] = "M"
    _row(g, 14, 17, 9, "B")
    _coins(g, 8, 17, 7)
    g[12][26] = "E"

    _row(g, 42, 49, 10, "=")
    _coins(g, 42, 49, 9)
    g[9][52] = "?"
    g[12][55] = "E"

    _row(g, 68, 75, 10, "=")
    _coins(g, 68, 75, 9)
    _row(g, 78, 85, 8, "=")
    _coins(g, 78, 85, 7)
    g[9][90] = "R"
    for x in range(92, 94):
        g[12][x] = "^"
    g[12][80] = "E"

    _row(g, 106, 113, 10, "=")
    _coins(g, 106, 113, 9)
    g[9][118] = "M"
    g[9][120] = "?"
    g[12][126] = "p"
    g[11][126] = "p"
    g[12][104] = "E"

    _row(g, 142, 149, 10, "=")
    _coins(g, 142, 149, 9)
    for x in range(154, 156):
        g[12][x] = "^"
    _row(g, 160, 167, 9, "B")
    _coins(g, 160, 167, 8)
    g[12][150] = "E"

    g[12][182] = "E"

    g[12][84] = "C"
    g[12][185] = "C"
    _coins(g, 190, 197, 11)
    return {"name": "2-1  Crystal Caverns", "theme": 1, "w": w, "h": GRID_H, "grid": g,
            "boss": {"kind": "esmee", "tx": 213, "ty": 12, "left": 197, "right": 228}}


def build_level_3():
    w = 232
    g = _blank(w)
    _ground(g, 0, 37)
    _ground(g, 40, 75)
    _ground(g, 78, 113)
    _ground(g, 116, 151)
    _ground(g, 154, 189)
    _ground(g, 192, w)
    g[12][3] = "P"

    _row(g, 8, 12, 9, "?")
    g[9][11] = "M"
    _coins(g, 8, 12, 7)
    g[12][22] = "E"

    _row(g, 44, 50, 11, "=")
    _coins(g, 44, 50, 10)
    _row(g, 53, 59, 9, "=")
    _coins(g, 53, 59, 8)
    _row(g, 62, 68, 7, "=")
    _coins(g, 62, 68, 6)
    g[12][70] = "E"

    g[9][82] = "R"
    _row(g, 86, 92, 10, "=")
    _coins(g, 86, 92, 9)
    for x in range(96, 98):
        g[12][x] = "^"
    g[12][84] = "E"
    g[12][104] = "E"

    _row(g, 120, 126, 9, "B")
    g[9][122] = "M"
    _row(g, 130, 136, 10, "=")
    _coins(g, 130, 136, 9)
    g[12][144] = "E"

    _row(g, 158, 164, 10, "=")
    _coins(g, 158, 164, 9)
    for x in range(168, 170):
        g[12][x] = "^"
    _row(g, 172, 178, 9, "B")
    _coins(g, 172, 178, 8)
    g[12][184] = "E"

    _row(g, 190, 196, 9, "=")
    _coins(g, 190, 196, 8)

    g[12][108] = "C"
    g[12][182] = "C"
    _coins(g, 198, 206, 11)
    return {"name": "3-1  Sunset Summits", "theme": 2, "w": w, "h": GRID_H, "grid": g,
            "boss": {"kind": "laycan", "tx": 210, "ty": 12, "left": 194, "right": 224}}


def build_level_4():
    w = 196
    g = _blank(w)
    _ground(g, 0, 40)
    _ground(g, 44, 80)
    _ground(g, 84, 120)
    _ground(g, 124, w)
    g[12][3] = "P"

    _row(g, 8, 12, 9, "?")
    g[9][11] = "M"
    _coins(g, 8, 12, 7)
    g[7][18] = "W"
    g[12][26] = "E"

    _row(g, 14, 18, 9, "B")
    _row(g, 15, 17, 6, "o")
    g[6][34] = "W"
    _row(g, 30, 36, 9, "=")
    _coins(g, 30, 36, 8)

    _row(g, 48, 54, 8, "=")
    _coins(g, 48, 54, 7)
    g[9][60] = "R"
    g[7][58] = "W"
    g[12][64] = "E"

    _row(g, 68, 74, 9, "=")
    _coins(g, 68, 74, 8)

    _row(g, 90, 96, 8, "=")
    _coins(g, 90, 96, 7)
    g[9][100] = "?"
    g[9][112] = "W"
    g[12][108] = "E"

    _row(g, 132, 142, 10, "=")
    _coins(g, 132, 142, 9)
    g[12][138] = "E"

    for x in range(192, 196):
        for y in range(6, 13):
            g[y][x] = "#"
    g[9][152] = "?"
    g[9][158] = "M"
    _coins(g, 148, 156, 11)

    g[12][100] = "C"
    g[12][146] = "C"
    return {"name": "4-1  Gilbert's Glacier", "theme": 3, "w": w, "h": GRID_H,
            "grid": g, "boss": {"kind": "gilbert", "tx": 176, "ty": 12, "left": 150, "right": 191}}


def build_level_5():
    w = 244
    g = _blank(w)
    segs = [(0, 36), (40, 76), (80, 116), (120, 156), (160, 196), (200, w)]
    for (a, b) in segs:
        _ground(g, a, b)
    for (a, b) in zip(segs[:-1], segs[1:]):
        for x in range(a[1], b[0]):
            for y in range(13, GRID_H):
                g[y][x] = "L"
    g[12][3] = "P"

    _row(g, 8, 12, 9, "?")
    g[9][11] = "M"
    _coins(g, 8, 12, 7)
    g[12][24] = "E"
    g[7][30] = "w"

    _row(g, 42, 48, 10, "=")
    _coins(g, 42, 48, 9)
    g[9][52] = "R"
    g[12][60] = "Z"
    g[7][66] = "w"

    _row(g, 82, 88, 9, "=")
    _coins(g, 82, 88, 8)
    g[9][92] = "?"
    g[12][100] = "E"
    g[6][104] = "w"

    _row(g, 122, 128, 10, "=")
    _coins(g, 122, 128, 9)
    g[12][132] = "Z"
    _row(g, 136, 142, 7, "B")
    _coins(g, 136, 142, 6)

    _row(g, 162, 168, 9, "=")
    _coins(g, 162, 168, 8)
    g[9][172] = "M"
    g[12][180] = "E"
    g[6][184] = "w"

    _row(g, 200, 208, 8, "=")
    _coins(g, 200, 208, 7)
    g[9][212] = "?"

    g[12][90] = "C"
    g[12][205] = "C"
    return {"name": "5-1  Lava Castle", "theme": 4, "w": w, "h": GRID_H, "grid": g,
            "boss": {"kind": "mech", "tx": 228, "ty": 12, "left": 216, "right": 240}}


def build_level_6():
    w = 212
    g = _blank(w)
    _ground(g, 0, 40)
    _ground(g, 44, 84)
    _ground(g, 88, 128)
    _ground(g, 132, 172)
    _ground(g, 176, w)
    g[12][3] = "P"

    _row(g, 8, 12, 9, "?")
    g[9][11] = "M"
    _coins(g, 8, 12, 7)
    g[12][24] = "K"
    g[9][30] = "?"

    _row(g, 44, 50, 10, "=")
    _coins(g, 44, 50, 9)
    g[12][54] = "N"
    g[12][64] = "K"

    _row(g, 88, 94, 9, "=")
    _coins(g, 88, 94, 8)
    g[9][98] = "R"
    g[12][104] = "K"
    g[12][112] = "N"

    _row(g, 132, 140, 10, "=")
    _coins(g, 132, 140, 9)
    g[12][146] = "K"
    _coins(g, 150, 160, 11)

    g[12][90] = "C"
    g[12][178] = "C"
    return {"name": "6-1  theres more?", "theme": 5, "w": w, "h": GRID_H, "grid": g,
            "boss": {"kind": "bob", "tx": 198, "ty": 12, "left": 190, "right": 206}}


CLOUD_LEVEL_NAMES = [
    "W2-1  Cumulus Cove",
    "W2-2  Nimbus Heights",
    "W2-3  Stratus Steps",
    "W2-4  Cirrus Cliffs",
    "W2-5  The Thunderhead",
]


def build_cloud_level(n):
    w = 168 + n * 12
    g = _blank(w)
    segs = [(0, 30), (34, 70), (74, 110), (114, 150), (154, w)]
    for (a, b) in segs:
        _ground(g, a, b)
    g[12][3] = "P"

    _row(g, 8, 12, 9, "?")
    g[9][11] = "M"
    _coins(g, 8, 12, 7)
    g[12][22] = "G"           # green grump
    g[7][26] = "y"            # sky bat

    _row(g, 44, 50, 9, "=")
    _coins(g, 44, 50, 8)
    g[12][62] = "G"
    g[7][58] = "y"

    g[12][84] = "Q"           # cloud necromancer
    _row(g, 84, 92, 8, "=")
    g[9][90] = "R"
    g[7][96] = "y"

    _row(g, 126, 134, 9, "=")
    _coins(g, 126, 134, 8)
    g[12][124] = "G"
    g[6][130] = "y"
    g[9][140] = "?"

    _coins(g, 156, 166, 11)

    g[12][40] = "C"
    g[12][120] = "C"
    g[12][w - 6] = "F"        # goal flag
    return {"name": CLOUD_LEVEL_NAMES[n - 1], "theme": 6, "w": w, "h": GRID_H, "grid": g}


class Game:
    def __init__(self, screen, audio):
        self.screen = screen
        self.sounds = SoundBank(audio)
        self.fonts = {}
        self.levels = [build_level_1(), build_level_2(), build_level_3(),
                       build_level_4(), build_level_5(), build_level_6(),
                       build_cloud_level(1), build_cloud_level(2), build_cloud_level(3),
                       build_cloud_level(4), build_cloud_level(5)]
        self.state = "title"
        self.level_index = 0
        self.level = None
        self.player = None
        self.camera = Camera()
        self.score = 0
        self.coins = 0
        self.lives = START_LIVES
        self.sparks = []
        self.floats = []
        self.time = 0
        self.timer = 0
        self.paused = False
        self.boss_done = False
        self.mushrooms = 0
        self.ramen_shots = []
        self.enemy_shots = []
        self.shoot_cd = 0
        self.pal = THEMES[0]
        self.bg = make_gradient(THEMES[0]["sky_top"], THEMES[0]["sky_bot"], W, H)
        self.clouds = []
        for i in range(9):
            self.clouds.append([random.randint(0, 1400), random.randint(40, 300),
                                random.uniform(0.4, 1.1)])
        self.sounds.music("menu")
        self.title_anim = 0.0

    def get_font(self, size, bold=True):
        key = (size, bold)
        if key not in self.fonts:
            try:
                self.fonts[key] = pygame.font.SysFont("consolas", size, bold=bold)
            except Exception:
                self.fonts[key] = pygame.font.Font(None, size)
        return self.fonts[key]

    def start_game(self):
        self.score = 0
        self.coins = 0
        self.lives = START_LIVES
        self.mushrooms = 0
        self.start_level(0)

    def start_level(self, index):
        self.level_index = index
        self.lives = START_LIVES
        self.checkpoint = None
        self.level = Level(self.levels[index])
        self.pal = self.level.pal
        self.bg = make_gradient(self.pal["sky_top"], self.pal["sky_bot"], W, H)
        self.player = Player(*self.level.start)
        self.player.skin = index
        self.camera.x = clamp(self.player.rect().centerx - W * 0.42, 0,
                              max(0, self.level.pixel_w - W))
        self.sparks = []
        self.floats = []
        self.timer = 0
        self.paused = False
        self.boss_done = False
        self.ramen_shots = []
        self.enemy_shots = []
        self.shoot_cd = 0
        self.state = "play"
        self.sounds.music("game")

    def reset_level(self):
        self.level = Level(self.levels[self.level_index])
        spawn = self.level.start
        if self.checkpoint:
            spawn = self.checkpoint
            for cp in self.level.checkpoints:
                if (cp.tx, cp.ty) == self.checkpoint:
                    cp.active = True
        self.player = Player(*spawn)
        self.player.skin = self.level_index
        if self.checkpoint:
            self.player.grow()
        self.camera.x = clamp(self.player.rect().centerx - W * 0.42, 0,
                              max(0, self.level.pixel_w - W))
        self.sparks = []
        self.floats = []
        self.state = "play"
        self.paused = False
        self.boss_done = False
        self.ramen_shots = []
        self.enemy_shots = []
        self.shoot_cd = 0
        self.sounds.music("game")

    def add_score(self, amount, x, y, color=(255, 255, 255)):
        self.score += amount
        if amount:
            self.floats.append(FloatText(str(amount), x, y, color))

    def add_sparks(self, x, y, color):
        for _ in range(8):
            self.sparks.append(Spark(x, y, color))

    def recall_mushroom(self):
        if self.state != "play" or self.paused or self.mushrooms <= 0:
            return
        self.mushrooms -= 1
        p = self.player
        self.level.powerups.append(PowerUp.sky_at(p.rect().centerx, kind="mushroom"))
        self.floats.append(FloatText("MUSHROOM!",
                                     p.rect().centerx, p.rect().top - 10, (255, 240, 180)))
        self.sounds.play("powerup")

    def build_arena_walls(self, boss):
        lvl = self.level
        pr = self.player.rect()
        left_tx = int(boss.arena_left) // TILE - 1
        right_tx = int(boss.arena_right) // TILE
        for tx in (left_tx, right_tx):
            for ty in range(4, 13):
                if not (0 <= tx < lvl.w):
                    continue
                if lvl.grid[ty][tx] != " ":
                    continue
                cell = pygame.Rect(tx * TILE, ty * TILE, TILE, TILE)
                if cell.colliderect(pr):
                    continue
                lvl.grid[ty][tx] = "B"
        self.sounds.play("bump")
        self.floats.append(FloatText("THE ARENA SEALS!",
                                     (left_tx + right_tx) * TILE // 2, 130,
                                     (255, 130, 110)))

    def level_clear(self):
        if self.state == "play":
            self.state = "levelclear"
            self.timer = 160
            self.sounds.play("win")

    def advance_level(self):
        if self.level_index + 1 < len(self.levels):
            self.start_level(self.level_index + 1)
        else:
            self.state = "win"
            self.timer = 0
            self.sounds.music("menu")

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.state = "gameover"
            self.sounds.music("menu")
        else:
            self.reset_level()

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            pygame.event.post(pygame.event.Event(pygame.QUIT))
            return
        if e.type != pygame.KEYDOWN:
            return
        k = e.key
        if k == pygame.K_m:
            self.sounds.toggle_mute()
        if self.state == "title":
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_game()
            elif k == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
        elif self.state == "play":
            if k in (pygame.K_ESCAPE, pygame.K_p):
                self.paused = not self.paused
            elif k == pygame.K_e:
                self.recall_mushroom()
        elif self.state == "levelclear":
            self.advance_level()
        elif self.state in ("gameover", "win"):
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.state = "title"
                self.sounds.music("menu")
        if self.paused and k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.paused = False

    def update(self, keys):
        self.time += 1
        self.title_anim += 0.05
        for s in self.sparks:
            s.update()
        self.sparks = [s for s in self.sparks if s.life > 0]
        for f in self.floats:
            f.update()
        self.floats = [f for f in self.floats if f.life > 0]

        if self.state == "levelclear":
            self.timer -= 1
            if self.timer <= 0:
                self.advance_level()
            return
        if self.state != "play" or self.paused:
            return

        p = self.player
        p.bumped = []
        p.update(keys, self.level, self.sounds)
        for (tx, ty) in p.bumped:
            self.level.bump(tx, ty, self)

        for e in self.level.enemies:
            e.update(self.level, p, self)
        boss = self.level.boss
        if boss:
            boss.update(p, self)
            if boss.active and not boss.walls_built:
                self.build_arena_walls(boss)
                boss.walls_built = True
            if boss.active and not boss.dead:
                self.sounds.music("boss")
        for c in self.level.coins:
            c.update()
        for pu in self.level.powerups:
            pu.update(self.level)

        pr = p.rect()

        if p.dying:
            if p.y > self.level.pixel_h + 140:
                self.lose_life()
            else:
                self.camera.update(p, self.level)
            return

        for cp in self.level.checkpoints:
            if not cp.active and pr.colliderect(cp.rect()):
                cp.active = True
                self.checkpoint = cp.spawn()
                self.lives += 1
                self.sounds.play("checkpoint")
                self.add_sparks(cp.rect().centerx, cp.rect().bottom - 20, (120, 255, 170))
                self.floats.append(FloatText("+1 LIFE - CHECKPOINT!",
                                             cp.rect().centerx, cp.rect().top,
                                             (150, 255, 190)))

        for pu in list(self.level.powerups):
            if pr.colliderect(pu.rect()):
                self.level.powerups.remove(pu)
                if pu.kind == "ramen":
                    p.ramen = True
                    self.floats.append(FloatText("RAMEN POWER!",
                                                 pu.rect().centerx, pu.rect().centery,
                                                 (255, 220, 150)))
                else:
                    if not p.big:
                        p.grow()
                    else:
                        self.mushrooms += 1
                        self.floats.append(FloatText("+1 MUSHROOM (E)",
                                                     pu.rect().centerx, pu.rect().centery,
                                                     (255, 240, 180)))
                self.add_score(1000, pu.rect().centerx, pu.rect().centery, (255, 230, 120))
                self.add_sparks(pu.rect().centerx, pu.rect().centery, (255, 240, 180))
                self.sounds.play("powerup")

        if self.shoot_cd > 0:
            self.shoot_cd -= 1
        if p.shoot and p.ramen and self.shoot_cd <= 0:
            self.shoot_cd = RAMEN_SHOOT_COOLDOWN
            muzzle_x = p.rect().centerx + p.facing * 18
            muzzle_y = p.rect().centery - 4
            self.ramen_shots.append(Ramen(muzzle_x, muzzle_y,
                                          p.facing * 7.2, -4.2))
            self.sounds.play("bump")
        for shot in self.ramen_shots:
            shot.update(self.level)
        for shot in list(self.ramen_shots):
            sr = shot.rect()
            for e in self.level.enemies:
                if e.state == "walk" and sr.colliderect(e.rect()):
                    e.squash()
                    shot.life = 0
                    self.add_score(200, e.rect().centerx, e.rect().top, (255, 220, 160))
                    self.sounds.play("stomp")
                    break
            if shot.life <= 0:
                continue
            if boss and boss.active and not boss.dead and sr.colliderect(boss.rect()):
                boss.damage(6, self)
                shot.life = 0
                self.add_score(50, sr.centerx, sr.centery, (255, 220, 160))
                self.sounds.play("stomp")
        self.ramen_shots = [s for s in self.ramen_shots if s.life > 0]

        for es in self.enemy_shots:
            es.update(self.level)
        for es in list(self.enemy_shots):
            if pr.colliderect(es.rect()):
                self.enemy_shots.remove(es)
                p.hurt(self.sounds)     # fireballs cannot be parried
        self.enemy_shots = [s for s in self.enemy_shots if s.life > 0]

        for c in list(self.level.coins):
            if pr.colliderect(c.rect()):
                self.level.coins.remove(c)
                self.coins += 1
                self.add_score(100, c.rect().centerx, c.rect().centery, self.pal["coin"])
                self.sounds.play("coin")
                self.add_sparks(c.rect().centerx, c.rect().centery, self.pal["coin"])
                if self.coins % 50 == 0:
                    self.lives += 1
                    self.sounds.play("life")

        for e in self.level.enemies:
            if e.state != "walk":
                continue
            er = e.rect()
            if pr.colliderect(er):
                falling = p.vy > 0
                from_above = (pr.bottom - er.top) < 22
                if falling and from_above:
                    e.squash()
                    p.vy = STOMP_BOUNCE
                    self.add_score(200, er.centerx, er.top, (200, 255, 220))
                    self.add_sparks(er.centerx, er.top, (180, 255, 210))
                    self.sounds.play("stomp")
                elif isinstance(e, Bat) and e.variant == "sky":
                    away = 1 if pr.centerx >= er.centerx else -1
                    p.xs = 24 * away
                    p.facing = away
                    p.vx = p.xs * SMB_SCALE / 16.0
                    p.on_ground = False
                    self.add_sparks(er.centerx, er.centery, (220, 235, 255))
                    self.sounds.play("bump")
                else:
                    p.hurt(self.sounds)

        for e in self.level.enemies:
            if isinstance(e, Knight) and e.hit_active:
                if pr.colliderect(e.sword_rect()):
                    p.hurt(self.sounds)

        if boss and boss.active and not boss.dead:
            br = boss.rect()
            if pr.colliderect(br):
                if p.vy > 0 and (pr.bottom - br.top) < 48 and boss.vulnerable:
                    boss.damage(boss.stomp_damage, self)
                    p.vy = STOMP_BOUNCE
                    away = 1 if pr.centerx >= br.centerx else -1
                    p.xs = BOSS_BOUNCE_X * away
                    p.facing = away
                    p.vx = p.xs * SMB_SCALE / 16.0
                    p.on_ground = False
                    self.add_score(50, br.centerx, br.top, (255, 240, 180))
                    self.add_sparks(br.centerx, br.top, (200, 235, 255))
                    self.sounds.play("stomp")
                else:
                    p.hurt(self.sounds)
            for sb in list(boss.shots):
                sbr = sb.rect()
                if pr.colliderect(sbr):
                    boss.shots.remove(sb)
                    on_top = (p.vy > 0 and (pr.bottom - sbr.top) < 22
                              and getattr(sb, "parryable", True))
                    if on_top:
                        p.double_jump()
                        p.flip = PARRY_FLIP_FRAMES
                        self.add_sparks(sbr.centerx, sbr.centery, (150, 230, 255))
                        self.floats.append(FloatText("PARRY!",
                                                     sbr.centerx, sbr.centery,
                                                     (150, 230, 255)))
                        self.sounds.play("jump")
                    else:
                        p.hurt(self.sounds)

        if boss and boss.dead and boss.dead_timer <= 0 and not self.boss_done:
            self.boss_done = True
            self.sounds.music("game")
            self.add_score(5000, boss.rect().centerx, boss.rect().top, (255, 230, 120))
            self.level_clear()
            return

        hz = self.level.hazard_tiles(pr)
        if hz:
            p.hurt(self.sounds)

        if self.level.flag_tile:
            fx = self.level.flag_tile[0] * TILE + 10
            if pr.right >= fx:
                self.level_clear()
                return

        if p.y > self.level.pixel_h + 40 and not p.dying:
            p.die(self.sounds)

        if p.dying and p.y > self.level.pixel_h + 140:
            self.lose_life()
            return

        self.level.enemies = [e for e in self.level.enemies if e.state != "dead"]
        self.camera.update(p, self.level)

    def draw_text(self, text, size, color, center=None, topleft=None, bold=True, shadow=True):
        font = self.get_font(size, bold)
        img = font.render(text, True, color)
        rect = img.get_rect()
        if center:
            rect.center = center
        elif topleft:
            rect.topleft = topleft
        if shadow:
            sh = font.render(text, True, (0, 0, 0))
            self.screen.blit(sh, (rect.x + 2, rect.y + 2))
        self.screen.blit(img, rect)
        return rect

    def draw_background(self):
        self.screen.blit(self.bg, (0, 0))
        if self.level.theme == 1:
            for i in range(14):
                tx = (i * 160 - int(self.camera.x * 0.4)) % (self.level.pixel_w + 300) - 100
                pygame.draw.polygon(self.screen, (34, 26, 62), [
                    (tx, 0), (tx + 26, 0), (tx + 13, 90)])
            for i in range(18):
                cx = (i * 137 + int(self.camera.x * 0.2)) % W
                cy = 120 + (i * 53) % 300
                r = 2 + (i % 3)
                pygame.draw.circle(self.screen, (150, 120, 220), (cx, cy), r)
            return
        if self.level.theme == 4:
            # distant castle silhouette + rising embers + lava glow
            for i in range(10):
                bx = (i * 300 - int(self.camera.x * 0.3)) % (self.level.pixel_w + 400) - 200
                pygame.draw.rect(self.screen, (58, 22, 30), (bx, H - 300, 140, 300))
                pygame.draw.polygon(self.screen, (58, 22, 30), [
                    (bx - 10, H - 300), (bx + 70, H - 360), (bx + 150, H - 300)])
            glow = pygame.Surface((W, 160), pygame.SRCALPHA)
            for gy in range(160):
                a = int(90 * (gy / 160.0))
                pygame.draw.line(glow, (255, 120, 40, a), (0, gy), (W, gy))
            self.screen.blit(glow, (0, H - 160))
            for i in range(60):
                sx = (i * 91 + int(self.camera.x * 0.4)) % W
                sy = H - ((i * 53 + self.time * (2 + i % 3)) % (H + 40))
                pygame.draw.circle(self.screen, (255, 150 + (i % 3) * 30, 60), (sx, sy),
                                   2 if i % 2 else 1)
            return
        if self.level.theme == 5:
            # monochrome void: faint grid lines + drifting static squares
            for i in range(0, W + TILE, TILE):
                x = (i - int(self.camera.x * 0.2)) % (W + TILE)
                pygame.draw.line(self.screen, (34, 34, 34), (x, 0), (x, H), 1)
            for i in range(26):
                sx = (i * 143 + int(self.camera.x * 0.5) + self.time) % W
                sy = (i * 89 + self.time * (1 + i % 2)) % H
                sz = 6 + (i % 4) * 5
                pygame.draw.rect(self.screen, (90, 90, 90), (sx, sy, sz, sz), 1)
            return
        if self.level.theme == 6:
            # fluffy cloud layers
            for layer, (ox, cy, sc) in enumerate(((0.15, 150, 1.6), (0.3, 320, 2.2), (0.5, 470, 2.8))):
                for i in range(-1, 8):
                    x = i * int(320 * sc) - int(self.camera.x * ox) % int(320 * sc) + 60
                    c = (252, 254, 255) if layer else (240, 248, 255)
                    pygame.draw.ellipse(self.screen, c, (x, cy - int(30 * sc), int(150 * sc), int(56 * sc)))
                    pygame.draw.ellipse(self.screen, c, (x + int(60 * sc), cy - int(50 * sc), int(120 * sc), int(70 * sc)))
                    pygame.draw.ellipse(self.screen, c, (x + int(140 * sc), cy - int(24 * sc), int(130 * sc), int(52 * sc)))
            return
        ox = self.camera.x * 0.25
        for i in range(-1, 12):
            x = i * 240 - int(ox % 240)
            pygame.draw.circle(self.screen, self.pal["hill2"], (x, H - 20), 170)
        ox = self.camera.x * 0.4
        for i in range(-1, 12):
            x = i * 300 - int(ox % 300) + 120
            pygame.draw.circle(self.screen, self.pal["hill"], (x, H - 10), 140)
        ox = self.camera.x * 0.15 + self.time * 0.15
        for c in self.clouds:
            cx = (c[0] - ox * c[2]) % (self.level.pixel_w + 400) - 200
            cy = c[1]
            col = (255, 255, 255)
            pygame.draw.ellipse(self.screen, col, (cx, cy, 110, 44))
            pygame.draw.ellipse(self.screen, col, (cx + 30, cy - 18, 90, 50))
            pygame.draw.ellipse(self.screen, col, (cx + 70, cy, 90, 40))
        if self.level.theme == 3:
            for i in range(70):
                sx = (i * 97 + int(self.camera.x * 0.3) + self.time * 2) % W
                sy = (i * 53 + self.time * (1 + i % 3)) % H
                pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy),
                                   2 if i % 2 else 1)

    def draw_world(self):
        self.draw_background()
        camx = self.camera.ix()
        lvl = self.level
        tx0 = max(0, camx // TILE)
        tx1 = min(lvl.w, (camx + W) // TILE + 1)
        for ty in range(lvl.h):
            for tx in range(tx0, tx1):
                ch = lvl.grid[ty][tx]
                if ch == " ":
                    continue
                if ch == "#":
                    surf = lvl.tile_surfs["#top" if not lvl.is_solid(tx, ty - 1) else "#"]
                else:
                    surf = lvl.tile_surfs.get(ch)
                if surf:
                    self.screen.blit(surf, (tx * TILE - camx, ty * TILE))

        self.draw_flag(camx)
        self.draw_checkpoints(camx)

        for c in lvl.coins:
            self.draw_coin(c, camx)
        for pu in lvl.powerups:
            self.screen.blit(pu.render(), (pu.rect().x - camx, pu.rect().y))
        for shot in self.ramen_shots:
            r = shot.rect()
            self.screen.blit(shot.render(), (r.x - camx, r.y))
        for es in self.enemy_shots:
            r = es.rect()
            self.screen.blit(es.render(), (r.x - camx, r.y))

        for e in lvl.enemies:
            r = e.rect()
            self.screen.blit(e.render(), (r.x - camx, r.y))

        boss = lvl.boss
        if boss:
            for sb in boss.shots:
                r = sb.rect()
                self.screen.blit(sb.render(), (r.x - camx, r.y))
            r = boss.sprite_rect()
            self.screen.blit(boss.render(), (r.x - camx, r.y))
            if boss.state == "warn" and not boss.dead:
                self.draw_boss_warning(r.centerx - camx, max(26, r.top - 24))

        p = self.player
        if p.invuln > 0 and (self.time // 4) % 2 == 0:
            pass
        else:
            moving = abs(p.vx) > 0.3
            img = render_vihaan(p.w, p.h, p.facing, p.big, p.walk, moving,
                                p.on_ground, p.vy, p.vx, self.time, p.skin)
            pr = p.rect()
            if p.flip > 0:
                progress = 1.0 - p.flip / float(PARRY_FLIP_FRAMES)
                img = pygame.transform.rotate(img, 360.0 * progress * p.facing)
                self.screen.blit(img, img.get_rect(center=(pr.centerx - camx, pr.centery)))
            else:
                self.screen.blit(img, (pr.x - camx, pr.y))

        for s in self.sparks:
            s.draw(self.screen, camx)
        for f in self.floats:
            f.draw(self.screen, camx, self.get_font(20))

        self.draw_hud()

    def draw_coin(self, c, camx):
        cx = c.x + c.w // 2 - camx
        cy = c.y + c.h // 2
        phase = (c.t // 7) % 4
        widths = (18, 11, 3, 11)
        ww = widths[phase]
        pygame.draw.ellipse(self.screen, self.pal["coin"], (cx - ww // 2, cy - 11, ww, 22))
        if ww > 5:
            pygame.draw.ellipse(self.screen, self.pal["coin_hi"], (cx - ww // 2 + 2, cy - 8, max(1, ww - 4), 16))

    def draw_flag(self, camx):
        if not self.level.flag_tile:
            return
        tx, ty = self.level.flag_tile
        base_y = (ty + 1) * TILE
        top_y = base_y - 5 * TILE
        x = tx * TILE + 16 - camx
        pygame.draw.rect(self.screen, (200, 200, 210), (x, top_y, 6, 5 * TILE))
        pygame.draw.circle(self.screen, (255, 214, 90), (x + 3, top_y - 6), 8)
        col = (232, 86, 74) if self.level.theme != 1 else (180, 130, 240)
        pygame.draw.polygon(self.screen, col, [
            (x + 6, top_y + 10), (x + 6 + 46, top_y + 28), (x + 6, top_y + 46)])
        pygame.draw.polygon(self.screen, (255, 255, 255), [
            (x + 6, top_y + 10), (x + 6 + 46, top_y + 28), (x + 6, top_y + 46)], 2)

    def draw_checkpoints(self, camx):
        for cp in self.level.checkpoints:
            base_y = (cp.ty + 1) * TILE
            top_y = base_y - 4 * TILE
            x = cp.tx * TILE + 16 - camx
            pygame.draw.rect(self.screen, (188, 190, 200), (x, top_y, 6, 4 * TILE))
            pygame.draw.circle(self.screen, (255, 214, 90), (x + 3, top_y - 5), 7)
            wave = int(math.sin(self.time * 0.15) * 3) if cp.active else 0
            if cp.active:
                col = (86, 220, 120)
                pts = [(x + 6, top_y + 8), (x + 6 + 42, top_y + 22 + wave), (x + 6, top_y + 36)]
            else:
                col = (150, 152, 164)
                pts = [(x + 6, top_y + 22), (x + 6 + 30, top_y + 30), (x + 6, top_y + 38)]
            pygame.draw.polygon(self.screen, col, pts)
            pygame.draw.polygon(self.screen, (255, 255, 255), pts, 2)

    def draw_boss_warning(self, cx, top_y):
        bob = int(math.sin(self.time * 0.4) * 3)
        y = top_y + bob
        pygame.draw.rect(self.screen, (255, 255, 255), (cx - 5, y - 11, 10, 20), border_radius=3)
        pygame.draw.rect(self.screen, (232, 62, 54), (cx - 3, y - 9, 6, 15), border_radius=2)
        pygame.draw.circle(self.screen, (255, 255, 255), (cx, y + 13), 5)
        pygame.draw.circle(self.screen, (232, 62, 54), (cx, y + 13), 4)

    def draw_heart(self, cx, cy, filled, size=9):
        col = (232, 60, 72) if filled else (78, 70, 76)
        if filled:
            pygame.draw.circle(self.screen, col, (cx - size // 2, cy), size // 2 + 1)
            pygame.draw.circle(self.screen, col, (cx + size // 2, cy), size // 2 + 1)
            pygame.draw.polygon(self.screen, col, [
                (cx - size, cy + 1), (cx + size, cy + 1), (cx, cy + size + 3)])
        else:
            pygame.draw.circle(self.screen, col, (cx - size // 2, cy), size // 2 + 1, 2)
            pygame.draw.circle(self.screen, col, (cx + size // 2, cy), size // 2 + 1, 2)
            pygame.draw.polygon(self.screen, col, [
                (cx - size, cy + 1), (cx + size, cy + 1), (cx, cy + size + 3)], 2)

    def draw_hud(self):
        pygame.draw.rect(self.screen, (0, 0, 0, 90), (0, 0, W, 46))
        self.draw_text("VIHAAN  x%d" % self.lives, 24, (255, 240, 200), topleft=(14, 10))
        if self.player:
            for i in range(PLAYER_START_HEARTS):
                self.draw_heart(190 + i * 24, 21, i < self.player.hearts)
        self.draw_text("COINS %02d" % self.coins, 24, self.pal["coin"], topleft=(300, 10))
        self.draw_text("SCORE %06d" % self.score, 24, (255, 255, 255), topleft=(500, 10))
        self.draw_text("SHROOMS %d" % self.mushrooms, 22, (255, 230, 180), topleft=(760, 12))
        self.draw_text(self.level.name, 18, self.pal["accent"], topleft=(14, 50))
        if self.player and self.player.ramen:
            self.draw_text("RAMEN!  RUN = throw", 18,
                           (255, 214, 120), topleft=(690, 50))
        boss = self.level.boss
        if boss and boss.active and not boss.dead:
            bw, bh = 360, 22
            bx = (W - bw) // 2
            by = 56
            pygame.draw.rect(self.screen, (20, 20, 30), (bx - 3, by - 3, bw + 6, bh + 6), border_radius=6)
            pygame.draw.rect(self.screen, (90, 40, 50), (bx, by, bw, bh), border_radius=4)
            frac = max(0.0, boss.hp / float(boss.max_hp))
            if frac > 0:
                pygame.draw.rect(self.screen, (230, 60, 70), (bx, by, int(bw * frac), bh),
                                 border_radius=4)
            pygame.draw.rect(self.screen, (255, 255, 255), (bx, by, bw, bh), 2, border_radius=4)
            self.draw_text("%s   %d/%d" % (boss.name.upper(), boss.hp, boss.max_hp), 20,
                           (255, 255, 255), center=(W // 2, by + bh + 16))

    def draw_title(self):
        self.screen.blit(self.bg, (0, 0))
        for c in self.clouds:
            cx = (c[0] + self.time * 0.4 * c[2]) % (W + 300) - 150
            cy = c[1]
            pygame.draw.ellipse(self.screen, (255, 255, 255), (cx, cy, 110, 44))
            pygame.draw.ellipse(self.screen, (255, 255, 255), (cx + 30, cy - 18, 90, 50))
        bob = math.sin(self.title_anim) * 10
        big = render_vihaan(90, 130, 1, True, 0.0, False, True, 0.0, 0.0, self.time)
        self.screen.blit(big, big.get_rect(center=(W // 2, 250 + bob)))
        self.draw_text("VIHAAN", 96, (255, 214, 90), center=(W // 2, 120))
        self.draw_text("ADVENTURES", 60, (255, 120, 96), center=(W // 2, 188))
        self.draw_text("A platforming quest for Vihaan", 28, (40, 40, 60), center=(W // 2, 380))
        self.draw_text("PRESS ENTER TO START", 34, (255, 255, 255), center=(W // 2, 450))
        self.draw_text("KEYBOARD: Arrows / WASD move    SPACE jump    SHIFT run", 19,
                       (30, 30, 50), center=(W // 2, 500))
        self.draw_text("GAMEPAD: Stick / D-pad move    A jump    X run    Start confirm", 19,
                       (30, 30, 50), center=(W // 2, 528))
        self.draw_text("E = recall stored mushroom      SHIFT = throw ramen (with RAMEN power)", 19,
                       (30, 30, 50), center=(W // 2, 556))
        self.draw_text("P pause    M mute    ESC quit", 19,
                       (30, 30, 50), center=(W // 2, 584))
        self.draw_text("Stomp foes, store mushrooms, slurp ramen, beat the bosses!", 19,
                       (30, 30, 50), center=(W // 2, 616))

    def draw_overlay(self):
        veil = pygame.Surface((W, H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        self.screen.blit(veil, (0, 0))

    def draw(self):
        if self.state == "title":
            self.draw_title()
            return
        self.draw_world()
        if self.state == "levelclear":
            self.draw_overlay()
            self.draw_text("LEVEL CLEAR!", 72, (255, 226, 120), center=(W // 2, 220))
            self.draw_text("Score  %06d" % self.score, 36, (255, 255, 255), center=(W // 2, 310))
            self.draw_text("Press ENTER for the next stage", 28, (220, 240, 255), center=(W // 2, 380))
        elif self.state == "gameover":
            self.draw_overlay()
            self.draw_text("GAME OVER", 80, (255, 90, 90), center=(W // 2, 240))
            self.draw_text("Final score  %06d" % self.score, 36, (255, 255, 255), center=(W // 2, 330))
            self.draw_text("Press ENTER to return to the title", 28, (220, 240, 255), center=(W // 2, 400))
        elif self.state == "win":
            self.draw_overlay()
            self.draw_text("YOU WIN!", 84, (255, 226, 120), center=(W // 2, 200))
            self.draw_text("Vihaan conquered every stage!", 34, (255, 255, 255), center=(W // 2, 290))
            self.draw_text("Final score  %06d" % self.score, 40, (150, 255, 200), center=(W // 2, 360))
            self.draw_text("Press ENTER to play again", 28, (220, 240, 255), center=(W // 2, 430))
        elif self.paused:
            self.draw_overlay()
            self.draw_text("PAUSED", 80, (255, 255, 255), center=(W // 2, 280))
            self.draw_text("Press P or ENTER to resume", 28, (220, 240, 255), center=(W // 2, 360))


class Keys:
    def __init__(self, pressed):
        self.pressed = set(pressed)

    def __getitem__(self, k):
        return k in self.pressed


PAD_HORIZONTAL_AXIS = 0
PAD_DEADZONE = 0.35
PAD_BTN_JUMP = 0
PAD_BTN_RUN = 2
PAD_BTN_BACK = 6
PAD_BTN_START = 7
PAD_BTN_MUTE = 3
PAD_BTN_DPAD_LEFT = 13
PAD_BTN_DPAD_RIGHT = 14


class Gamepads:
    def __init__(self):
        self.joysticks = []
        self.prev = []
        self.newly = set()
        self.refresh()

    def refresh(self):
        self.joysticks = []
        try:
            for i in range(pygame.joystick.get_count()):
                js = pygame.joystick.Joystick(i)
                if not js.get_init():
                    js.init()
                self.joysticks.append(js)
        except pygame.error:
            self.joysticks = []
        self.prev = [set() for _ in self.joysticks]
        self.newly = set()

    def handle_event(self, e):
        if e.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
            self.refresh()

    def any(self):
        return len(self.joysticks) > 0

    def poll(self):
        current = []
        for js in self.joysticks:
            try:
                buttons = set(b for b in range(js.get_numbuttons()) if js.get_button(b))
            except pygame.error:
                buttons = set()
            current.append(buttons)
        newly = set()
        for idx, buttons in enumerate(current):
            prev = self.prev[idx] if idx < len(self.prev) else set()
            newly |= buttons - prev
        self.prev = current
        self.newly = newly


class InputState:
    def __init__(self):
        self.kb = None
        self.virtual = set()

    def poll(self, pads):
        self.kb = pygame.key.get_pressed()
        self.virtual = set()
        for js in pads.joysticks:
            try:
                if js.get_numaxes() > PAD_HORIZONTAL_AXIS:
                    ax = js.get_axis(PAD_HORIZONTAL_AXIS)
                    if ax < -PAD_DEADZONE:
                        self.virtual.add(pygame.K_LEFT)
                    elif ax > PAD_DEADZONE:
                        self.virtual.add(pygame.K_RIGHT)
                if js.get_numhats() > 0:
                    hx, hy = js.get_hat(0)
                    if hx < 0:
                        self.virtual.add(pygame.K_LEFT)
                    elif hx > 0:
                        self.virtual.add(pygame.K_RIGHT)
                n = js.get_numbuttons()
                if n > PAD_BTN_DPAD_RIGHT:
                    if js.get_button(PAD_BTN_DPAD_LEFT):
                        self.virtual.add(pygame.K_LEFT)
                    if js.get_button(PAD_BTN_DPAD_RIGHT):
                        self.virtual.add(pygame.K_RIGHT)
                if n > PAD_BTN_JUMP and js.get_button(PAD_BTN_JUMP):
                    self.virtual.add(pygame.K_SPACE)
                if n > 1 and js.get_button(1):
                    self.virtual.add(pygame.K_SPACE)
                if n > PAD_BTN_RUN and js.get_button(PAD_BTN_RUN):
                    self.virtual.add(pygame.K_LSHIFT)
                if n > 4 and js.get_button(4):
                    self.virtual.add(pygame.K_LSHIFT)
            except pygame.error:
                continue

    def __getitem__(self, k):
        if k in self.virtual:
            return True
        return self.kb is not None and self.kb[k]


def bootstrap():
    pygame.init()
    audio = True
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 512)
    except Exception:
        audio = False
    try:
        pygame.joystick.init()
    except Exception:
        pass
    generate_audio.ensure_assets()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Vihaan Adventures")
    return screen, audio


def main():
    screen, audio = bootstrap()
    clock = pygame.time.Clock()
    game = Game(screen, audio)
    pads = Gamepads()
    inp = InputState()
    if pads.any():
        names = ", ".join(js.get_name() for js in pads.joysticks)
        print("Controller detected: %s" % names)
    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                pads.handle_event(e)
            else:
                game.handle_event(e)
        if not running:
            break
        pads.poll()
        if PAD_BTN_START in pads.newly:
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        if PAD_BTN_BACK in pads.newly:
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        if PAD_BTN_MUTE in pads.newly:
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
        if PAD_BTN_RECALL in pads.newly:
            game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
        inp.poll(pads)
        game.update(inp)
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


def run_selftest():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    screen, audio = bootstrap()
    game = Game(screen, audio)
    print("assets ok, audio=%s" % audio)
    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    assert game.state == "play", game.state
    for li in range(len(game.levels)):
        game.start_level(li)
        for f in range(300):
            pressed = {pygame.K_RIGHT}
            if f % 40 < 20:
                pressed.add(pygame.K_SPACE)
            if f % 150 > 125:
                pressed = {pygame.K_LEFT}
            game.update(Keys(pressed))
            game.draw()
        print("level %d '%s' simulated: enemies=%d coins=%d"
              % (li, game.level.name, len(game.level.enemies), len(game.level.coins)))
    game.level_clear()
    for _ in range(200):
        game.update(Keys(set()))
        game.draw()
    print("selftest ok  state=%s score=%d lives=%d"
          % (game.state, game.score, game.lives))
    pygame.quit()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        run_selftest()
    else:
        main()
