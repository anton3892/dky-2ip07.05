"""
╔══════════════════════════════════════════════════════════════════════╗
║         УЛЬТРА ХАОС МОД v9000 ULTRA — PYGAME EDITION               ║
║         Переписан на pygame: нет лагов, нет вылетов!                ║
║         ESC / Q — выход                                              ║
╚══════════════════════════════════════════════════════════════════════╝

Требования:  pip install pygame numpy
"""

import pygame
import numpy as np
import math
import random
import sys
import colorsys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════
#  НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════════════

TARGET_FPS   = 60
WIDTH        = 1280
HEIGHT       = 720
TITLE        = "🔥 УЛЬТРА ХАОС МОД v9000 ULTRA 🔥"

# Цвета
BLACK   = (0,   0,   0)
WHITE   = (255, 255, 255)
RED     = (255,  50,  50)
GREEN   = ( 50, 255,  50)
BLUE    = ( 50, 100, 255)
YELLOW  = (255, 255,   0)
CYAN    = (  0, 255, 255)
MAGENTA = (255,   0, 255)
ORANGE  = (255, 165,   0)

CX = WIDTH  // 2
CY = HEIGHT // 2

# ═══════════════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════

def hsv_color(h: float, s: float = 1.0, v: float = 1.0) -> Tuple[int,int,int]:
    """HSV -> RGB (0-255)"""
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r*255), int(g*255), int(b*255))

def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0]-c1[0])*t),
        int(c1[1] + (c2[1]-c1[1])*t),
        int(c1[2] + (c2[2]-c1[2])*t),
    )

def add_alpha(col, alpha: int) -> Tuple[int,int,int,int]:
    return (col[0], col[1], col[2], max(0, min(255, alpha)))

def rand_color() -> Tuple[int,int,int]:
    return hsv_color(random.random())

def rot2d(x, y, angle):
    c, s = math.cos(angle), math.sin(angle)
    return x*c - y*s, x*s + y*c

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def safe_circle(surf, color, center, radius):
    """Рисует круг только если радиус > 0"""
    r = int(abs(radius))
    if r < 1:
        return
    try:
        pygame.draw.circle(surf, color, (int(center[0]), int(center[1])), r)
    except Exception:
        pass

def rand_screen_pos():
    return (random.randint(0, WIDTH), random.randint(0, HEIGHT))

RAINBOW_COLS = [
    (255,  50,  50),
    (255, 165,   0),
    (255, 255,   0),
    ( 50, 255,  50),
    (  0, 200, 255),
    (150,  50, 255),
    (255,  50, 200),
]

# ═══════════════════════════════════════════════════════════════════════
#  PLASMA SURFACE (предрасчитанный цветовой градиент)
# ═══════════════════════════════════════════════════════════════════════

PLASMA_W, PLASMA_H = 64, 64

def make_plasma_surface():
    surf = pygame.Surface((PLASMA_W, PLASMA_H))
    for y in range(PLASMA_H):
        for x in range(PLASMA_W):
            v = (math.sin(x/8.0) + math.sin(y/8.0)) * 0.5 + 0.5
            col = hsv_color(v)
            surf.set_at((x, y), col)
    return surf

# ═══════════════════════════════════════════════════════════════════════
#  СИСТЕМА ЧАСТИЦ — базовый класс
# ═══════════════════════════════════════════════════════════════════════

class Particle:
    __slots__ = ['x','y','vx','vy','life','max_life','hue','size','grav']

    def __init__(self, x, y, vx=0.0, vy=0.0, life=60,
                 hue=0.0, size=3.0, grav=0.0):
        self.x, self.y   = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.life        = float(life)
        self.max_life    = float(life)
        self.hue         = float(hue)
        self.size        = float(size)
        self.grav        = float(grav)

    def update(self):
        self.x    += self.vx
        self.y    += self.vy
        self.vy   += self.grav
        self.life -= 1.0
        return self.life > 0

    @property
    def alive(self):
        return self.life > 0

    @property
    def frac(self):
        return max(0.0, self.life / self.max_life)

    def draw(self, surf):
        alpha = int(self.frac * 255)
        col   = hsv_color(self.hue, 1.0, self.frac)
        r     = max(1, int(self.size * self.frac))
        safe_circle(surf, col, (int(self.x), int(self.y)), r)


# ═══════════════════════════════════════════════════════════════════════
#  ПУЛ ЧАСТИЦ (переиспользуем объекты)
# ═══════════════════════════════════════════════════════════════════════

MAX_PARTICLES = 4000

class ParticlePool:
    def __init__(self, capacity=MAX_PARTICLES):
        self.pool: List[Particle] = []
        self.capacity = capacity

    def spawn(self, x, y, vx=0, vy=0, life=60, hue=0.0, size=3.0, grav=0.0):
        if len(self.pool) >= self.capacity:
            return
        self.pool.append(Particle(x, y, vx, vy, life, hue, size, grav))

    def burst(self, x, y, n=30, speed=4.0, life=80, size=3.0,
              hue=None, spread_hue=0.15, grav=0.05):
        for _ in range(n):
            angle = random.uniform(0, math.tau)
            sp    = random.uniform(0.3, speed)
            vx    = sp * math.cos(angle)
            vy    = sp * math.sin(angle)
            h     = (random.random() if hue is None
                     else (hue + random.uniform(-spread_hue, spread_hue))) % 1.0
            li    = int(life * random.uniform(0.6, 1.4))
            sz    = size * random.uniform(0.5, 1.8)
            self.spawn(x, y, vx, vy, li, h, sz, grav)

    def update_and_draw(self, surf):
        dead = []
        for i, p in enumerate(self.pool):
            if not p.update():
                dead.append(i)
            else:
                p.draw(surf)
        for i in reversed(dead):
            self.pool.pop(i)

    def count(self):
        return len(self.pool)


# ═══════════════════════════════════════════════════════════════════════
#  ШЛЕЙФ (TRAIL)
# ═══════════════════════════════════════════════════════════════════════

