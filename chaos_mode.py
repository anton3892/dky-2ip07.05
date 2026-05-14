import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import random

# ─────────────────────────────────────────
#  НАСТРОЙКА ФИГУРЫ
# ─────────────────────────────────────────
fig = plt.figure(figsize=(12, 9), facecolor='black')
fig.patch.set_facecolor('black')

# Главный 2D-холст
ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor('black')
ax.set_xlim(-5, 5)
ax.set_ylim(-4, 4)
ax.set_aspect('equal')
ax.axis('off')

FPS        = 60
SCREAM_SEC = 5
MATRIX_SEC = 10

# ─────────────────────────────────────────
#  ТРЕУГОЛЬНИК (центр)
# ─────────────────────────────────────────
BASE_TRI = np.array([[0, 1.2], [-1.04, -0.6], [1.04, -0.6]])
N_TRAIL  = 14
triangles = []
for _ in range(N_TRAIL):
    p = Polygon(BASE_TRI, closed=True, animated=True, zorder=5)
    ax.add_patch(p)
    triangles.append(p)

def rotate2d(pts, a):
    c, s = np.cos(a), np.sin(a)
    return pts @ np.array([[c, -s], [s, c]]).T

# ─────────────────────────────────────────
#  ПАРАЛЛЕЛЕПИПЕДЫ (3D → ручная проекция)
# ─────────────────────────────────────────
def box_verts(w, h, d):
    hw, hh, hd = w/2, h/2, d/2
    return np.array([
        [-hw,-hh,-hd],[hw,-hh,-hd],[hw,hh,-hd],[-hw,hh,-hd],
        [-hw,-hh, hd],[hw,-hh, hd],[hw,hh, hd],[-hw,hh, hd],
    ], dtype=float)

FACES = [(0,1,2,3),(4,5,6,7),(0,1,5,4),(2,3,7,6),(0,3,7,4),(1,2,6,5)]
EDGES = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]

def rot3d(pts, rx, ry, rz):
    Rx = np.array([[1,0,0],[0,np.cos(rx),-np.sin(rx)],[0,np.sin(rx),np.cos(rx)]])
    Ry = np.array([[np.cos(ry),0,np.sin(ry)],[0,1,0],[-np.sin(ry),0,np.cos(ry)]])
    Rz = np.array([[np.cos(rz),-np.sin(rz),0],[np.sin(rz),np.cos(rz),0],[0,0,1]])
    return pts @ (Rz@Ry@Rx).T

def project(pts, fov=6):
    d = pts[:,2]/fov + 1.6
    return np.column_stack([pts[:,0]/d, pts[:,1]/d])

N_BOXES = 14
rng = np.random.default_rng(42)

box_cfgs = []
for i in range(N_BOXES):
    ang = 2*np.pi*i/N_BOXES
    r   = rng.uniform(2.2, 3.8)
    box_cfgs.append(dict(
        cx=r*np.cos(ang),
        cy=r*np.sin(ang)*0.75,
        verts=box_verts(*rng.uniform(0.25, 0.65, 3)),
        phase=rng.uniform(0, 2*np.pi),
        speed=rng.uniform(1.5, 4.0),
        hue=i/N_BOXES,
    ))

# Линии рёбер для каждого ящика
box_lines = []
for bc in box_cfgs:
    lines = []
    for _ in EDGES:
        l, = ax.plot([], [], '-', lw=1.2, animated=True, zorder=4)
        lines.append(l)
    box_lines.append(lines)

# ─────────────────────────────────────────
#  МАТРИЦА ЦИФР (пандемия-стиль)
# ─────────────────────────────────────────
N_DIGITS = 80
digit_texts = []
for _ in range(N_DIGITS):
    t = ax.text(
        rng.uniform(-5, 5), rng.uniform(-4, 4),
        str(rng.integers(0, 10)),
        color='lime', fontsize=rng.integers(10, 28),
        ha='center', va='center',
        animated=True, visible=False,
        alpha=rng.uniform(0.5, 1.0),
        fontfamily='monospace', zorder=6,
        fontweight='bold'
    )
    digit_texts.append(t)

matrix_active = [0]   # кадров осталось

def activate_matrix():
    matrix_active[0] = int(3.0 * FPS)
    for t in digit_texts:
        t.set_position((rng.uniform(-5,5), rng.uniform(-4,4)))
        t.set_text(str(rng.integers(0,10)))
        t.set_fontsize(int(rng.integers(10,28)))
        t.set_color(rng.choice(['lime','cyan','#00ff88','#aaff00']))
        t.set_visible(True)

# ─────────────────────────────────────────
#  СКРИМЕР
# ─────────────────────────────────────────
SCREAM_FACES = ['😱', '💀', '👁️', '🫀', '😈']
scream_bg = ax.fill([-5,-5,5,5],[-4,4,4,-4],
                    color='red', alpha=0, animated=True, zorder=8)[0]
scream_txt = ax.text(0, 0.6, '', fontsize=120, ha='center', va='center',
                     animated=True, visible=False, zorder=9)
scream_sub = ax.text(0, -1.4, '', fontsize=28, ha='center', va='center',
                     color='white', fontweight='bold',
                     animated=True, visible=False, zorder=9)
