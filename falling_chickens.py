import sys
import os
import json
import random
import math
import pygame


# Game constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 800
FPS = 60

# ── Refined Palette ──────────────────────────────────────────────────────────
SKY_TOP        = (12,  20,  48)    # deep midnight blue
SKY_BOT        = (28,  56, 110)    # dusk blue
GROUND_COLOR   = (34,  42,  58)    # dark slate
GROUND_LINE    = (60,  75, 100)    # subtle horizon line
STAR_COLOR     = (220, 230, 255)   # soft white-blue stars

# UI
UI_BG          = (10,  16,  34, 200)   # semi-transparent dark panel
PANEL_BORDER   = (80, 130, 220)        # electric blue border
ACCENT         = (90, 200, 255)        # cyan accent
GOLD           = (255, 210,  50)
GOLD_DARK      = (200, 150,  20)
WHITE          = (240, 245, 255)
BLACK          = (8,   14,  28)
RED            = (240,  70,  70)
RED_DARK       = (160,  30,  30)
GREEN_BRIGHT   = (80,  230, 140)
LIGHT_BLUE     = (120, 190, 255)

# Legacy aliases kept for compatibility
LIGHT_GREEN    = (180, 230, 180)
BLUE           = (50,  120, 255)


# ── Star field (drawn once, reused) ──────────────────────────────────────────
_STARS: list[tuple[int, int, int]] = []  # (x, y, size)

def _init_stars(n: int = 80):
    global _STARS
    _STARS = [(random.randint(0, WINDOW_WIDTH), random.randint(0, WINDOW_HEIGHT * 2 // 3),
               random.choice([1, 1, 1, 2])) for _ in range(n)]

_init_stars()


# ── Gradient helper ───────────────────────────────────────────────────────────
def draw_gradient_rect(surface: pygame.Surface,
                       color_top: tuple, color_bot: tuple,
                       rect: pygame.Rect):
    """Draw a vertical gradient inside *rect* using horizontal lines."""
    r1, g1, b1 = color_top[:3]
    r2, g2, b2 = color_bot[:3]
    h = max(rect.height, 1)
    for i in range(rect.height):
        t = i / h
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        pygame.draw.line(surface, (r, g, b),
                         (rect.left, rect.top + i),
                         (rect.right - 1, rect.top + i))


def draw_background(surface: pygame.Surface, scroll: float = 0.0):
    """Draw sky gradient + stars + ground strip."""
    # Sky gradient
    draw_gradient_rect(surface, SKY_TOP, SKY_BOT,
                       pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
    # Stars (twinkle via alpha variation)
    t = pygame.time.get_ticks() / 1000.0
    for i, (sx, sy, ss) in enumerate(_STARS):
        alpha = int(160 + 90 * math.sin(t * 1.4 + i * 0.7))
        alpha = max(60, min(255, alpha))
        sc = (STAR_COLOR[0], STAR_COLOR[1], STAR_COLOR[2])
        if ss == 1:
            surface.set_at((sx, sy), sc)
        else:
            pygame.draw.circle(surface, sc, (sx, sy), ss)
    # Ground strip
    ground_y = WINDOW_HEIGHT - 20
    pygame.draw.rect(surface, GROUND_COLOR,
                     pygame.Rect(0, ground_y, WINDOW_WIDTH, 20))
    pygame.draw.line(surface, GROUND_LINE, (0, ground_y), (WINDOW_WIDTH, ground_y), 2)


# ── Particle system ───────────────────────────────────────────────────────────
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size")

    def __init__(self, x, y, color, vx=0.0, vy=0.0, life=30, size=3):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = vx, vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.12   # gravity
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface: pygame.Surface):
        alpha = self.life / self.max_life
        r, g, b = self.color
        c = (int(r * alpha), int(g * alpha), int(b * alpha))
        radius = max(1, int(self.size * alpha))
        pygame.draw.circle(surface, c, (int(self.x), int(self.y)), radius)


_particles: list[Particle] = []


def spawn_hit_particles(x: int, y: int, count: int = 18):
    for _ in range(count):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 5.0)
        color = random.choice([(255, 180, 60), (255, 100, 60), (255, 220, 100)])
        _particles.append(Particle(x, y, color,
                                   vx=math.cos(angle) * speed,
                                   vy=math.sin(angle) * speed - 2,
                                   life=random.randint(20, 40),
                                   size=random.randint(2, 5)))


def spawn_coin_particles(x: int, y: int):
    for _ in range(8):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.0, 3.0)
        _particles.append(Particle(x, y, GOLD,
                                   vx=math.cos(angle) * speed,
                                   vy=math.sin(angle) * speed - 1.5,
                                   life=random.randint(15, 25),
                                   size=random.randint(2, 4)))


def update_and_draw_particles(surface: pygame.Surface):
    global _particles
    alive = []
    for p in _particles:
        p.update()
        if p.alive:
            p.draw(surface)
            alive.append(p)
    _particles = alive


# ── Panel / UI helpers ────────────────────────────────────────────────────────
def draw_panel(surface: pygame.Surface, rect: pygame.Rect,
               alpha: int = 200, border_color=PANEL_BORDER, radius: int = 12):
    """Draw a rounded semi-transparent dark panel."""
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*BLACK[:3], alpha), (0, 0, rect.width, rect.height),
                     border_radius=radius)
    surface.blit(panel, rect.topleft)
    pygame.draw.rect(surface, border_color, rect, width=2, border_radius=radius)


def draw_text(surface: pygame.Surface, text: str, size: int,
              color: tuple, center: tuple,
              font_name: str = "consolas"):
    font = pygame.font.SysFont(font_name, size, bold=True)
    render = font.render(text, True, color)
    rect = render.get_rect(center=center)
    surface.blit(render, rect)


def draw_text_shadow(surface: pygame.Surface, text: str, size: int,
                     color: tuple, center: tuple,
                     shadow_color=(0, 0, 0), offset: int = 2):
    draw_text(surface, text, size, shadow_color,
              (center[0] + offset, center[1] + offset))
    draw_text(surface, text, size, color, center)