class Trail:
    def __init__(self, max_len=60, width=3):
        self.points = []
        self.max_len = max_len
        self.width   = width
        self.hue_offset = random.random()

    def add(self, x, y):
        self.points.append((x, y))
        if len(self.points) > self.max_len:
            self.points.pop(0)

    def draw(self, surf, t):
        n = len(self.points)
        if n < 2:
            return
        for i in range(1, n):
            frac = i / n
            hue  = (self.hue_offset + t * 0.2 + frac * 0.3) % 1.0
            col  = hsv_color(hue, 1.0, frac)
            w    = max(1, int(self.width * frac))
            try:
                pygame.draw.line(surf, col,
                    (int(self.points[i-1][0]), int(self.points[i-1][1])),
                    (int(self.points[i][0]),   int(self.points[i][1])), w)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ГЛАВНЫЙ КРУГ С ШЛЕЙФОМ
# ═══════════════════════════════════════════════════════════════════════

class MainCircleEffect:
    def __init__(self):
        self.angle   = 0.0
        self.radius  = 200
        self.speed   = 0.08   # рад/кадр (разумная скорость)
        self.trail   = Trail(max_len=80, width=4)
        self.hue     = 0.0
        self.pulse   = 0.0

        # Дополнительные орбиты
        self.orbits = []
        for i in range(5):
            self.orbits.append({
                'angle':  i * math.tau / 5,
                'radius': 120 + i * 30,
                'speed':  0.05 + i * 0.015,
                'hue':    i / 5.0,
                'trail':  Trail(max_len=40, width=2),
                'size':   6 + i * 2,
            })

        # Частицы кольца
        self.ring_particles = ParticlePool(capacity=600)
        self.spawn_timer = 0

    def update(self, t, particles: ParticlePool):
        self.angle += self.speed
        self.hue    = (self.hue + 0.003) % 1.0
        self.pulse  = (math.sin(t * 3) + 1) * 0.5

        px = CX + self.radius * math.cos(self.angle)
        py = CY + self.radius * math.sin(self.angle)
        self.trail.add(px, py)

        # Спавним частицы с орбиты
        self.spawn_timer += 1
        if self.spawn_timer % 2 == 0:
            particles.spawn(
                px, py,
                vx=random.uniform(-1.5, 1.5),
                vy=random.uniform(-1.5, 1.5),
                life=int(random.uniform(20, 50)),
                hue=self.hue,
                size=random.uniform(1.5, 4.0),
                grav=0.01
            )

        for orb in self.orbits:
            orb['angle'] += orb['speed']
            ox = CX + orb['radius'] * math.cos(orb['angle'])
            oy = CY + orb['radius'] * math.sin(orb['angle'])
            orb['trail'].add(ox, oy)

            if random.random() < 0.3:
                particles.spawn(
                    ox, oy,
                    vx=random.uniform(-1.0, 1.0),
                    vy=random.uniform(-1.0, 1.0),
                    life=int(random.uniform(15, 40)),
                    hue=(orb['hue'] + t*0.1) % 1.0,
                    size=random.uniform(1.0, 3.0),
                    grav=0.02
                )

    def draw(self, surf, t):
        # Рисуем орбиты
        for orb in self.orbits:
            hue = (orb['hue'] + t*0.15) % 1.0
            col = hsv_color(hue)
            r   = int(orb['radius'])
            pygame.draw.circle(surf, (*col, 40), (CX, CY), r, 1)
            orb['trail'].draw(surf, t)
            ox = int(CX + orb['radius'] * math.cos(orb['angle']))
            oy = int(CY + orb['radius'] * math.sin(orb['angle']))
            glow_circle(surf, col, (ox, oy), orb['size'], alpha=200)

        # Главное кольцо
        pulse_r = int(self.radius + 8 * self.pulse)
        hue_col = hsv_color(self.hue)
        pygame.draw.circle(surf, (*hue_col, 60), (CX, CY), pulse_r, 2)
        self.trail.draw(surf, t)

        # Точка на кольце
        px = int(CX + self.radius * math.cos(self.angle))
        py = int(CY + self.radius * math.sin(self.angle))
        dot_size = int(10 + 5 * self.pulse)
        glow_circle(surf, hue_col, (px, py), dot_size, alpha=255)


# ═══════════════════════════════════════════════════════════════════════
#  УТИЛИТА: СВЕЧЕНИЕ
# ═══════════════════════════════════════════════════════════════════════

def glow_circle(surf, color, center, radius, alpha=255, layers=4):
    for i in range(layers, 0, -1):
        r   = radius * i // layers * 2
        a   = alpha * i // (layers * layers)
        s   = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color[:3], a), (r+1, r+1), r)
        surf.blit(s, (int(center[0])-r-1, int(center[1])-r-1))
    safe_circle(surf, color, center, radius)


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ФЕЙЕРВЕРКИ
# ═══════════════════════════════════════════════════════════════════════

class FireworkShell:
    def __init__(self, x, y):
        self.x   = float(x)
        self.y   = float(y)
        self.vx  = random.uniform(-2, 2)
        self.vy  = random.uniform(-8, -14)
        self.hue = random.random()
        self.exploded = False
        self.trail = Trail(max_len=20, width=2)
        self.trail.hue_offset = self.hue

    def update(self):
        self.trail.add(self.x, self.y)
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.35
        if self.vy >= 0:
            self.exploded = True
        return not self.exploded and 0 < self.x < WIDTH and -100 < self.y < HEIGHT

    def draw(self, surf, t):
        self.trail.draw(surf, t)
        col = hsv_color(self.hue)
        safe_circle(surf, col, (int(self.x), int(self.y)), 4)