scream_sub2 = ax.text(0, -2.2, '', fontsize=18, ha='center', va='center',
                      color='yellow',
                      animated=True, visible=False, zorder=9)

SCREAMS = [
    ('ТЫ НЕ ГОТОВ',   'БЕГИ'),
    ('ОНО ПРИШЛО',    'СПАСАЙСЯ'),
    ('ЧТО ТЫ ВИДИШЬ', '...ОНО СМОТРИТ'),
    ('КОНЕЦ БЛИЗОК',  'ХА-ХА-ХА-ХА'),
    ('ДОБРО ПОЖАЛОВ.','В АД'),
]

scream_active = [0]

def activate_scream():
    scream_active[0] = int(1.0 * FPS)
    face = random.choice(SCREAM_FACES)
    s1, s2 = random.choice(SCREAMS)
    scream_txt.set_text(face)
    scream_sub.set_text(s1)
    scream_sub2.set_text(s2)
    scream_bg.set_facecolor(random.choice(['red','darkred','#8b0000']))

# ─────────────────────────────────────────
#  ЗАГОЛОВОК
# ─────────────────────────────────────────
title_txt = ax.text(0, 3.6, '⚡ CHAOS MODE ⚡', fontsize=22,
                    ha='center', va='center', color='white',
                    fontweight='bold', animated=True, zorder=7)

# ─────────────────────────────────────────
#  СОСТОЯНИЕ
# ─────────────────────────────────────────
state = {'angle': 0.0}

# собираем всех артистов для blit
all_artists = (triangles +
               [scream_bg, scream_txt, scream_sub, scream_sub2, title_txt] +
               digit_texts +
               [l for ls in box_lines for l in ls])

# ─────────────────────────────────────────
#  ГЛАВНЫЙ UPDATE
# ─────────────────────────────────────────
def update(frame):
    t = frame / FPS
    state['angle'] += 0.38

    # ── ТРЕУГОЛЬНИК ──
    for i, tri in enumerate(triangles):
        a = state['angle'] - i * 0.19
        pts = rotate2d(BASE_TRI, a)
        tri.set_xy(pts)
        alpha = (N_TRAIL - i) / N_TRAIL
        hue = (state['angle'] / (2*np.pi) + i*0.07) % 1.0
        c = plt.cm.hsv(hue)
        tri.set_facecolor((*c[:3], alpha * 0.9))
        tri.set_edgecolor((*c[:3], alpha))
        tri.set_linewidth(2.5 if i == 0 else 0.4)

    # ── ПАРАЛЛЕЛЕПИПЕДЫ ──
    for bc, lines in zip(box_cfgs, box_lines):
        ph = bc['phase']
        sp = bc['speed']
        rx = t * sp * 1.1 + ph
        ry = t * sp * 0.8 + ph * 1.3
        rz = np.sin(t * sp * 0.6 + ph) * 2.0   # качающийся
        rv = rot3d(bc['verts'], rx, ry, rz)
        pr = project(rv)
        pr[:,0] += bc['cx']
        pr[:,1] += bc['cy']
        hue = (bc['hue'] + t * 0.08) % 1.0
        c = plt.cm.plasma(hue)
        for (e0,e1), ln in zip(EDGES, lines):
            ln.set_data([pr[e0,0], pr[e1,0]], [pr[e0,1], pr[e1,1]])
            ln.set_color(c)

    # ── СКРИМЕР каждые 5 с ──
    if frame > 0 and frame % (SCREAM_SEC * FPS) == 0:
        activate_scream()

    if scream_active[0] > 0:
        scream_active[0] -= 1
        prog = scream_active[0] / (1.0*FPS)
        scream_bg.set_alpha(0.88 * min(prog*3, 1.0))
        for obj in (scream_txt, scream_sub, scream_sub2):
            obj.set_visible(True)
        # дрожание текста
        scream_txt.set_position((rng.uniform(-0.2,0.2), 0.6+rng.uniform(-0.1,0.1)))
    else:
        scream_bg.set_alpha(0)
        for obj in (scream_txt, scream_sub, scream_sub2):
            obj.set_visible(False)

    # ── МАТРИЦА ЦИФР каждые 10 с ──
    if frame > 0 and frame % (MATRIX_SEC * FPS) == 0:
        activate_matrix()

    if matrix_active[0] > 0:
        matrix_active[0] -= 1
        # дождь: сдвигаем цифры вниз
        for txt in digit_texts:
            x, y = txt.get_position()
            y -= 0.18
            if y < -4:
                y = 4.2
                x = rng.uniform(-5, 5)
                txt.set_text(str(rng.integers(0,10)))
            txt.set_position((x, y))
            txt.set_visible(True)
        # случайное мигание
        if frame % 4 == 0:
            random.choice(digit_texts).set_text(str(rng.integers(0,10)))
    else:
        for txt in digit_texts:
            txt.set_visible(False)

    # ── ЗАГОЛОВОК мигает в цвет ──
    hue = (t * 0.3) % 1.0
    title_txt.set_color(plt.cm.hsv(hue)[:3])

    return all_artists

# ─────────────────────────────────────────
#  ЗАПУСК
# ─────────────────────────────────────────
ani = animation.FuncAnimation(
    fig, update,
    frames=100_000,
    interval=1000 // FPS,
    blit=True
)

plt.tight_layout(pad=0)
plt.show()