# ── Hearts ────────────────────────────────────────────────────────────────────
def draw_hearts(surface: pygame.Surface, hearts: int, max_hearts: int = 6):
    spacing = 8
    heart_w, heart_h = 20, 18
    x = WINDOW_WIDTH - 12
    y = 14

    for i in range(max_hearts):
        filled = i < hearts
        left = x - (heart_w + spacing) * i - heart_w
        top = y
        cx = left + heart_w // 2
        cy = top + heart_h // 2

        if filled:
            # Draw a filled heart shape
            pygame.draw.circle(surface, RED, (left + heart_w // 3, top + 6), 6)
            pygame.draw.circle(surface, RED, (left + 2 * heart_w // 3, top + 6), 6)
            pts = [
                (left, top + 7),
                (cx, top + heart_h + 2),
                (left + heart_w, top + 7),
            ]
            pygame.draw.polygon(surface, RED, pts)
            # Shine
            pygame.draw.circle(surface, (255, 160, 160), (left + heart_w // 3 - 1, top + 4), 2)
        else:
            pygame.draw.circle(surface, (80, 80, 100), (left + heart_w // 3, top + 6), 6, 2)
            pygame.draw.circle(surface, (80, 80, 100), (left + 2 * heart_w // 3, top + 6), 6, 2)
            pts = [
                (left, top + 7),
                (cx, top + heart_h + 2),
                (left + heart_w, top + 7),
            ]
            pygame.draw.polygon(surface, (80, 80, 100), pts, 2)


# ── Angel ─────────────────────────────────────────────────────────────────────
def draw_angel(surface: pygame.Surface, rect: pygame.Rect):
    t = pygame.time.get_ticks() / 1000.0
    bob = int(math.sin(t * 3) * 3)
    r = rect.move(0, bob)

    # Glow aura
    glow_surf = pygame.Surface((r.width + 30, r.height + 30), pygame.SRCALPHA)
    glow_alpha = int(60 + 40 * math.sin(t * 2))
    pygame.draw.ellipse(glow_surf, (255, 255, 180, glow_alpha),
                        (0, 0, r.width + 30, r.height + 30))
    surface.blit(glow_surf, (r.x - 15, r.y - 15))

    # Wings
    wing_l = pygame.Rect(r.x, r.y + r.h // 4, r.w // 3 + 4, r.h // 2)
    wing_r = pygame.Rect(r.right - r.w // 3 - 4, r.y + r.h // 4, r.w // 3 + 4, r.h // 2)
    pygame.draw.ellipse(surface, (180, 220, 255), wing_l)
    pygame.draw.ellipse(surface, (180, 220, 255), wing_r)
    pygame.draw.ellipse(surface, WHITE, wing_l, 1)
    pygame.draw.ellipse(surface, WHITE, wing_r, 1)

    # Body
    body = pygame.Rect(r.x + r.w // 4, r.y + r.h // 3, r.w // 2, r.h * 2 // 3)
    pygame.draw.rect(surface, WHITE, body, border_radius=6)

    # Head
    hr = r.w // 6
    hc = (r.centerx, r.y + r.h // 4)
    pygame.draw.circle(surface, (255, 230, 200), hc, hr)

    # Halo — spinning gold ring
    halo_r = hr + 5
    pygame.draw.circle(surface, GOLD, hc, halo_r, 3)
    # Small sparkle on halo
    angle = t * 3
    sx = hc[0] + int(math.cos(angle) * halo_r)
    sy = hc[1] + int(math.sin(angle) * halo_r)
    pygame.draw.circle(surface, WHITE, (sx, sy), 2)

    draw_text_shadow(surface, "ANGEL", 11, GOLD, (r.centerx, r.bottom - 6))


# ── TNT ───────────────────────────────────────────────────────────────────────
def draw_tnt(surface: pygame.Surface, rect: pygame.Rect):
    t = pygame.time.get_ticks() / 1000.0
    # Pulsing red
    pulse = int(30 * math.sin(t * 8))
    col = (min(255, 220 + pulse), max(0, 40 - pulse // 2), max(0, 40 - pulse // 2))
    pygame.draw.rect(surface, col, rect, border_radius=8)
    pygame.draw.rect(surface, (255, 180, 60), rect, width=2, border_radius=8)
    # Fuse spark
    fuse_x = rect.centerx
    fuse_y = rect.top
    if random.random() < 0.5:
        spark_c = random.choice([(255, 230, 60), (255, 160, 40), WHITE])
        pygame.draw.circle(surface, spark_c,
                           (fuse_x + random.randint(-3, 3),
                            fuse_y + random.randint(-6, 0)), 3)
    draw_text_shadow(surface, "TNT", 22, WHITE, rect.center)


# ── Character definitions ─────────────────────────────────────────────────────
CHARACTERS = [
    {
        "id":    0,
        "name":  "Astronaut",
        "file":  "assets/character_1.png",
        "color": ACCENT,
        "desc":  "Fearless space explorer",
        "stat":  "Balanced",
    },
    {
        "id":    1,
        "name":  "Ninja",
        "file":  "assets/character_2.png",
        "color": RED,
        "desc":  "Shadow of the night",
        "stat":  "Fast",
    },
    {
        "id":    2,
        "name":  "Wizard",
        "file":  "assets/character_3.png",
        "color": (180, 80, 255),
        "desc":  "Master of arcane arts",
        "stat":  "Lucky",
    },
]

# Cache: character_id → loaded pygame.Surface
_char_sprite_cache: dict[int, pygame.Surface | None] = {}

def load_character_sprite(char_id: int, target_size: tuple[int, int]) -> pygame.Surface | None:
    """Load (and cache at target_size) a character sprite."""
    key = char_id
    if key in _char_sprite_cache:
        return _char_sprite_cache[key]
    path = CHARACTERS[char_id]["file"]
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, target_size)
        _char_sprite_cache[key] = img
        return img
    except Exception:
        _char_sprite_cache[key] = None
        return None


# ── Player ────────────────────────────────────────────────────────────────────
class Player:
    _sprite: pygame.Surface | None = None
    _sprite_size: tuple[int, int] | None = None

    @staticmethod
    def load_shared_sprite(target_size, char_id: int = 0):
        """Load sprite for the given character id."""
        sprite = load_character_sprite(char_id, target_size)
        if sprite is None:
            # Try legacy player.png as fallback for char 0
            try:
                img = pygame.image.load("assets/player.png").convert_alpha()
                img = pygame.transform.smoothscale(img, target_size)
                sprite = img
            except Exception:
                sprite = None
        Player._sprite = sprite
        Player._sprite_size = target_size

    def __init__(self, x, y, width=100, height=110, speed=8, char_id: int = 0):
        self.width = width
        self.height = height
        self.speed = speed
        self.char_id = char_id
        self.rect = pygame.Rect(x, y, width, height)
        Player.load_shared_sprite((width, height), char_id)
        self.velocity_y = 0.0
        self._step = 0.0   # for walk animation
        self._facing = 1   # 1 = right, -1 = left
        self._walk_offset = 0  # pixel bob

    def set_character(self, char_id: int):
        self.char_id = char_id
        Player.load_shared_sprite((self.width, self.height), char_id)

    def reset(self, x, y):
        self.rect.topleft = (x, y)
        self.velocity_y = 0.0
        self._step = 0.0
        self._walk_offset = 0

    def update(self, pressed_keys):
        moving = False
        if pressed_keys[pygame.K_LEFT] or pressed_keys[pygame.K_a]:
            self.rect.x -= self.speed
            self._facing = -1
            moving = True
        if pressed_keys[pygame.K_RIGHT] or pressed_keys[pygame.K_d]:
            self.rect.x += self.speed
            self._facing = 1
            moving = True

        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH

        self.velocity_y += 0.8
        self.rect.y += int(self.velocity_y)
        ground_y = WINDOW_HEIGHT - 20
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.velocity_y = 0.0

        # Walk bob
        if moving and self.is_on_ground():
            self._step += 0.25
            self._walk_offset = int(math.sin(self._step) * 3)
        else:
            self._walk_offset = 0

    def is_on_ground(self):
        return self.rect.bottom >= WINDOW_HEIGHT - 20 and abs(self.velocity_y) < 0.5

    def draw(self, surface: pygame.Surface, shield_active=False, ghost_active=False):
        draw_rect = self.rect.move(0, -self._walk_offset)

        if ghost_active:
            s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            if Player._sprite:
                s.blit(Player._sprite, (0, 0))
                s.set_alpha(140)
            else:
                pygame.draw.rect(s, (*LIGHT_BLUE[:3], 140), s.get_rect(), border_radius=4)
            surface.blit(s, draw_rect)
        elif Player._sprite is not None:
            img = Player._sprite
            if self._facing == -1:
                img = pygame.transform.flip(img, True, False)
            surface.blit(img, draw_rect)
        else:
            # Fallback drawn character
            _draw_fallback_player(surface, draw_rect)

        if shield_active:
            t = pygame.time.get_ticks() / 1000.0
            shield_alpha = int(80 + 50 * math.sin(t * 4))
            shield_surf = pygame.Surface((self.width + 16, self.height + 16), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surf,
                                (*ACCENT[:3], shield_alpha),
                                shield_surf.get_rect())
            pygame.draw.ellipse(shield_surf,
                                (*WHITE[:3], min(255, shield_alpha + 60)),
                                shield_surf.get_rect(), 2)
            surface.blit(shield_surf, (draw_rect.x - 8, draw_rect.y - 8))


def _draw_fallback_player(surface: pygame.Surface, rect: pygame.Rect):
    """Draws a simple astronaut-style figure when no sprite is available."""
    cx = rect.centerx
    # Body
    body = pygame.Rect(rect.x + rect.w // 5, rect.y + rect.h // 3,
                       rect.w * 3 // 5, rect.h * 2 // 3)
    pygame.draw.rect(surface, (70, 130, 200), body, border_radius=6)
    pygame.draw.rect(surface, ACCENT, body, width=2, border_radius=6)
    # Helmet
    helm_r = rect.w // 3
    helm_c = (cx, rect.y + rect.h // 5)
    pygame.draw.circle(surface, (50, 100, 180), helm_c, helm_r)
    pygame.draw.circle(surface, (120, 200, 255), (helm_c[0] - 4, helm_c[1] - 4), helm_r // 2)
    # Visor shine
    pygame.draw.circle(surface, WHITE, (helm_c[0] - 5, helm_c[1] - 5), 4)


# ── Chicken ───────────────────────────────────────────────────────────────────
class Chicken:
    _sprite: pygame.Surface | None = None
    _sprite_size: tuple[int, int] | None = None

    @staticmethod
    def load_shared_sprite(target_size):
        if Chicken._sprite is not None and Chicken._sprite_size == target_size:
            return
        try:
            image = pygame.image.load("assets/chicken.png").convert_alpha()
            image = pygame.transform.smoothscale(image, target_size)
            Chicken._sprite = image
            Chicken._sprite_size = target_size
        except Exception:
            Chicken._sprite = None

    def __init__(self, x, width=41, height=41, fall_speed=2.7):
        self.rect = pygame.Rect(x, -height - 5, width, height)
        self.base_fall_speed = fall_speed
        self.extra_speed = 0.0
        self._rot = random.uniform(0, 360)
        self._rot_speed = random.uniform(-4, 4)
        self._wobble = random.uniform(0, math.tau)
        self._wobble_amp = random.uniform(0.4, 1.4)
        Chicken.load_shared_sprite((width, height))

    def set_difficulty_bonus(self, bonus_speed):
        self.extra_speed = bonus_speed

    def update(self):
        self.rect.y += self.base_fall_speed + self.extra_speed
        self._rot += self._rot_speed
        self._wobble += 0.08
        self.rect.x += int(math.sin(self._wobble) * self._wobble_amp)
        # Keep in bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH

    def is_off_screen(self):
        return self.rect.top > WINDOW_HEIGHT

    def draw(self, surface: pygame.Surface):
        if Chicken._sprite is not None:
            img = pygame.transform.rotate(Chicken._sprite, self._rot)
            r = img.get_rect(center=self.rect.center)
            surface.blit(img, r)
        else:
            _draw_fallback_chicken(surface, self.rect, self._rot)


def _draw_fallback_chicken(surface: pygame.Surface, rect: pygame.Rect, rot: float):
    """Draws a stylised chicken when no sprite is available."""
    cx, cy = rect.center
    r = rect.w // 2
    # Shadow
    shadow_surf = pygame.Surface((rect.w + 4, rect.h + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), shadow_surf.get_rect())
    surface.blit(shadow_surf, (rect.x - 2, rect.y + rect.h - 6))
    # Body
    pygame.draw.ellipse(surface, WHITE, rect)
    pygame.draw.ellipse(surface, (200, 200, 210), rect, 2)
    # Beak
    beak_pts = [(cx, cy - 4), (cx + 8, cy), (cx, cy + 4)]
    pygame.draw.polygon(surface, (255, 180, 30), beak_pts)
    # Eye
    pygame.draw.circle(surface, BLACK, (cx - 4, cy - 3), 3)
    pygame.draw.circle(surface, WHITE, (cx - 5, cy - 4), 1)
    # Comb
    pygame.draw.circle(surface, RED, (cx - 4, cy - r + 2), 4)


# ── Coin ──────────────────────────────────────────────────────────────────────
class Coin:
    _sprite: pygame.Surface | None = None
    _sprite_size: tuple[int, int] | None = None

    @staticmethod
    def load_shared_sprite(target_size):
        if Coin._sprite is not None and Coin._sprite_size == target_size:
            return
        try:
            image = pygame.image.load("assets/coin.png").convert_alpha()
            image = pygame.transform.smoothscale(image, target_size)
            Coin._sprite = image
            Coin._sprite_size = target_size
        except Exception:
            Coin._sprite = None

    def __init__(self, x, width=30, height=30, fall_speed=2.0):
        self.rect = pygame.Rect(x, -height - 5, width, height)
        self.base_fall_speed = fall_speed
        self.extra_speed = 0.0
        self._phase = random.uniform(0, math.tau)  # for spin squish
        Coin.load_shared_sprite((width, height))

    def set_difficulty_bonus(self, bonus_speed):
        self.extra_speed = bonus_speed

    def update(self):
        self.rect.y += self.base_fall_speed + self.extra_speed
        self._phase += 0.12

    def is_off_screen(self):
        return self.rect.top > WINDOW_HEIGHT

    def draw(self, surface: pygame.Surface):
        t = pygame.time.get_ticks() / 1000.0
        if Coin._sprite is not None:
            # Squish effect to simulate spinning
            squish = abs(math.cos(self._phase))
            w = max(4, int(self.rect.width * squish))
            h = self.rect.height
            scaled = pygame.transform.scale(Coin._sprite, (w, h))
            surface.blit(scaled, (self.rect.centerx - w // 2, self.rect.y))
        else:
            _draw_fallback_coin(surface, self.rect, self._phase)


def _draw_fallback_coin(surface: pygame.Surface, rect: pygame.Rect, phase: float):
    """Draw an animated spinning coin."""
    squish = abs(math.cos(phase))
    w = max(4, int(rect.width * squish))
    h = rect.height
    cx, cy = rect.centerx, rect.centery
    coin_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    pygame.draw.ellipse(surface, GOLD, coin_rect)
    # Shine
    if w > 8:
        shine_rect = pygame.Rect(cx - w // 4, cy - h // 3, max(2, w // 3), h // 3)
        pygame.draw.ellipse(surface, (255, 240, 150), shine_rect)
    pygame.draw.ellipse(surface, GOLD_DARK, coin_rect, 2)


# ── Score / HUD text helpers ──────────────────────────────────────────────────
def draw_hud_pill(surface: pygame.Surface, text: str, x: int, y: int,
                  bg=(20, 30, 60, 200), border=PANEL_BORDER, size=20):
    font = pygame.font.SysFont("consolas", size, bold=True)
    tw = font.size(text)[0]
    pad = 10
    pill = pygame.Rect(x, y, tw + pad * 2, size + pad)
    s = pygame.Surface((pill.width, pill.height), pygame.SRCALPHA)
    pygame.draw.rect(s, bg, s.get_rect(), border_radius=8)
    surface.blit(s, pill.topleft)
    pygame.draw.rect(surface, border, pill, 1, border_radius=8)
    render = font.render(text, True, WHITE)
    surface.blit(render, (pill.x + pad, pill.y + pad // 2))


# ── Active power bar ──────────────────────────────────────────────────────────
def draw_power_timer_bar(surface: pygame.Surface, label: str, fraction: float,
                         y: int, color=ACCENT, width=160):
    x = 10
    bar_h = 14
    bg_rect = pygame.Rect(x, y, width, bar_h)
    fill_w = int(width * max(0, min(1, fraction)))
    # BG
    pygame.draw.rect(surface, (20, 30, 50), bg_rect, border_radius=4)
    # Fill
    if fill_w > 0:
        pygame.draw.rect(surface, color,
                         pygame.Rect(x, y, fill_w, bar_h), border_radius=4)
    pygame.draw.rect(surface, color, bg_rect, 1, border_radius=4)
    # Label
    font = pygame.font.SysFont("consolas", 11, bold=True)
    surface.blit(font.render(label, True, WHITE), (x + 4, y + 1))


# ─────────────────────────────────────────────────────────────────────────────
def main():
    pygame.init()
    pygame.display.set_caption("Falling Chickens ✦")
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # ── Power inventory ──────────────────────────────────────────────────────
    player_powers = {
        "extra_life": 0, "speed_boost": 0, "coin_magnet": 0,
        "j_key_pack": 0, "slow_motion": 0, "super_jump": 0,
        "shield": 0, "double_coins": 0, "lucky_charm": 0,
        "time_freeze": 0, "coin_rain": 0, "ghost_mode": 0
    }

    speed_boost_active_until   = 0
    coin_magnet_active_until   = 0
    slow_motion_active_until   = 0
    super_jump_active_until    = 0
    shield_hits_remaining      = 0
    double_coins_active_until  = 0
    lucky_charm_active_until   = 0
    time_freeze_uses_remaining = 0
    coin_rain_active_until     = 0
    ghost_phases_remaining     = 0
    time_frozen_until          = 0

    # ── Audio ────────────────────────────────────────────────────────────────
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception:
        pass

    def load_hit_sound():
        try:
            return pygame.mixer.Sound("assets/hit.wav")
        except Exception:
            return None

    def load_background_music():
        try:
            pygame.mixer.music.load("assets/background.wav")
            return True
        except Exception:
            return False

    hit_sound = load_hit_sound()
    if load_background_music():
        try:
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

    # ── States ───────────────────────────────────────────────────────────────
    START_SCREEN     = "start_screen"
    CHAR_SELECT      = "char_select"
    MODE_SELECT      = "mode_select"
    SHOP             = "shop"
    RUNNING          = "running"
    GAME_OVER        = "game_over"
    state = START_SCREEN

    # ── Game modes ────────────────────────────────────────────────────────────
    GAME_MODES = [
        {
            "id":            0,
            "name":          "Easy",
            "color":         GREEN_BRIGHT,
            "icon":          "🌿",
            "desc":          "Slower chickens, more breathing room",
            "speed_mult":    0.6,   # base fall speed multiplier
            "spawn_mult":    1.4,   # spawn interval multiplier (higher = less frequent)
            "diff_mult":     0.6,   # how fast difficulty ramps
        },
        {
            "id":            1,
            "name":          "Normal",
            "color":         ACCENT,
            "icon":          "⚡",
            "desc":          "Classic experience, balanced challenge",
            "speed_mult":    1.0,
            "spawn_mult":    1.0,
            "diff_mult":     1.0,
        },
        {
            "id":            2,
            "name":          "Hard",
            "color":         RED,
            "icon":          "💀",
            "desc":          "Fast & relentless — good luck!",
            "speed_mult":    1.6,
            "spawn_mult":    0.65,  # shorter spawn interval = more chickens
            "diff_mult":     1.6,
        },
    ]
    selected_mode_id = 1   # highlighted in picker
    active_mode_id   = 1   # the one actually in play

    # ── Character selection ───────────────────────────────────────────────────
    selected_char_id = 0          # currently highlighted in picker
    active_char_id   = 0          # the one actually in play
    # Pre-load all character sprites at display size for the selection screen
    char_preview_size = (100, 110)
    char_previews: list = []
    for _ci in range(len(CHARACTERS)):
        char_previews.append(load_character_sprite(_ci, char_preview_size))

    # ── Entities ─────────────────────────────────────────────────────────────
    player_width  = 67
    player_height = 73
    chickens: list[Chicken] = []
    coins: list[Coin] = []

    start_ticks_ms     = pygame.time.get_ticks()
    last_spawn_ms      = 0
    spawn_interval_ms  = 700
    last_coin_spawn_ms = 0
    coin_spawn_interval_ms = 2000

    def get_difficulty(seconds_alive: float) -> float:
        mode = GAME_MODES[active_mode_id]
        return min(3.0, 0.15 * seconds_alive * mode["diff_mult"])

    score              = 0
    last_score_second  = 0
    coins_collected    = 0
    lives              = 5
    invulnerable_until_ms = 0
    j_keys_available   = 1
    coins_for_j_key    = 10

    TNT_INTERVAL_MS  = 20000
    TNT_DURATION_MS  = 3000
    TNT_SPEED_PX     = 4
    tnt_active        = False
    tnt_rect          = None
    last_tnt_spawn_ms = start_ticks_ms
    tnt_visible_until_ms = 0
    tnt_velocity_x    = 0

    ANGEL_INTERVAL_MS  = 30000
    ANGEL_DURATION_MS  = 2000
    angel_active        = False
    angel_rect          = None
    last_angel_spawn_ms = start_ticks_ms
    angel_visible_until_ms = 0

    # ── Highscores (per-difficulty) ───────────────────────────────────────────
    highscores_path = os.path.join(os.path.dirname(__file__), "highscores.json")
    DIFF_KEYS = ["easy", "normal", "hard"]

    def load_highscores():
        empty = {k: [] for k in DIFF_KEYS}
        try:
            with open(highscores_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                total_coins = int(data.get("total_coins", 0))
                if any(k in data for k in DIFF_KEYS):
                    result = {}
                    for k in DIFF_KEYS:
                        raw = data.get(k, [])
                        cleaned = [{"name": str(r["name"])[:12], "score": int(r["score"])}
                                   for r in raw if isinstance(r, dict) and "name" in r and "score" in r]
                        result[k] = sorted(cleaned, key=lambda x: x["score"], reverse=True)[:5]
                    return result, total_coins
                raw = data.get("scores", [])
                cleaned = [{"name": str(r["name"])[:12], "score": int(r["score"])}
                           for r in raw if isinstance(r, dict) and "name" in r and "score" in r]
                migrated = {k: [] for k in DIFF_KEYS}
                migrated["normal"] = sorted(cleaned, key=lambda x: x["score"], reverse=True)[:5]
                return migrated, total_coins
        except Exception:
            pass
        return empty, 0

    def save_highscores(scores_by_diff, total_coins):
        try:
            data = {"total_coins": total_coins}
            for k in DIFF_KEYS:
                data[k] = scores_by_diff.get(k, [])[:5]
            with open(highscores_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_highscore(name, value, mode_id, coins_earned=0):
        sbd, tc = load_highscores()
        key = DIFF_KEYS[mode_id]
        entry = {"name": (name[:12] if name else "Player"), "score": int(value)}
        sbd[key].append(entry)
        sbd[key] = sorted(sbd[key], key=lambda x: x["score"], reverse=True)[:5]
        tc += coins_earned
        save_highscores(sbd, tc)
        return sbd, tc

    scores_by_diff, total_coins_saved = load_highscores()
    name_input = ""
    name_saved = False

    # ── Shop ─────────────────────────────────────────────────────────────────
    shop_selected_item = 0
    shop_items = [
        {"name": "Extra Life",   "price":  50, "description": "Press 1  →  +1 life",           "type": "extra_life",  "key": "1"},
        {"name": "Speed Boost",  "price":  30, "description": "Press 2  →  10s speed boost",    "type": "speed_boost", "key": "2"},
        {"name": "Coin Magnet",  "price":  40, "description": "Press 3  →  15s coin attraction","type": "coin_magnet", "key": "3"},
        {"name": "J Key Pack",   "price":  25, "description": "Press 4  →  +2 J keys",          "type": "j_key_pack",  "key": "4"},
        {"name": "Slow Motion",  "price":  60, "description": "Press 5  →  12s slow motion",    "type": "slow_motion", "key": "5"},
        {"name": "Super Jump",   "price":  35, "description": "Press 6  →  20s super jump",     "type": "super_jump",  "key": "6"},
        {"name": "Shield",       "price":  80, "description": "Press 7  →  1-hit protection",   "type": "shield",      "key": "7"},
        {"name": "Double Coins", "price":  70, "description": "Press 8  →  30s double coins",   "type": "double_coins","key": "8"},
        {"name": "Lucky Charm",  "price":  45, "description": "Press 9  →  25s lucky protect",  "type": "lucky_charm", "key": "9"},
        {"name": "Time Freeze",  "price":  90, "description": "Press 0  →  3 time freezes",     "type": "time_freeze", "key": "0"},
        {"name": "Coin Rain",    "price":  55, "description": "Press Q  →  20s coin rain",      "type": "coin_rain",   "key": "Q"},
        {"name": "Ghost Mode",   "price": 100, "description": "Press W  →  1 ghost phase",      "type": "ghost_mode",  "key": "W"},
    ]

    # ── Player ───────────────────────────────────────────────────────────────
    player = Player(
        x=WINDOW_WIDTH // 2 - player_width // 2,
        y=WINDOW_HEIGHT - 20 - player_height,
        width=player_width, height=player_height, speed=8,
        char_id=active_char_id,
    )

    # Screen-shake state
    shake_until = 0
    shake_mag   = 0

    def trigger_shake(mag=6, duration_ms=300):
        nonlocal shake_until, shake_mag
        shake_until = pygame.time.get_ticks() + duration_ms
        shake_mag   = mag

    # Title wave animation
    def draw_wavy_title(surface, text, size, y, color):
        font = pygame.font.SysFont("consolas", size, bold=True)
        t = pygame.time.get_ticks() / 600.0
        total_w = sum(font.size(ch)[0] for ch in text)
        x = WINDOW_WIDTH // 2 - total_w // 2
        for i, ch in enumerate(text):
            cy = y + int(math.sin(t + i * 0.4) * 5)
            render = font.render(ch, True, color)
            shadow = font.render(ch, True, BLACK)
            surface.blit(shadow, (x + 2, cy + 2))
            surface.blit(render, (x, cy))
            x += render.get_width()

    # ── Main loop ────────────────────────────────────────────────────────────
    while True:
        now_ms = pygame.time.get_ticks()

        # ── Events ───────────────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            # ── START SCREEN ─────────────────────────────────────────────────
            if state == START_SCREEN and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                    # Go to character select before starting
                    state = CHAR_SELECT
                    selected_char_id = active_char_id
                elif event.key == pygame.K_y:
                    state = SHOP
                    shop_selected_item = 0
                elif event.key == pygame.K_c:
                    state = CHAR_SELECT
                    selected_char_id = active_char_id

            # ── GAME OVER ─────────────────────────────────────────────────────
            elif state == GAME_OVER and event.type == pygame.KEYDOWN:
                if not name_saved:
                    if event.key == pygame.K_BACKSPACE:
                        name_input = name_input[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if not name_input.strip():
                            name_input = "Player"
                        scores_by_diff, total_coins_saved = add_highscore(name_input, score, active_mode_id, coins_collected)
                        name_saved = True
                    else:
                        ch = event.unicode
                        if ch and ch.isprintable() and ch not in ("\r", "\n"):
                            if len(name_input) < 12 and (ch.isalnum() or ch in " _-."):
                                name_input += ch
                if event.key == pygame.K_r:
                    # Go to char select for a fresh start
                    state = CHAR_SELECT
                    selected_char_id = active_char_id

            # ── CHARACTER SELECT ──────────────────────────────────────────────
            elif state == CHAR_SELECT and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    state = START_SCREEN
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    selected_char_id = (selected_char_id - 1) % len(CHARACTERS)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected_char_id = (selected_char_id + 1) % len(CHARACTERS)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    # Confirm character, then pick mode
                    active_char_id = selected_char_id
                    player.set_character(active_char_id)
                    state = MODE_SELECT
                    selected_mode_id = active_mode_id

            # ── MODE SELECT ───────────────────────────────────────────────────
            elif state == MODE_SELECT and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    state = CHAR_SELECT
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    selected_mode_id = (selected_mode_id - 1) % len(GAME_MODES)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    selected_mode_id = (selected_mode_id + 1) % len(GAME_MODES)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    active_mode_id = selected_mode_id
                    # Full game reset & start
                    speed_boost_active_until = coin_magnet_active_until = 0
                    slow_motion_active_until = super_jump_active_until  = 0
                    shield_hits_remaining = double_coins_active_until   = 0
                    lucky_charm_active_until = time_freeze_uses_remaining = 0
                    coin_rain_active_until = ghost_phases_remaining = time_frozen_until = 0
                    chickens.clear(); coins.clear(); _particles.clear()
                    player.reset(WINDOW_WIDTH // 2 - player.width // 2, WINDOW_HEIGHT - 20 - player.height)
                    start_ticks_ms = now_ms
                    last_spawn_ms = last_coin_spawn_ms = 0
                    spawn_interval_ms = 700
                    score = last_score_second = coins_collected = 0
                    lives = 5; invulnerable_until_ms = 0; j_keys_available = 1
                    name_input = ""; name_saved = False
                    tnt_active = False; tnt_rect = None; tnt_velocity_x = 0
                    last_tnt_spawn_ms = tnt_visible_until_ms = now_ms
                    angel_active = False; angel_rect = None
                    last_angel_spawn_ms = angel_visible_until_ms = now_ms
                    state = RUNNING

            # ── SHOP ─────────────────────────────────────────────────────────
            elif state == SHOP and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    state = START_SCREEN
                elif event.key in (pygame.K_UP,):
                    shop_selected_item = (shop_selected_item - 1) % len(shop_items)
                elif event.key in (pygame.K_DOWN,):
                    shop_selected_item = (shop_selected_item + 1) % len(shop_items)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    sel = shop_items[shop_selected_item]
                    if total_coins_saved >= sel["price"]:
                        total_coins_saved -= sel["price"]
                        player_powers[sel["type"]] += 1
                        save_highscores(scores_by_diff, total_coins_saved)

            # ── RUNNING – power activation ────────────────────────────────────
            elif state == RUNNING and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1 and player_powers["extra_life"] > 0:
                    player_powers["extra_life"] -= 1; lives = min(6, lives + 1)
                elif event.key == pygame.K_2 and player_powers["speed_boost"] > 0:
                    player_powers["speed_boost"] -= 1; speed_boost_active_until = now_ms + 10000
                elif event.key == pygame.K_3 and player_powers["coin_magnet"] > 0:
                    player_powers["coin_magnet"] -= 1; coin_magnet_active_until = now_ms + 15000
                elif event.key == pygame.K_4 and player_powers["j_key_pack"] > 0:
                    player_powers["j_key_pack"] -= 1; j_keys_available += 2
                elif event.key == pygame.K_5 and player_powers["slow_motion"] > 0:
                    player_powers["slow_motion"] -= 1; slow_motion_active_until = now_ms + 12000
                elif event.key == pygame.K_6 and player_powers["super_jump"] > 0:
                    player_powers["super_jump"] -= 1; super_jump_active_until = now_ms + 20000
                elif event.key == pygame.K_7 and player_powers["shield"] > 0:
                    player_powers["shield"] -= 1; shield_hits_remaining += 1
                elif event.key == pygame.K_8 and player_powers["double_coins"] > 0:
                    player_powers["double_coins"] -= 1; double_coins_active_until = now_ms + 30000
                elif event.key == pygame.K_9 and player_powers["lucky_charm"] > 0:
                    player_powers["lucky_charm"] -= 1; lucky_charm_active_until = now_ms + 25000
                elif event.key == pygame.K_0 and player_powers["time_freeze"] > 0:
                    player_powers["time_freeze"] -= 1; time_freeze_uses_remaining += 3
                elif event.key == pygame.K_q and player_powers["coin_rain"] > 0:
                    player_powers["coin_rain"] -= 1; coin_rain_active_until = now_ms + 20000
                elif event.key == pygame.K_w and player_powers["ghost_mode"] > 0:
                    player_powers["ghost_mode"] -= 1; ghost_phases_remaining += 1

        # ════════════════════════════════════════════════════════════════════
        # Compute screen-shake offset
        shake_x = shake_y = 0
        if now_ms < shake_until:
            shake_x = random.randint(-shake_mag, shake_mag)
            shake_y = random.randint(-shake_mag, shake_mag)

        # ── DRAW BACKGROUND (always) ──────────────────────────────────────
        draw_background(screen)

        # ════════════════════════════════════════════════════════════════════
        if state == START_SCREEN:
            draw_wavy_title(screen, "FALLING CHICKENS", 52, 100, ACCENT)
            draw_text_shadow(screen, "Avoid the falling chickens!", 24, WHITE, (WINDOW_WIDTH // 2, 175))

            # Controls panel
            cp = pygame.Rect(30, 210, WINDOW_WIDTH - 60, 260)
            draw_panel(screen, cp)
            draw_text(screen, "CONTROLS", 20, ACCENT, (WINDOW_WIDTH // 2, 228))
            lines = [
                ("Left / Right  or  A / D", "Move"),
                ("Space",                    "Jump"),
                ("J",                        "Clear all chickens & coins"),
                ("K",                        "Buy J key (10 coins)"),
                ("1-9, 0, Q, W",             "Activate purchased powers"),
                ("F",                        "Time freeze (if owned)"),
            ]
            for i, (key, desc) in enumerate(lines):
                y = 252 + i * 28
                draw_text(screen, key,  17, GOLD,  (WINDOW_WIDTH // 2 - 70, y))
                draw_text(screen, desc, 17, WHITE, (WINDOW_WIDTH // 2 + 80, y))

            # Special items panel
            sp = pygame.Rect(30, 482, WINDOW_WIDTH - 60, 80)
            draw_panel(screen, sp, border_color=(200, 100, 100))
            draw_text(screen, "SPECIAL ITEMS", 18, RED, (WINDOW_WIDTH // 2, 498))
            draw_text(screen, "TNT  →  -1 heart      Angel  →  +2 hearts      Coins  →  score!", 15, WHITE, (WINDOW_WIDTH // 2, 522))
            t_flash = pygame.time.get_ticks() / 1000.0
            draw_text_shadow(screen, f"⭐  Total Coins: {total_coins_saved}  ⭐", 34, GOLD, (WINDOW_WIDTH // 2, 580))

            # Currently selected character + mode mini-display
            char_info = CHARACTERS[active_char_id]
            mode_info = GAME_MODES[active_mode_id]
            char_panel = pygame.Rect(30, 560, WINDOW_WIDTH - 60, 50)
            draw_panel(screen, char_panel, border_color=char_info["color"])
            char_prev = char_previews[active_char_id]
            if char_prev:
                small = pygame.transform.smoothscale(char_prev, (36, 40))
                screen.blit(small, (45, 568))
            draw_text(screen, f"{char_info['name']}  ·  {mode_info['icon']} {mode_info['name']}", 18,
                      char_info["color"], (WINDOW_WIDTH // 2 + 20, 585))

            # Mini leaderboard - top 1 per difficulty
            any_scores = any(scores_by_diff.get(k) for k in DIFF_KEYS)
            if any_scores:
                hp = pygame.Rect(30, 618, WINDOW_WIDTH - 60, 110)
                draw_panel(screen, hp)
                draw_text(screen, "TOP SCORES", 16, ACCENT, (WINDOW_WIDTH // 2, 632))
                col_xs = [WINDOW_WIDTH // 2 - 160, WINDOW_WIDTH // 2, WINDOW_WIDTH // 2 + 160]
                for ci, (k, mode) in enumerate(zip(DIFF_KEYS, GAME_MODES)):
                    rows = scores_by_diff.get(k, [])
                    draw_text(screen, f"{mode['icon']} {mode['name']}", 14, mode["color"], (col_xs[ci], 650))
                    if rows:
                        top = rows[0]
                        draw_text(screen, top["name"][:10], 13, WHITE, (col_xs[ci], 668))
                        draw_text(screen, str(top["score"]), 15, GOLD, (col_xs[ci], 685))
                    else:
                        draw_text(screen, "—", 14, (100,110,130), (col_xs[ci], 675))

            # Blinking prompt
            if (now_ms // 600) % 2 == 0:
                draw_text_shadow(screen, "SPACE / ENTER  →  Choose Character & Play", 22, GREEN_BRIGHT, (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 90))
            draw_text(screen, "Y  →  Shop       C  →  Characters", 20, LIGHT_BLUE, (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 55))

        # ════════════════════════════════════════════════════════════════════
        elif state == CHAR_SELECT:
            draw_wavy_title(screen, "CHOOSE YOUR HERO", 42, 55, ACCENT)
            draw_text(screen, "← / → to browse     ENTER to play     ESC to go back", 16,
                      LIGHT_BLUE, (WINDOW_WIDTH // 2, 108))

            # Draw 3 character cards side by side
            card_w, card_h = 150, 260
            gap        = 20
            total_w    = card_w * 3 + gap * 2
            start_x    = WINDOW_WIDTH // 2 - total_w // 2
            cards_y    = 130

            for ci, char in enumerate(CHARACTERS):
                cx = start_x + ci * (card_w + gap)
                card_rect = pygame.Rect(cx, cards_y, card_w, card_h)
                is_sel = (ci == selected_char_id)

                # Card panel – glow border if selected
                border_col = char["color"] if is_sel else (40, 55, 80)
                bg_alpha   = 230 if is_sel else 140
                draw_panel(screen, card_rect, alpha=bg_alpha, border_color=border_col, radius=14)

                # Pulsing glow behind selected card
                if is_sel:
                    t_g = now_ms / 600.0
                    glow_a = int(40 + 30 * math.sin(t_g * 2))
                    glow_s = pygame.Surface((card_w + 20, card_h + 20), pygame.SRCALPHA)
                    pygame.draw.rect(glow_s,
                                     (*char["color"][:3], glow_a),
                                     glow_s.get_rect(), border_radius=18)
                    screen.blit(glow_s, (cx - 10, cards_y - 10))

                # Character sprite (centred, larger if selected)
                sp_size = (110, 121) if is_sel else (90, 99)
                preview = load_character_sprite(ci, sp_size)
                if preview:
                    sp_rect = preview.get_rect(centerx=cx + card_w // 2,
                                               top=cards_y + 14)
                    # Floating bob for selected
                    if is_sel:
                        bob = int(math.sin(now_ms / 350.0) * 4)
                        sp_rect = sp_rect.move(0, bob)
                    screen.blit(preview, sp_rect)
                else:
                    # fallback coloured silhouette
                    fb = pygame.Rect(cx + card_w // 4, cards_y + 14,
                                     card_w // 2, 100)
                    pygame.draw.rect(screen, char["color"], fb, border_radius=8)

                # Name
                name_y = cards_y + 145
                draw_text_shadow(screen, char["name"], 20, char["color"],
                                 (cx + card_w // 2, name_y))
                # Description
                draw_text(screen, char["desc"], 13, (180, 190, 210),
                          (cx + card_w // 2, name_y + 24))
                # Stat tag
                tag_col = GREEN_BRIGHT if is_sel else (120, 130, 150)
                draw_text(screen, char["stat"], 15, tag_col,
                          (cx + card_w // 2, name_y + 46))

                # Crown / checkmark if this is active char
                if ci == active_char_id:
                    draw_text(screen, "✦ current ✦", 12, GOLD,
                              (cx + card_w // 2, cards_y + card_h - 16))

            # Arrow indicators
            draw_text(screen, "◄", 28, CHARACTERS[selected_char_id]["color"],
                      (start_x - 22, cards_y + card_h // 2))
            draw_text(screen, "►", 28, CHARACTERS[selected_char_id]["color"],
                      (start_x + total_w + 22, cards_y + card_h // 2))

            # Confirm prompt
            confirm_y = cards_y + card_h + 36
            sel_char  = CHARACTERS[selected_char_id]
            conf_panel = pygame.Rect(60, confirm_y, WINDOW_WIDTH - 120, 70)
            draw_panel(screen, conf_panel, border_color=sel_char["color"])
            if (now_ms // 500) % 2 == 0:
                draw_text_shadow(screen,
                                 f"ENTER  →  Play as  {sel_char['name']}",
                                 24, sel_char["color"],
                                 (WINDOW_WIDTH // 2, confirm_y + 22))
            draw_text(screen, "ESC  →  Back to menu", 16, LIGHT_BLUE,
                      (WINDOW_WIDTH // 2, confirm_y + 50))

        # ════════════════════════════════════════════════════════════════════
        elif state == MODE_SELECT:
            draw_wavy_title(screen, "SELECT DIFFICULTY", 40, 60, GOLD)
            char_info = CHARACTERS[active_char_id]
            # Show chosen character as small badge
            prev = char_previews[active_char_id]
            if prev:
                sm = pygame.transform.smoothscale(prev, (40, 44))
                screen.blit(sm, (WINDOW_WIDTH // 2 - 80, 110))
            draw_text(screen, f"{char_info['name']}  ready!", 20, char_info["color"],
                      (WINDOW_WIDTH // 2 + 20, 132))

            draw_text(screen, "← / →  browse     ENTER  confirm     ESC  back", 15,
                      LIGHT_BLUE, (WINDOW_WIDTH // 2, 168))

            # Mode cards
            card_w, card_h = 160, 300
            gap     = 14
            total_w = card_w * 3 + gap * 2
            mx      = WINDOW_WIDTH // 2 - total_w // 2
            cards_y = 186

            for mi, mode in enumerate(GAME_MODES):
                cx = mx + mi * (card_w + gap)
                cr = pygame.Rect(cx, cards_y, card_w, card_h)
                is_sel = (mi == selected_mode_id)

                border_col = mode["color"] if is_sel else (40, 55, 80)
                bg_alpha   = 235 if is_sel else 130
                draw_panel(screen, cr, alpha=bg_alpha, border_color=border_col, radius=14)

                # Pulsing glow for selected
                if is_sel:
                    t_g = now_ms / 500.0
                    ga  = int(35 + 25 * math.sin(t_g * 2))
                    gs  = pygame.Surface((card_w + 22, card_h + 22), pygame.SRCALPHA)
                    pygame.draw.rect(gs, (*mode["color"][:3], ga),
                                     gs.get_rect(), border_radius=18)
                    screen.blit(gs, (cx - 11, cards_y - 11))

                # Big icon
                icon_size = 56 if is_sel else 44
                draw_text_shadow(screen, mode["icon"], icon_size, mode["color"],
                                 (cx + card_w // 2, cards_y + 46))

                # Mode name
                draw_text_shadow(screen, mode["name"], 26 if is_sel else 22,
                                 mode["color"], (cx + card_w // 2, cards_y + 96))

                # Description (word-wrap manually at ~20 chars)
                words = mode["desc"].split()
                lines_d, cur = [], ""
                for w in words:
                    if len(cur) + len(w) + 1 <= 20:
                        cur = (cur + " " + w).strip()
                    else:
                        lines_d.append(cur); cur = w
                if cur:
                    lines_d.append(cur)
                for li, ln in enumerate(lines_d):
                    draw_text(screen, ln, 14, (180, 190, 210),
                              (cx + card_w // 2, cards_y + 128 + li * 18))

                # Stats panel inside card
                stats_y = cards_y + 185
                stat_panel = pygame.Rect(cx + 10, stats_y, card_w - 20, 82)
                draw_panel(screen, stat_panel, alpha=160, border_color=border_col, radius=8)

                spd_label = ["Slow", "Normal", "Fast"][mi]
                spawn_label = ["Sparse", "Normal", "Dense"][mi]
                ramp_label  = ["Gentle", "Normal", "Steep"][mi]
                for si, (lbl, val) in enumerate([("Speed", spd_label),
                                                  ("Spawn", spawn_label),
                                                  ("Ramp",  ramp_label)]):
                    draw_text(screen, f"{lbl}: {val}", 13, WHITE,
                              (cx + card_w // 2, stats_y + 14 + si * 22))

                # Active marker
                if mi == active_mode_id:
                    draw_text(screen, "✦ active ✦", 12, GOLD,
                              (cx + card_w // 2, cards_y + card_h - 14))

            # Arrow indicators
            draw_text(screen, "◄", 28, GAME_MODES[selected_mode_id]["color"],
                      (mx - 22, cards_y + card_h // 2))
            draw_text(screen, "►", 28, GAME_MODES[selected_mode_id]["color"],
                      (mx + total_w + 22, cards_y + card_h // 2))

            # Confirm prompt
            sel_mode   = GAME_MODES[selected_mode_id]
            confirm_y  = cards_y + card_h + 22
            conf_panel = pygame.Rect(60, confirm_y, WINDOW_WIDTH - 120, 60)
            draw_panel(screen, conf_panel, border_color=sel_mode["color"])
            if (now_ms // 500) % 2 == 0:
                draw_text_shadow(screen,
                                 f"ENTER  →  Play on  {sel_mode['name']}",
                                 22, sel_mode["color"],
                                 (WINDOW_WIDTH // 2, confirm_y + 18))
            draw_text(screen, "ESC  →  Back to characters", 14, LIGHT_BLUE,
                      (WINDOW_WIDTH // 2, confirm_y + 42))

        # ════════════════════════════════════════════════════════════════════
        elif state == SHOP:
            draw_text_shadow(screen, "SHOP", 52, GOLD, (WINDOW_WIDTH // 2, 50))
            draw_hud_pill(screen, f"Coins: {total_coins_saved}", WINDOW_WIDTH // 2 - 70, 88,
                          bg=(40, 30, 10, 220), border=GOLD, size=22)

            draw_text(screen, "↑ / ↓  navigate     ENTER  buy     ESC  back", 15, LIGHT_BLUE,
                      (WINDOW_WIDTH // 2, 126))

            start_y = 150
            items_per_screen = 8
            item_h = 68
            scroll_offset = max(0, shop_selected_item - items_per_screen + 1)

            for i in range(len(shop_items)):
                di = i - scroll_offset
                if di < 0 or di >= items_per_screen:
                    continue
                item = shop_items[i]
                y = start_y + di * item_h
                is_sel = (i == shop_selected_item)
                can_afford = total_coins_saved >= item["price"]
                owned = player_powers[item["type"]]

                # Panel bg
                ir = pygame.Rect(28, y - 4, WINDOW_WIDTH - 56, item_h - 4)
                sel_border = GOLD if is_sel else (40, 55, 80)
                bg_alpha   = 220 if is_sel else 140
                draw_panel(screen, ir, alpha=bg_alpha, border_color=sel_border, radius=10)

                # Icon circle
                icon_col = GOLD if can_afford else (100, 60, 60)
                pygame.draw.circle(screen, icon_col, (ir.x + 22, ir.centery), 14)
                draw_text(screen, item["key"], 13, BLACK, (ir.x + 22, ir.centery))

                # Name + price
                name_col = WHITE if can_afford else (180, 90, 90)
                draw_text(screen, item["name"], 19, name_col, (ir.x + 160, y + 12))
                price_col = GOLD if can_afford else RED
                draw_text(screen, f"{item['price']} 🪙", 17, price_col, (ir.right - 60, y + 12))
                draw_text(screen, item["description"], 14, LIGHT_BLUE, (ir.x + 160, y + 34))
                draw_text(screen, f"Owned: {owned}", 13, GREEN_BRIGHT if owned > 0 else (120, 120, 140),
                          (ir.right - 55, y + 34))

            if scroll_offset > 0:
                draw_text(screen, "▲", 18, LIGHT_BLUE, (WINDOW_WIDTH // 2, start_y - 8))
            if scroll_offset + items_per_screen < len(shop_items):
                draw_text(screen, "▼", 18, LIGHT_BLUE, (WINDOW_WIDTH // 2, start_y + items_per_screen * item_h + 2))

        # ════════════════════════════════════════════════════════════════════
        elif state == RUNNING:
            elapsed_ms      = now_ms - start_ticks_ms
            elapsed_seconds = elapsed_ms / 1000.0

            if int(elapsed_seconds) > last_score_second:
                last_score_second = int(elapsed_seconds)
                score = last_score_second

            difficulty = get_difficulty(elapsed_seconds)
            if now_ms < slow_motion_active_until:
                difficulty *= 0.8

            # ── TNT ──────────────────────────────────────────────────────────
            if not tnt_active and (last_tnt_spawn_ms == 0 or now_ms - last_tnt_spawn_ms >= TNT_INTERVAL_MS):
                tnt_w, tnt_h = 80, 36
                tnt_rect = pygame.Rect(-tnt_w, WINDOW_HEIGHT - 20 - tnt_h, tnt_w, tnt_h)
                tnt_active = True
                tnt_visible_until_ms = now_ms + TNT_DURATION_MS
                last_tnt_spawn_ms = now_ms
                tnt_velocity_x = TNT_SPEED_PX
            if tnt_active and now_ms > tnt_visible_until_ms:
                tnt_active = False; tnt_rect = None; tnt_velocity_x = 0
            if tnt_active and tnt_rect is not None:
                tnt_rect.x += tnt_velocity_x

            # ── Angel ─────────────────────────────────────────────────────────
            if not angel_active and (last_angel_spawn_ms == start_ticks_ms or
                                     now_ms - last_angel_spawn_ms >= ANGEL_INTERVAL_MS):
                angel_w, angel_h = 60, 80
                angel_rect = pygame.Rect(WINDOW_WIDTH // 2 - angel_w // 2, 550, angel_w, angel_h)
                angel_active = True
                angel_visible_until_ms = now_ms + ANGEL_DURATION_MS
                last_angel_spawn_ms = now_ms
            if angel_active and now_ms > angel_visible_until_ms:
                angel_active = False; angel_rect = None

            # ── Player input ──────────────────────────────────────────────────
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_SPACE] and player.is_on_ground():
                player.velocity_y = -24.0 if now_ms < super_jump_active_until else -16.0
            if pressed[pygame.K_j] and j_keys_available > 0:
                chickens.clear(); coins.clear(); j_keys_available -= 1
                spawn_hit_particles(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, 30)
            if pressed[pygame.K_k] and coins_collected >= coins_for_j_key:
                coins_collected -= coins_for_j_key; j_keys_available += 1
            if pressed[pygame.K_f] and time_freeze_uses_remaining > 0 and now_ms > time_frozen_until:
                time_freeze_uses_remaining -= 1; time_frozen_until = now_ms + 3000

            player.speed = int(8 * 1.25) if now_ms < speed_boost_active_until else 8
            player.update(pressed)

            # ── Spawn chickens ────────────────────────────────────────────────
            if last_spawn_ms == 0:
                last_spawn_ms = now_ms
            _mode = GAME_MODES[active_mode_id]
            base_interval = int(spawn_interval_ms * _mode["spawn_mult"])
            dyn_interval = max(180, int(base_interval - difficulty * 120))
            if now_ms - last_spawn_ms >= dyn_interval:
                last_spawn_ms = now_ms
                sx = random.randint(10, WINDOW_WIDTH - 51)
                spd = (2.7 + random.random() * 1.35) * _mode["speed_mult"]
                c = Chicken(sx, width=41, height=41, fall_speed=spd)
                c.set_difficulty_bonus(difficulty * 0.9)
                chickens.append(c)

            # ── Spawn coins ───────────────────────────────────────────────────
            if last_coin_spawn_ms == 0:
                last_coin_spawn_ms = now_ms
            coin_interval = coin_spawn_interval_ms // 2 if now_ms < coin_rain_active_until else coin_spawn_interval_ms
            if now_ms - last_coin_spawn_ms >= coin_interval:
                last_coin_spawn_ms = now_ms
                sx = random.randint(10, WINDOW_WIDTH - 40)
                spd = (2.0 + random.random()) * _mode["speed_mult"]
                co = Coin(sx, width=30, height=30, fall_speed=spd)
                co.set_difficulty_bonus(difficulty * 0.5)
                coins.append(co)

            # ── Update entities ───────────────────────────────────────────────
            frozen = now_ms <= time_frozen_until
            if not frozen:
                for ch in chickens:
                    ch.set_difficulty_bonus(difficulty * 0.9); ch.update()
                last_coin_ref = None
                for co in coins:
                    co.set_difficulty_bonus(difficulty * 0.5); co.update()
                    last_coin_ref = co
                # Coin magnet
                if now_ms < coin_magnet_active_until and last_coin_ref is not None:
                    for co in coins:
                        dx = player.rect.centerx - co.rect.centerx
                        dy = player.rect.centery - co.rect.centery
                        dist = math.hypot(dx, dy)
                        if 0 < dist < 150:
                            co.rect.x += int(dx / dist * 3)
                            co.rect.y += int(dy / dist * 3)

            chickens = [c for c in chickens if not c.is_off_screen()]
            coins     = [c for c in coins    if not c.is_off_screen()]

            # ── Collisions ────────────────────────────────────────────────────
            if now_ms >= invulnerable_until_ms:
                hit = False
                for ch in chickens[:]:
                    if player.rect.colliderect(ch.rect):
                        if now_ms < lucky_charm_active_until and random.random() < 0.25:
                            continue
                        if ghost_phases_remaining > 0:
                            ghost_phases_remaining -= 1; continue
                        if shield_hits_remaining > 0:
                            shield_hits_remaining -= 1
                            invulnerable_until_ms = now_ms + 1000
                            spawn_hit_particles(ch.rect.centerx, ch.rect.centery, 12)
                            continue
                        lives -= 1
                        invulnerable_until_ms = now_ms + 1000
                        spawn_hit_particles(player.rect.centerx, player.rect.centery, 20)
                        trigger_shake(8, 350)
                        try:
                            if hit_sound: hit_sound.play()
                        except Exception:
                            pass
                        hit = True
                        if lives <= 0:
                            state = GAME_OVER
                            final_score = score
                        break

                # TNT
                if tnt_active and tnt_rect and player.rect.colliderect(tnt_rect):
                    lives -= 1
                    invulnerable_until_ms = now_ms + 1000
                    spawn_hit_particles(tnt_rect.centerx, tnt_rect.centery, 30)
                    trigger_shake(12, 500)
                    tnt_active = False; tnt_rect = None
                    try:
                        if hit_sound: hit_sound.play()
                    except Exception:
                        pass
                    if lives <= 0:
                        state = GAME_OVER; final_score = score

                # Angel
                if angel_active and angel_rect and player.rect.colliderect(angel_rect):
                    lives = min(5, lives + 2)
                    angel_active = False; angel_rect = None
                    # Healing sparkles
                    for _ in range(20):
                        ax = angel_rect.centerx + random.randint(-20, 20) if angel_rect else player.rect.centerx
                        ay = player.rect.centery
                        _particles.append(Particle(ax, ay, (255, 255, 180),
                                                    vx=random.uniform(-2, 2),
                                                    vy=random.uniform(-4, -1),
                                                    life=30, size=3))

                # Coins
                for co in coins[:]:
                    if player.rect.colliderect(co.rect):
                        coins.remove(co)
                        val = 2 if now_ms < double_coins_active_until else 1
                        coins_collected += val
                        spawn_coin_particles(co.rect.centerx, co.rect.centery)

            # ── Draw entities (with shake offset) ─────────────────────────────
            # Draw with screen offset for shake
            draw_offset = (shake_x, shake_y)

            for ch in chickens:
                r = ch.rect.move(*draw_offset)
                orig_rect = ch.rect
                ch.rect = r
                ch.draw(screen)
                ch.rect = orig_rect

            for co in coins:
                r = co.rect.move(*draw_offset)
                orig_rect = co.rect
                co.rect = r
                co.draw(screen)
                co.rect = orig_rect

            # TNT
            if tnt_active and tnt_rect:
                draw_tnt(screen, tnt_rect.move(*draw_offset))

            # Angel
            if angel_active and angel_rect:
                draw_angel(screen, angel_rect.move(*draw_offset))

            # Player
            blink = now_ms < invulnerable_until_ms and (now_ms // 100) % 2 == 0
            if not blink:
                pr = player.rect.move(*draw_offset)
                orig = player.rect
                player.rect = pr
                player.draw(screen,
                            shield_active=shield_hits_remaining > 0,
                            ghost_active=ghost_phases_remaining > 0)
                player.rect = orig

            # Particles
            update_and_draw_particles(screen)

            # Time freeze overlay
            if frozen:
                frost = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                frost.fill((100, 180, 255, 30))
                screen.blit(frost, (0, 0))
                draw_text_shadow(screen, "⏸  TIME FROZEN", 26, ACCENT, (WINDOW_WIDTH // 2, 44))

            # ── HUD ───────────────────────────────────────────────────────────
            draw_hud_pill(screen, f"Score  {score}", 8, 8,   bg=(10,20,50,200), border=ACCENT, size=20)
            draw_hud_pill(screen, f"🪙 {coins_collected}", 8, 40, bg=(40,30,10,200), border=GOLD,  size=18)
            draw_hud_pill(screen, f"J ×{j_keys_available}", 8, 68, bg=(20,40,20,200), border=GREEN_BRIGHT, size=16)
            # Mode badge (top centre)
            _am = GAME_MODES[active_mode_id]
            draw_hud_pill(screen, f"{_am['icon']} {_am['name']}",
                          WINDOW_WIDTH // 2 - 46, 8,
                          bg=(10, 20, 40, 200), border=_am["color"], size=16)
            draw_hearts(screen, lives, max_hearts=6)

            # Active power bars
            hud_y = 98
            bar_w = 150
            if now_ms < speed_boost_active_until:
                frac = (speed_boost_active_until - now_ms) / 10000
                draw_power_timer_bar(screen, "⚡ Speed", frac, hud_y, ACCENT, bar_w); hud_y += 18
            if now_ms < coin_magnet_active_until:
                frac = (coin_magnet_active_until - now_ms) / 15000
                draw_power_timer_bar(screen, "🧲 Magnet", frac, hud_y, GOLD, bar_w); hud_y += 18
            if now_ms < slow_motion_active_until:
                frac = (slow_motion_active_until - now_ms) / 12000
                draw_power_timer_bar(screen, "🐌 Slow", frac, hud_y, LIGHT_BLUE, bar_w); hud_y += 18
            if now_ms < super_jump_active_until:
                frac = (super_jump_active_until - now_ms) / 20000
                draw_power_timer_bar(screen, "🚀 Jump", frac, hud_y, GREEN_BRIGHT, bar_w); hud_y += 18
            if now_ms < double_coins_active_until:
                frac = (double_coins_active_until - now_ms) / 30000
                draw_power_timer_bar(screen, "💰 ×2 Coins", frac, hud_y, GOLD, bar_w); hud_y += 18
            if now_ms < lucky_charm_active_until:
                frac = (lucky_charm_active_until - now_ms) / 25000
                draw_power_timer_bar(screen, "🍀 Lucky", frac, hud_y, GREEN_BRIGHT, bar_w); hud_y += 18
            if now_ms < coin_rain_active_until:
                frac = (coin_rain_active_until - now_ms) / 20000
                draw_power_timer_bar(screen, "🌧️ Rain", frac, hud_y, LIGHT_BLUE, bar_w); hud_y += 18
            if time_freeze_uses_remaining > 0:
                draw_power_timer_bar(screen, f"⏰ Freeze ×{time_freeze_uses_remaining} (F)", 1.0, hud_y, ACCENT, bar_w); hud_y += 18
            if shield_hits_remaining > 0:
                draw_power_timer_bar(screen, f"🛡️ Shield ×{shield_hits_remaining}", 1.0, hud_y, WHITE, bar_w); hud_y += 18
            if ghost_phases_remaining > 0:
                draw_power_timer_bar(screen, f"👻 Ghost ×{ghost_phases_remaining}", 1.0, hud_y, LIGHT_BLUE, bar_w); hud_y += 18

            # Available powers hint (compact)
            avail = []
            km = {"extra_life":"1","speed_boost":"2","coin_magnet":"3","j_key_pack":"4",
                  "slow_motion":"5","super_jump":"6","shield":"7","double_coins":"8",
                  "lucky_charm":"9","time_freeze":"0","coin_rain":"Q","ghost_mode":"W"}
            for pt, cnt in player_powers.items():
                if cnt > 0:
                    avail.append(f"{km.get(pt,'?')}×{cnt}")
            if avail:
                draw_hud_pill(screen, "  ".join(avail), 8, hud_y,
                              bg=(10,20,40,180), border=(60,80,120), size=13)
                hud_y += 18

            if coins_collected >= coins_for_j_key:
                draw_text_shadow(screen, f"Hold K → J key ({coins_for_j_key}🪙)", 14, GOLD,
                                 (115, WINDOW_HEIGHT - 28))

        # ════════════════════════════════════════════════════════════════════
        elif state == GAME_OVER:
            # Dark overlay
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            draw_gradient_rect(overlay, (0, 0, 20, 220), (0, 0, 40, 180),
                               pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT))
            screen.blit(overlay, (0, 0))

            # Pulsing title
            t = now_ms / 400.0
            pulse = int(10 * abs(math.sin(t)))
            draw_wavy_title(screen, "GAME OVER", 56 + pulse // 2, 90, RED)

            fs = locals().get("final_score", score)
            panel_r = pygame.Rect(60, 155, WINDOW_WIDTH - 120, 200)
            draw_panel(screen, panel_r, alpha=230, border_color=ACCENT)
            _gom = GAME_MODES[active_mode_id]
            draw_text(screen, f"{_gom['icon']} {_gom['name']}  ·  {CHARACTERS[active_char_id]['name']}",
                      16, _gom["color"], (WINDOW_WIDTH // 2, 170))
            draw_text_shadow(screen, f"Score:  {fs}", 32, WHITE, (WINDOW_WIDTH // 2, 198))
            draw_text_shadow(screen, f"Coins this game:  {coins_collected}", 22, GOLD, (WINDOW_WIDTH // 2, 236))
            draw_text_shadow(screen, f"Total coins:  {total_coins_saved + coins_collected}", 18, GOLD, (WINDOW_WIDTH // 2, 264))
            if not name_saved:
                draw_text(screen, "Enter your name:", 22, LIGHT_BLUE, (WINDOW_WIDTH // 2, 300))
                caret = "_" if (now_ms // 400) % 2 == 0 else " "
                draw_text_shadow(screen, name_input + caret, 28, WHITE, (WINDOW_WIDTH // 2, 330))
                draw_text(screen, "ENTER to save", 17, LIGHT_BLUE, (WINDOW_WIDTH // 2, 360))
            else:
                draw_text_shadow(screen, "✓  Saved!", 22, GREEN_BRIGHT, (WINDOW_WIDTH // 2, 320))

            # ── Per-difficulty Leaderboard ────────────────────────────────
            hs_r = pygame.Rect(14, 372, WINDOW_WIDTH - 28, 378)
            draw_panel(screen, hs_r, alpha=200, border_color=ACCENT)
            draw_text_shadow(screen, "LEADERBOARD", 22, ACCENT, (WINDOW_WIDTH // 2, 390))

            # Three columns, one per difficulty
            col_w    = (WINDOW_WIDTH - 28) // 3
            medals3  = ["🥇", "🥈", "🥉", "4.", "5."]
            for ci, (dk, mode) in enumerate(zip(DIFF_KEYS, GAME_MODES)):
                cx = 14 + ci * col_w + col_w // 2
                col_rows = scores_by_diff.get(dk, [])

                # Column header with mode colour + icon
                header_r = pygame.Rect(14 + ci * col_w + 4, 406, col_w - 8, 26)
                hs = pygame.Surface((col_w - 8, 26), pygame.SRCALPHA)
                pygame.draw.rect(hs, (*mode["color"][:3], 60), hs.get_rect(), border_radius=6)
                screen.blit(hs, header_r.topleft)
                pygame.draw.rect(screen, mode["color"], header_r, 1, border_radius=6)
                draw_text(screen, f"{mode['icon']} {mode['name']}", 15, mode["color"], (cx, 419))

                # Highlight active mode column header
                if ci == active_mode_id:
                    pygame.draw.rect(screen, mode["color"], header_r, 2, border_radius=6)

                if not col_rows:
                    draw_text(screen, "No scores yet", 12, (100, 110, 130), (cx, 455))
                else:
                    for ri, row in enumerate(col_rows[:5]):
                        entry_name  = str(row.get("name", "Player"))[:10]
                        entry_score = int(row.get("score", 0))
                        ey = 440 + ri * 56

                        # Row panel
                        row_r = pygame.Rect(14 + ci * col_w + 4, ey - 2, col_w - 8, 50)
                        row_bg_alpha = 120 if ri % 2 == 0 else 70
                        rs = pygame.Surface((col_w - 8, 50), pygame.SRCALPHA)
                        pygame.draw.rect(rs, (255, 255, 255, row_bg_alpha // 6),
                                         rs.get_rect(), border_radius=5)
                        screen.blit(rs, row_r.topleft)

                        # Medal
                        medal_col = GOLD if ri == 0 else (200, 200, 180) if ri < 3 else (140, 150, 165)
                        draw_text(screen, medals3[ri], 14, medal_col, (cx, ey + 8))
                        # Name
                        draw_text(screen, entry_name, 13, WHITE, (cx, ey + 25))
                        # Score
                        draw_text(screen, str(entry_score), 15, GOLD if ri == 0 else medal_col,
                                  (cx, ey + 41))

                # Vertical divider between columns (except after last)
                if ci < 2:
                    div_x = 14 + (ci + 1) * col_w
                    pygame.draw.line(screen, (50, 65, 90),
                                     (div_x, 406), (div_x, hs_r.bottom - 6), 1)

            if (now_ms // 700) % 2 == 0:
                draw_text_shadow(screen, "R  →  Choose Character & Restart", 22, GREEN_BRIGHT, (WINDOW_WIDTH // 2, WINDOW_HEIGHT - 35))

        # ── Flip ─────────────────────────────────────────────────────────────
        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