class FireworksEffect:
    def __init__(self, particles: ParticlePool):
        self.shells: List[FireworkShell] = []
        self.particles = particles
        self.timer = 0

    def launch(self, cx=None, cy=None):
        x = cx if cx is not None else random.randint(WIDTH//4, 3*WIDTH//4)
        y = cy if cy is not None else HEIGHT
        self.shells.append(FireworkShell(x, y))

    def explode(self, x, y, hue):
        n = random.randint(80, 160)
        self.particles.burst(x, y, n=n, speed=random.uniform(4, 9),
                              life=random.randint(60, 120),
                              size=random.uniform(2, 5),
                              hue=hue, spread_hue=0.15, grav=0.06)
        # Вторичный взрыв
        n2 = random.randint(20, 40)
        self.particles.burst(x, y, n=n2, speed=random.uniform(1, 3),
                              life=random.randint(30, 60),
                              size=random.uniform(1, 2.5),
                              hue=(hue+0.5)%1.0, spread_hue=0.3, grav=0.04)

    def update(self, t):
        self.timer += 1
        if self.timer % 25 == 0:
            self.launch()

        dead = []
        for i, sh in enumerate(self.shells):
            if not sh.update():
                self.explode(int(sh.x), int(sh.y), sh.hue)
                dead.append(i)
        for i in reversed(dead):
            self.shells.pop(i)

    def draw(self, surf, t):
        for sh in self.shells:
            sh.draw(surf, t)


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: МАТРИЦА ЦИФР
# ═══════════════════════════════════════════════════════════════════════

class MatrixEffect:
    COLS    = 48
    SPEED   = 3

    def __init__(self, font):
        self.font     = font
        col_w         = WIDTH // self.COLS
        self.columns  = []
        for i in range(self.COLS):
            self.columns.append({
                'x':     i * col_w + col_w // 2,
                'y':     random.randint(-HEIGHT, 0),
                'speed': random.randint(2, 6),
                'len':   random.randint(8, 24),
                'chars': [str(random.randint(0,9)) for _ in range(30)],
                'timer': 0,
            })
        self.alpha = 0
        self.active = False

    def activate(self):
        self.active = True
        self.alpha  = 255
        for col in self.columns:
            col['y'] = random.randint(-HEIGHT, 0)

    def deactivate(self):
        self.active = False
        self.alpha  = 0

    def update(self):
        if not self.active:
            return
        if self.alpha > 0:
            self.alpha = max(0, self.alpha - 1)
        for col in self.columns:
            col['y'] += col['speed']
            col['timer'] += 1
            if col['timer'] % 5 == 0:
                idx = random.randint(0, len(col['chars'])-1)
                col['chars'][idx] = str(random.randint(0, 9))
            if col['y'] > HEIGHT + 50:
                col['y'] = random.randint(-200, -10)
                col['speed'] = random.randint(2, 6)

    def draw(self, surf):
        if not self.active and self.alpha == 0:
            return
        for col in self.columns:
            for j, ch in enumerate(col['chars']):
                ry = int(col['y'] - j * 18)
                if ry < -20 or ry > HEIGHT + 20:
                    continue
                frac = 1.0 - j / len(col['chars'])
                a    = int(frac * self.alpha)
                if a < 5:
                    continue
                g   = int(frac * 255)
                col_c = (0, g, 0)
                ts  = self.font.render(ch, True, col_c)
                ts.set_alpha(a)
                surf.blit(ts, (col['x'] - 6, ry))


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ВОРТЕКС СПИРАЛЬ
# ═══════════════════════════════════════════════════════════════════════

class VortexEffect:
    N_ARMS = 8

    def __init__(self):
        self.angle  = 0.0
        self.active = False
        self.alpha  = 0
        self.hue    = 0.0

    def activate(self):
        self.active = True
        self.alpha  = 0

    def deactivate(self):
        self.active = False

    def update(self, t):
        self.angle += 0.04
        self.hue    = (self.hue + 0.005) % 1.0
        if self.active:
            self.alpha = min(255, self.alpha + 8)
        else:
            self.alpha = max(0, self.alpha - 8)

    def draw(self, surf, t):
        if self.alpha < 5:
            return
        vsurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for arm in range(self.N_ARMS):
            arm_offset = arm * math.tau / self.N_ARMS
            hue = (self.hue + arm / self.N_ARMS) % 1.0
            col = hsv_color(hue)
            pts = []
            for i in range(80):
                r   = i * 5.5
                th  = self.angle + arm_offset + i * 0.18
                px  = CX + r * math.cos(th)
                py  = CY + r * math.sin(th) * 0.7
                pts.append((int(px), int(py)))
            for i in range(1, len(pts)):
                frac = i / len(pts)
                a    = int(frac * self.alpha * 0.9)
                if a < 5:
                    continue
                try:
                    pygame.draw.line(vsurf, (*col, a), pts[i-1], pts[i], 2)
                except Exception:
                    pass
        surf.blit(vsurf, (0, 0))


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: 3D ПАРАЛЛЕЛЕПИПЕДЫ
# ═══════════════════════════════════════════════════════════════════════

BOX_EDGES = [
    (0,1),(1,2),(2,3),(3,0),
    (4,5),(5,6),(6,7),(7,4),
    (0,4),(1,5),(2,6),(3,7),
]

def box_vertices(w, h, d):
    hw, hh, hd = w/2, h/2, d/2
    return np.array([
        [-hw,-hh,-hd],[hw,-hh,-hd],[hw,hh,-hd],[-hw,hh,-hd],
        [-hw,-hh, hd],[hw,-hh, hd],[hw,hh, hd],[-hw,hh, hd],
    ], dtype=float)

def rot3d(pts, rx, ry, rz):
    Rx = np.array([[1,0,0],[0,np.cos(rx),-np.sin(rx)],[0,np.sin(rx),np.cos(rx)]])
    Ry = np.array([[np.cos(ry),0,np.sin(ry)],[0,1,0],[-np.sin(ry),0,np.cos(ry)]])
    Rz = np.array([[np.cos(rz),-np.sin(rz),0],[np.sin(rz),np.cos(rz),0],[0,0,1]])
    return pts @ (Rz @ Ry @ Rx).T

def proj3d(pts, fov=600):
    out = []
    for p in pts:
        z  = p[2] + fov
        px = int(p[0] * fov / z) + CX
        py = int(p[1] * fov / z) + CY
        out.append((px, py))
    return out

class Box3D:
    def __init__(self, ox, oy, w, h, d):
        self.ox   = ox
        self.oy   = oy
        self.verts= box_vertices(w, h, d)
        self.rx   = random.uniform(0, math.tau)
        self.ry   = random.uniform(0, math.tau)
        self.rz   = random.uniform(0, math.tau)
        self.wrx  = random.uniform(0.01, 0.04)
        self.wry  = random.uniform(0.01, 0.04)
        self.wrz  = random.uniform(0.005, 0.025)
        self.hue  = random.random()
        self.scale= random.uniform(40, 120)

    def update(self):
        self.rx  += self.wrx
        self.ry  += self.wry
        self.rz  += self.wrz
        self.hue  = (self.hue + 0.002) % 1.0

    def draw(self, surf, t):
        s   = self.verts * self.scale
        rv  = rot3d(s, self.rx, self.ry, self.rz)
        rv[:,0] += self.ox - CX
        rv[:,1] += self.oy - CY
        pr  = proj3d(rv)
        col = hsv_color(self.hue)
        for e0, e1 in BOX_EDGES:
            try:
                pygame.draw.line(surf, col, pr[e0], pr[e1], 2)
            except Exception:
                pass


class BoxesEffect:
    def __init__(self):
        self.boxes: List[Box3D] = []
        n = 14
        for i in range(n):
            ang = i * math.tau / n
            r   = random.randint(250, 480)
            ox  = int(CX + r * math.cos(ang))
            oy  = int(CY + r * math.sin(ang) * 0.65)
            ox  = clamp(ox, 50, WIDTH-50)
            oy  = clamp(oy, 50, HEIGHT-50)
            w   = random.uniform(0.5, 1.5)
            h   = random.uniform(0.5, 1.5)
            d   = random.uniform(0.5, 1.5)
            self.boxes.append(Box3D(ox, oy, w, h, d))

    def update(self, t):
        for b in self.boxes:
            b.update()

    def draw(self, surf, t):
        for b in self.boxes:
            b.draw(surf, t)


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ТРЕУГОЛЬНИКИ
# ═══════════════════════════════════════════════════════════════════════

class TrianglesEffect:
    N      = 24
    BASE   = [(0, -100), (-87, 50), (87, 50)]

    def __init__(self):
        self.angle = 0.0
        self.hue   = 0.0

    def update(self, t):
        self.angle += 0.025
        self.hue    = (self.hue + 0.004) % 1.0

    def draw(self, surf, t):
        tsurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(self.N):
            a   = self.angle - i * 0.18
            hue = (self.hue + i * 0.04) % 1.0
            col = hsv_color(hue)
            alpha = int(255 * (self.N - i) / self.N * 0.8)
            pts = []
            for bx, by in self.BASE:
                rx, ry = rot2d(bx, by, a)
                pts.append((int(CX + rx), int(CY + ry)))
            try:
                pygame.draw.polygon(tsurf, (*col, alpha), pts, 0 if i < 3 else 2)
            except Exception:
                pass
        surf.blit(tsurf, (0, 0))


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ЗВЁЗДЫ (фоновое поле)
# ═══════════════════════════════════════════════════════════════════════

class StarsEffect:
    N = 250

    def __init__(self):
        self.stars = []
        for _ in range(self.N):
            self.stars.append({
                'x':    random.randint(0, WIDTH),
                'y':    random.randint(0, HEIGHT),
                'r':    random.uniform(0.5, 2.5),
                'hue':  random.random(),
                'blink':random.uniform(0, math.tau),
                'speed':random.uniform(0.02, 0.12),
            })

    def update(self, t):
        for s in self.stars:
            s['blink'] += s['speed']

    def draw(self, surf, t):
        for s in self.stars:
            bright = (math.sin(s['blink']) + 1) * 0.5
            col    = hsv_color(s['hue'], 0.3, 0.5 + 0.5 * bright)
            r      = max(1, int(s['r'] + bright * 1.5))
            safe_circle(surf, col, (int(s['x']), int(s['y'])), r)


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: СКРИМЕР + НАДПИСЬ
# ═══════════════════════════════════════════════════════════════════════

SCREAM_MESSAGES = [
    "ХАОС АКТИВИРОВАН!",
    "ВСЁ СЛОМАЛОСЬ!!!",
    "ПАНИКА!!! ПАНИКА!!!",
    "ЗАПУСКАЙ СИСТЕМУ!",
    "ЭТО КОНЕЦ... ИЛИ НЕТ?",
    "МАТРИЦА РУХНУЛА!",
    "ПЕРЕЗАГРУЗКА!!!",
    "ВНИМАНИЕ! ВНИМАНИЕ!",
]

FACES = ['😱', '💀', '👁️', '😈', '🤡', '👻', '☠️', '🔥', '⚡', '🌀']

class ScreamEffect:
    def __init__(self, font_big, font_med):
        self.font_big = font_big
        self.font_med = font_med
        self.active   = False
        self.timer    = 0
        self.duration = 180
        self.message  = ""
        self.face     = ""
        self.hue      = 0.0
        self.jitter_x = 0
        self.jitter_y = 0
        self.bg_hue   = 0.0

    def activate(self):
        self.active   = True
        self.timer    = self.duration
        self.message  = random.choice(SCREAM_MESSAGES)
        self.face     = random.choice(FACES)
        self.hue      = random.random()
        self.bg_hue   = random.random()

    def update(self, particles: ParticlePool):
        if not self.active:
            return
        self.timer -= 1
        if self.timer <= 0:
            self.active = False
            return

        self.hue = (self.hue + 0.02) % 1.0
        self.jitter_x = random.randint(-8, 8)
        self.jitter_y = random.randint(-4, 4)

        # Взрыв частиц по краям
        if self.timer % 4 == 0:
            edge = random.choice(['top','bot','left','right'])
            if edge == 'top':
                px, py = random.randint(0, WIDTH), 0
            elif edge == 'bot':
                px, py = random.randint(0, WIDTH), HEIGHT
            elif edge == 'left':
                px, py = 0, random.randint(0, HEIGHT)
            else:
                px, py = WIDTH, random.randint(0, HEIGHT)
            particles.burst(px, py, n=12, speed=5, life=60,
                            hue=self.hue, size=3, grav=0.05)

    def draw(self, surf, t):
        if not self.active and self.timer <= 0:
            return
        prog = self.timer / self.duration
        a    = int(min(prog * 3, 1.0) * 200)
        bg   = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        bg_c = hsv_color(self.bg_hue, 1.0, 0.6)
        bg.fill((*bg_c, a))
        surf.blit(bg, (0, 0))

        col  = hsv_color(self.hue)
        sz   = int(72 + 20 * abs(math.sin(self.timer * 0.1)))
        try:
            f   = pygame.font.SysFont('Arial', sz, bold=True)
            txt = f.render(self.message, True, col)
            x   = CX - txt.get_width()//2 + self.jitter_x
            y   = CY//2 + self.jitter_y
            surf.blit(txt, (x, y))

            sub = self.font_med.render("ПАНИКА | CHAOS | PANIC", True, WHITE)
            sx  = CX - sub.get_width()//2 + self.jitter_x//2
            surf.blit(sub, (sx, CY//2 + sz + 20))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ВЗРЫВНЫЕ НАДПИСИ
# ═══════════════════════════════════════════════════════════════════════

BANGS = [
    'ХАОС!', 'BOOM!', 'ВАУ!', 'PANIC!', 'КАК?!', 'ААААА!',
    'ЧТО?!', '🔥🔥🔥', 'МОЩЬ!', 'ЕПТА!!!', 'ВЗРЫВ!!!', 'POWER!',
    'MAX!!!', 'GG', 'WTF?!', '!!!', 'ULTRA!', 'OMG!!!'
]

BANG_COLORS = [RED, ORANGE, YELLOW, CYAN, MAGENTA, WHITE, GREEN]

class BangEffect:
    def __init__(self):
        self.items = []
        self.timer = 0

    def fire(self):
        self.items.append({
            'text':  random.choice(BANGS),
            'x':     random.randint(WIDTH//6, 5*WIDTH//6),
            'y':     random.randint(HEIGHT//6, 5*HEIGHT//6),
            'life':  int(random.uniform(40, 80)),
            'max_life': 60,
            'col':   random.choice(BANG_COLORS),
            'scale': random.uniform(0.8, 1.5),
            'rot':   random.uniform(-0.3, 0.3),
        })

    def update(self, t):
        self.timer += 1
        if self.timer % int(1.8 * TARGET_FPS) == int(TARGET_FPS * 0.3):
            self.fire()
        self.items = [b for b in self.items if b['life'] > 0]
        for b in self.items:
            b['life'] -= 1

    def draw(self, surf, t):
        for b in self.items:
            prog = b['life'] / b['max_life']
            sz   = int(50 * b['scale'] * (1.0 + 0.4 * math.sin(b['life'] * 0.4)))
            try:
                f   = pygame.font.SysFont('Arial', sz, bold=True)
                txt = f.render(b['text'], True, b['col'])
                txt.set_alpha(int(prog * 255))
                surf.blit(txt, (b['x'] - txt.get_width()//2,
                                b['y'] - txt.get_height()//2))
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ПЛАЗМЕННЫЕ ВОЛНЫ
# ═══════════════════════════════════════════════════════════════════════

class PlasmaWaveEffect:
    def __init__(self):
        self.phase  = 0.0
        self.active = False
        self.alpha  = 0

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def update(self, t):
        self.phase += 0.05
        if self.active:
            self.alpha = min(255, self.alpha + 5)
        else:
            self.alpha = max(0, self.alpha - 5)

    def draw(self, surf, t):
        if self.alpha < 5:
            return
        step = 6
        for y in range(0, HEIGHT, step):
            for x in range(0, WIDTH, step):
                v  = (math.sin((x/80.0) + self.phase) +
                      math.sin((y/60.0) + self.phase * 0.7) +
                      math.sin((x+y)/100.0 + self.phase * 1.3)) / 3.0
                hue = (v + 1) * 0.5
                col = hsv_color(hue, 1.0, 0.8)
                a   = self.alpha // 5
                try:
                    pygame.draw.rect(surf, (*col, a),
                                     (x, y, step, step))
                except Exception:
                    pass


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: LIGHTNING (МОЛНИЯ)
# ═══════════════════════════════════════════════════════════════════════

class LightningBolt:
    def __init__(self, x1, y1, x2, y2, hue=0.6, depth=4, spread=40):
        self.hue     = hue
        self.segments = []
        self._generate(x1, y1, x2, y2, depth, spread)
        self.life    = random.randint(4, 12)
        self.max_life= self.life

    def _generate(self, x1, y1, x2, y2, depth, spread):
        if depth == 0:
            self.segments.append(((x1,y1),(x2,y2)))
            return
        mx = (x1+x2)/2 + random.uniform(-spread, spread)
        my = (y1+y2)/2 + random.uniform(-spread, spread)
        self._generate(x1,y1,mx,my, depth-1, spread*0.55)
        self._generate(mx,my,x2,y2, depth-1, spread*0.55)

    def update(self):
        self.life -= 1
        return self.life > 0

    def draw(self, surf, t):
        a   = int(255 * self.life / self.max_life)
        col = hsv_color(self.hue)
        for p1, p2 in self.segments:
            try:
                pygame.draw.line(surf, (*col, a),
                    (int(p1[0]),int(p1[1])), (int(p2[0]),int(p2[1])), 2)
            except Exception:
                pass


class LightningEffect:
    def __init__(self):
        self.bolts: List[LightningBolt] = []
        self.timer = 0

    def strike(self, x1=None, y1=None, x2=None, y2=None):
        x1 = x1 or random.randint(0, WIDTH)
        y1 = y1 or random.randint(0, HEIGHT//2)
        x2 = x2 or random.randint(0, WIDTH)
        y2 = y2 or random.randint(HEIGHT//2, HEIGHT)
        self.bolts.append(LightningBolt(x1, y1, x2, y2,
                                         hue=random.uniform(0.55, 0.75)))

    def update(self, t):
        self.timer += 1
        if self.timer % 18 == 0:
            self.strike()
        self.bolts = [b for b in self.bolts if b.update()]

    def draw(self, surf, t):
        lsurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for b in self.bolts:
            b.draw(lsurf, t)
        surf.blit(lsurf, (0, 0))


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: DNA СПИРАЛЬ
# ═══════════════════════════════════════════════════════════════════════

class DNAEffect:
    def __init__(self):
        self.phase  = 0.0
        self.active = False
        self.alpha  = 0

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def update(self):
        self.phase += 0.06
        if self.active:
            self.alpha = min(200, self.alpha + 6)
        else:
            self.alpha = max(0, self.alpha - 6)

    def draw(self, surf, t):
        if self.alpha < 5:
            return
        dsurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        n     = 60
        for i in range(n):
            y    = int(i * HEIGHT / n)
            frac = i / n
            px1  = int(CX + 120 * math.cos(self.phase + frac * math.tau * 2))
            px2  = int(CX - 120 * math.cos(self.phase + frac * math.tau * 2))
            col1 = hsv_color(frac, 1.0, 1.0)
            col2 = hsv_color((frac + 0.5) % 1.0, 1.0, 1.0)
            a    = self.alpha
            pygame.draw.circle(dsurf, (*col1, a), (px1, y), 6)
            pygame.draw.circle(dsurf, (*col2, a), (px2, y), 6)
            if i > 0:
                yprev = int((i-1) * HEIGHT / n)
                px1p  = int(CX + 120 * math.cos(self.phase + (i-1)/n * math.tau * 2))
                px2p  = int(CX - 120 * math.cos(self.phase + (i-1)/n * math.tau * 2))
                pygame.draw.line(dsurf, (*col1, a), (px1p, yprev), (px1, y), 2)
                pygame.draw.line(dsurf, (*col2, a), (px2p, yprev), (px2, y), 2)
            if i % 6 == 0:
                pygame.draw.line(dsurf, (*WHITE, a//2), (px1, y), (px2, y), 1)
        surf.blit(dsurf, (0, 0))


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ГИПНОТИЧЕСКОЕ КОЛЬЦО
# ═══════════════════════════════════════════════════════════════════════

class HypnoRingEffect:
    N_RINGS = 20

    def __init__(self):
        self.phase = 0.0
        self.hue   = 0.0

    def update(self, t):
        self.phase += 0.03
        self.hue    = (self.hue + 0.003) % 1.0

    def draw(self, surf, t):
        rsurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(self.N_RINGS):
            r   = int(20 + i * (min(CX, CY) // self.N_RINGS))
            hue = (self.hue + i * 0.05 + self.phase * 0.1) % 1.0
            col = hsv_color(hue)
            a   = int(80 - i * 3)
            if a < 5:
                continue
            try:
                pygame.draw.circle(rsurf, (*col, a), (CX, CY), r, 2)
            except Exception:
                pass
        surf.blit(rsurf, (0, 0))


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: RAINBOW ШЛЕЙФЫ (случайные объекты)
# ═══════════════════════════════════════════════════════════════════════

class Floater:
    def __init__(self):
        self.x    = float(random.randint(0, WIDTH))
        self.y    = float(random.randint(0, HEIGHT))
        self.vx   = random.uniform(-2, 2)
        self.vy   = random.uniform(-2, 2)
        self.hue  = random.random()
        self.size = random.uniform(4, 14)
        self.trail= Trail(max_len=30, width=2)

    def update(self, t):
        self.trail.add(self.x, self.y)
        self.x   += self.vx
        self.y   += self.vy
        self.vx  += random.uniform(-0.1, 0.1)
        self.vy  += random.uniform(-0.1, 0.1)
        self.vx   = clamp(self.vx, -3, 3)
        self.vy   = clamp(self.vy, -3, 3)
        if self.x < 0 or self.x > WIDTH:
            self.vx *= -1
        if self.y < 0 or self.y > HEIGHT:
            self.vy *= -1
        self.hue = (self.hue + 0.005) % 1.0

    def draw(self, surf, t):
        self.trail.draw(surf, t)
        col = hsv_color(self.hue)
        glow_circle(surf, col, (int(self.x), int(self.y)),
                    int(self.size), alpha=220, layers=3)


class FloatersEffect:
    N = 30

    def __init__(self):
        self.floaters = [Floater() for _ in range(self.N)]

    def update(self, t):
        for f in self.floaters:
            f.update(t)

    def draw(self, surf, t):
        for f in self.floaters:
            f.draw(surf, t)


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ПИКСЕЛЬНЫЙ ВЗРЫВ
# ═══════════════════════════════════════════════════════════════════════

class PixelExplosion:
    def __init__(self, particles: ParticlePool):
        self.particles = particles
        self.timer     = 0

    def update(self, t):
        self.timer += 1
        if self.timer % 90 == 0:
            cx = random.randint(100, WIDTH-100)
            cy = random.randint(100, HEIGHT-100)
            hue = random.random()
            self.particles.burst(cx, cy, n=150, speed=8, life=120,
                                  size=4, hue=hue, spread_hue=0.2, grav=0.08)


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: СНЕЖИНКИ / КОНФЕТТИ
# ═══════════════════════════════════════════════════════════════════════

class Confetti:
    def __init__(self):
        self.x   = float(random.randint(0, WIDTH))
        self.y   = float(random.randint(-50, -10))
        self.vx  = random.uniform(-1.5, 1.5)
        self.vy  = random.uniform(1.5, 4.5)
        self.hue = random.random()
        self.size= random.randint(3, 8)
        self.rot = random.uniform(0, math.tau)
        self.vrot= random.uniform(-0.1, 0.1)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vx += random.uniform(-0.05, 0.05)
        self.rot+= self.vrot
        return self.y < HEIGHT + 20

    def draw(self, surf):
        col = hsv_color(self.hue)
        pts = []
        for i in range(4):
            a   = self.rot + i * math.pi/2
            px  = int(self.x + self.size * math.cos(a))
            py  = int(self.y + self.size * math.sin(a))
            pts.append((px, py))
        try:
            pygame.draw.polygon(surf, col, pts)
        except Exception:
            pass


class ConfettiEffect:
    MAX = 200

    def __init__(self):
        self.pieces: List[Confetti] = [Confetti() for _ in range(60)]
        self.timer = 0

    def update(self):
        self.timer += 1
        if self.timer % 3 == 0 and len(self.pieces) < self.MAX:
            self.pieces.append(Confetti())
        self.pieces = [c for c in self.pieces if c.update()]

    def draw(self, surf):
        for c in self.pieces:
            c.draw(surf)


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: РАДИАЛЬНЫЕ ЛУЧИ
# ═══════════════════════════════════════════════════════════════════════

class RadialRaysEffect:
    N_RAYS = 24

    def __init__(self):
        self.angle = 0.0
        self.hue   = 0.0
        self.active= False
        self.alpha = 0

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def update(self):
        self.angle += 0.015
        self.hue    = (self.hue + 0.004) % 1.0
        if self.active:
            self.alpha = min(180, self.alpha + 8)
        else:
            self.alpha = max(0, self.alpha - 8)

    def draw(self, surf, t):
        if self.alpha < 5:
            return
        rsurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(self.N_RAYS):
            a   = self.angle + i * math.tau / self.N_RAYS
            ex  = int(CX + 900 * math.cos(a))
            ey  = int(CY + 900 * math.sin(a))
            hue = (self.hue + i / self.N_RAYS) % 1.0
            col = hsv_color(hue)
            pts = [
                (CX, CY),
                (int(CX + 900*math.cos(a-0.06)), int(CY + 900*math.sin(a-0.06))),
                (int(CX + 900*math.cos(a+0.06)), int(CY + 900*math.sin(a+0.06))),
            ]
            try:
                pygame.draw.polygon(rsurf, (*col, self.alpha//4), pts)
                pygame.draw.line(rsurf, (*col, self.alpha),
                                 (CX, CY), (ex, ey), 2)
            except Exception:
                pass
        surf.blit(rsurf, (0, 0))


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: СИНУСОИДАЛЬНЫЕ ВОЛНЫ
# ═══════════════════════════════════════════════════════════════════════

class SineWavesEffect:
    N_WAVES = 8

    def __init__(self):
        self.phases  = [random.uniform(0, math.tau) for _ in range(self.N_WAVES)]
        self.speeds  = [random.uniform(0.03, 0.09) for _ in range(self.N_WAVES)]
        self.amps    = [random.uniform(40, 120) for _ in range(self.N_WAVES)]
        self.freqs   = [random.uniform(0.008, 0.025) for _ in range(self.N_WAVES)]
        self.hues    = [i/self.N_WAVES for i in range(self.N_WAVES)]
        self.offsets = [HEIGHT*(i+1)//(self.N_WAVES+1) for i in range(self.N_WAVES)]

    def update(self, t):
        for i in range(self.N_WAVES):
            self.phases[i] += self.speeds[i]
            self.hues[i]    = (self.hues[i] + 0.002) % 1.0

    def draw(self, surf, t):
        wsurf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for i in range(self.N_WAVES):
            pts = []
            for x in range(0, WIDTH+1, 4):
                y = int(self.offsets[i] +
                        self.amps[i] * math.sin(x*self.freqs[i] + self.phases[i]))
                pts.append((x, y))
            if len(pts) >= 2:
                col = hsv_color(self.hues[i])
                try:
                    pygame.draw.lines(wsurf, (*col, 120), False, pts, 2)
                except Exception:
                    pass
        surf.blit(wsurf, (0, 0))


# ═══════════════════════════════════════════════════════════════════════
#  ЭФФЕКТ: ТАЙТЛ + HUD
# ═══════════════════════════════════════════════════════════════════════

class HUDEffect:
    def __init__(self, font_title, font_small):
        self.font_title = font_title
        self.font_small = font_small
        self.hue        = 0.0
        self.pulse      = 0.0

    def update(self, t, particle_count):
        self.hue   = (self.hue + 0.005) % 1.0
        self.pulse = (math.sin(t * 3.5) + 1) * 0.5
        self.particle_count = particle_count

    def draw(self, surf, t, fps):
        col  = hsv_color(self.hue)
        sz   = int(26 + 6 * self.pulse)
        try:
            f   = pygame.font.SysFont('Arial', sz, bold=True)
            txt = f.render("🔥 УЛЬТРА ХАОС МОД v9000 ULTRA 🔥", True, col)
            surf.blit(txt, (CX - txt.get_width()//2, 10))
        except Exception:
            pass

        # FPS и кол-во частиц
        try:
            info = self.font_small.render(
                f"FPS: {int(fps)} | Particles: {self.particle_count} | ESC - выход",
                True, (150, 150, 150))
            surf.blit(info, (10, HEIGHT - 30))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════
#  МЕНЕДЖЕР ФАЗ
# ═══════════════════════════════════════════════════════════════════════

PHASE_DURATIONS = {
    'chaos':      int(5.0 * TARGET_FPS),
    'scream':     int(3.0 * TARGET_FPS),
    'fireworks':  int(4.0 * TARGET_FPS),
    'matrix':     int(3.5 * TARGET_FPS),
    'vortex':     int(2.5 * TARGET_FPS),
    'dna':        int(3.0 * TARGET_FPS),
    'plasma':     int(2.5 * TARGET_FPS),
    'rays':       int(2.0 * TARGET_FPS),
}

PHASE_ORDER = ['chaos', 'scream', 'fireworks', 'matrix',
               'vortex', 'dna', 'plasma', 'rays']

class PhaseManager:
    def __init__(self):
        self.phase_idx  = 0
        self.phase_timer= 0
        self.current    = PHASE_ORDER[0]

    def update(self):
        dur = PHASE_DURATIONS[self.current]
        self.phase_timer += 1
        if self.phase_timer >= dur:
            self.phase_timer = 0
            self.phase_idx   = (self.phase_idx + 1) % len(PHASE_ORDER)
            self.current     = PHASE_ORDER[self.phase_idx]
            return True, self.current
        return False, self.current

    def is_phase(self, name):
        return self.current == name


# ═══════════════════════════════════════════════════════════════════════
#  ГЛАВНЫЙ КЛАСС ПРИЛОЖЕНИЯ
# ═══════════════════════════════════════════════════════════════════════

class UltraChaosApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)

        info = pygame.display.Info()
        global WIDTH, HEIGHT, CX, CY
        WIDTH  = info.current_w
        HEIGHT = info.current_h
        CX     = WIDTH  // 2
        CY     = HEIGHT // 2

        self.screen = pygame.display.set_mode(
            (WIDTH, HEIGHT),
            pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        self.clock  = pygame.time.Clock()
        self.frame  = 0
        self.running= True

        # Шрифты
        self.font_big   = pygame.font.SysFont('Arial', 72, bold=True)
        self.font_med   = pygame.font.SysFont('Arial', 36, bold=True)
        self.font_small = pygame.font.SysFont('Courier', 18)
        self.font_matrix= pygame.font.SysFont('Courier', 16, bold=True)

        # Основная поверхность с затуханием
        self.trail_surf = pygame.Surface((WIDTH, HEIGHT))
        self.trail_surf.fill(BLACK)

        # Пул частиц
        self.particles = ParticlePool(capacity=4000)

        # Эффекты
        self.stars      = StarsEffect()
        self.main_circle= MainCircleEffect()
        self.fireworks  = FireworksEffect(self.particles)
        self.matrix     = MatrixEffect(self.font_matrix)
        self.vortex     = VortexEffect()
        self.boxes      = BoxesEffect()
        self.triangles  = TrianglesEffect()
        self.scream     = ScreamEffect(self.font_big, self.font_med)
        self.bang       = BangEffect()
        self.plasma     = PlasmaWaveEffect()
        self.lightning  = LightningEffect()
        self.dna        = DNAEffect()
        self.hypno      = HypnoRingEffect()
        self.floaters   = FloatersEffect()
        self.pixel_exp  = PixelExplosion(self.particles)
        self.confetti   = ConfettiEffect()
        self.rays       = RadialRaysEffect()
        self.waves      = SineWavesEffect()
        self.hud        = HUDEffect(self.font_big, self.font_small)
        self.phase_mgr  = PhaseManager()

        self.fps_avg    = TARGET_FPS

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    # Ручной взрыв частиц
                    self.particles.burst(CX, CY, n=200, speed=10,
                                         life=120, size=5, grav=0.05)
                    self.fireworks.launch(CX, CY//2)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                self.particles.burst(mx, my, n=100, speed=7,
                                     life=100, size=4, grav=0.05)
                self.lightning.strike(CX, CY, mx, my)

    def handle_phase_change(self, new_phase):
        # Деактивируем всё
        self.matrix.deactivate()
        self.vortex.deactivate()
        self.plasma.deactivate()
        self.dna.deactivate()
        self.rays.deactivate()

        if new_phase == 'scream':
            self.scream.activate()
            self.particles.burst(CX, CY, n=300, speed=12,
                                  life=120, size=5, grav=0.06)
        elif new_phase == 'fireworks':
            for _ in range(5):
                self.fireworks.launch()
        elif new_phase == 'matrix':
            self.matrix.activate()
        elif new_phase == 'vortex':
            self.vortex.activate()
        elif new_phase == 'dna':
            self.dna.activate()
        elif new_phase == 'plasma':
            self.plasma.activate()
        elif new_phase == 'rays':
            self.rays.activate()

    def update(self):
        t = self.frame / TARGET_FPS

        # Фазы
        changed, new_phase = self.phase_mgr.update()
        if changed:
            self.handle_phase_change(new_phase)

        # Обновляем все эффекты
        self.stars.update(t)
        self.main_circle.update(t, self.particles)
        self.fireworks.update(t)
        self.matrix.update()
        self.vortex.update(t)
        self.boxes.update(t)
        self.triangles.update(t)
        self.scream.update(self.particles)
        self.bang.update(t)
        self.plasma.update(t)
        self.lightning.update(t)
        self.dna.update()
        self.hypno.update(t)
        self.floaters.update(t)
        self.pixel_exp.update(t)
        self.confetti.update()
        self.rays.update()
        self.waves.update(t)
        self.hud.update(t, self.particles.count())

        self.frame += 1

    def draw(self):
        t = self.frame / TARGET_FPS

        # Затухание следов (motion blur)
        fade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        bg_alpha = 35
        if self.phase_mgr.is_phase('scream'):
            fade.fill((60, 0, 0, bg_alpha))
        elif self.phase_mgr.is_phase('matrix'):
            fade.fill((0, 10, 0, bg_alpha))
        else:
            fade.fill((0, 0, 0, bg_alpha))

        self.screen.blit(fade, (0, 0))

        # Порядок отрисовки (back to front)
        self.stars.draw(self.screen, t)
        self.hypno.draw(self.screen, t)
        self.waves.draw(self.screen, t)
        self.plasma.draw(self.screen, t)
        self.rays.draw(self.screen, t)
        self.boxes.draw(self.screen, t)
        self.triangles.draw(self.screen, t)
        self.dna.draw(self.screen, t)
        self.vortex.draw(self.screen, t)
        self.floaters.draw(self.screen, t)
        self.main_circle.draw(self.screen, t)
        self.confetti.draw(self.screen)
        self.particles.update_and_draw(self.screen)
        self.fireworks.draw(self.screen, t)
        self.lightning.draw(self.screen, t)
        self.matrix.draw(self.screen)
        self.bang.draw(self.screen, t)
        self.scream.draw(self.screen, t)
        self.hud.draw(self.screen, t, self.fps_avg)

        pygame.display.flip()

    def run(self):
        print("=" * 60)
        print("   УЛЬТРА ХАОС МОД v9000 ULTRA — PYGAME EDITION")
        print("   ESC / Q  — выход")
        print("   SPACE    — мега взрыв!")
        print("   ЛКМ      — молния + взрыв в точке клика")
        print("=" * 60)

        while self.running:
            dt = self.clock.tick(TARGET_FPS)
            self.fps_avg = self.fps_avg * 0.95 + (1000 / max(dt, 1)) * 0.05

            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit(0)


# ═══════════════════════════════════════════════════════════════════════
#  ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app = UltraChaosApp()
    app.run()
