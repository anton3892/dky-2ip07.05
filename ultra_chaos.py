"""
╔══════════════════════════════════════════════════════════════╗
║           УЛЬТРА ХАОС МОД v9000 — МАКСИМАЛЬНЫЙ УРОН         ║
╚══════════════════════════════════════════════════════════════╝
"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon, Circle
from matplotlib.collections import LineCollection
import random, math, time

matplotlib.rcParams['toolbar'] = 'None'

# ══════════════════════════════════════════════════════════════
#  ФИГУРА — ПОЛНЫЙ ЭКРАН
# ══════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(14, 10), facecolor='black')
manager = plt.get_current_fig_manager()
try:    manager.window.state('zoomed')        # Windows / Tk
except: pass
try:    manager.full_screen_toggle()           # Qt / другие
except: pass

ax = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor('black')
W, H = 7.0, 5.5
ax.set_xlim(-W, W)
ax.set_ylim(-H, H)
ax.set_aspect('equal')
ax.axis('off')

FPS  = 60
rng  = np.random.default_rng(42)

# ══════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ══════════════════════════════════════════════════════════════
def r2d(pts, a):
    c, s = np.cos(a), np.sin(a)
    return pts @ np.array([[c, -s], [s, c]]).T

def rot3d(pts, rx, ry, rz):
    Rx = np.array([[1,0,0],[0,np.cos(rx),-np.sin(rx)],[0,np.sin(rx),np.cos(rx)]])
    Ry = np.array([[np.cos(ry),0,np.sin(ry)],[0,1,0],[-np.sin(ry),0,np.cos(ry)]])
    Rz = np.array([[np.cos(rz),-np.sin(rz),0],[np.sin(rz),np.cos(rz),0],[0,0,1]])
    return pts @ (Rz @ Ry @ Rx).T

def proj3d(pts, fov=9):
    d = pts[:,2]/fov + 2.2
    return np.column_stack([pts[:,0]/d, pts[:,1]/d])

def box_v(w, h, d):
    hw, hh, hd = w/2, h/2, d/2
    return np.array([
        [-hw,-hh,-hd],[hw,-hh,-hd],[hw,hh,-hd],[-hw,hh,-hd],
        [-hw,-hh, hd],[hw,-hh, hd],[hw,hh, hd],[-hw,hh, hd]], dtype=float)

BEDGES = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]

CMAPS  = [plt.cm.hsv, plt.cm.plasma, plt.cm.cool,
          plt.cm.rainbow, plt.cm.spring, plt.cm.autumn]

# ══════════════════════════════════════════════════════════════
#  ФОН — СТРОБОСКОП
# ══════════════════════════════════════════════════════════════
bg = ax.fill([-W,-W,W,W],[-H,H,H,-H], color='black', alpha=1, animated=True, zorder=0)[0]

# ══════════════════════════════════════════════════════════════
#  1. ГЛАВНЫЙ КРУГ — СКОРОСТЬ СВЕТА
#     Крутится с угловой скоростью 3 рад/кадр (180 об/сек!)
# ══════════════════════════════════════════════════════════════
MAIN_R      = 2.2
MAIN_TRAIL  = 40          # шлейф из секций дуги
main_lines  = []
for i in range(MAIN_TRAIL):
    l, = ax.plot([], [], '-', lw=3.5 - i*0.07, animated=True, zorder=6)
    main_lines.append(l)

# Точка-маркер на главном круге
main_dot, = ax.plot([], [], 'o', ms=14, animated=True, zorder=7)

# ══════════════════════════════════════════════════════════════
#  2. ОРБИТАЛЬНЫЕ КРУГИ — вылетают из главного
# ══════════════════════════════════════════════════════════════
N_ORB = 200
orb_x   = rng.uniform(-W, W, N_ORB)
orb_y   = rng.uniform(-H, H, N_ORB)
orb_vx  = rng.uniform(-0.08, 0.08, N_ORB)
orb_vy  = rng.uniform(-0.08, 0.08, N_ORB)
orb_r   = rng.uniform(0.02, 0.20, N_ORB)
orb_hue = rng.uniform(0, 1, N_ORB)
orb_life= rng.uniform(0.3, 1.0, N_ORB)
orb_alive = np.ones(N_ORB, dtype=bool)
N_ORB_PTS = 32
theta_orb = np.linspace(0, 2*np.pi, N_ORB_PTS+1)
orb_patches = []
for _ in range(N_ORB):
    l, = ax.plot([], [], '-', lw=0.8, animated=True, zorder=5, alpha=0.85)
    orb_patches.append(l)

def respawn_orb(i, from_circle=True):
    """Переспавним орбитальный круг с главного кольца"""
    if from_circle:
        ang = rng.uniform(0, 2*np.pi)
        orb_x[i]  = MAIN_R * np.cos(ang) + rng.uniform(-0.3, 0.3)
        orb_y[i]  = MAIN_R * np.sin(ang) + rng.uniform(-0.3, 0.3)
    else:
        orb_x[i]  = rng.uniform(-W, W)
        orb_y[i]  = rng.uniform(-H, H)
    sp = rng.uniform(0.04, 0.18)
    a  = rng.uniform(0, 2*np.pi)
    orb_vx[i] = sp * np.cos(a)
    orb_vy[i] = sp * np.sin(a)
    orb_r[i]  = rng.uniform(0.04, 0.25)
    orb_hue[i]= rng.uniform(0, 1)
    orb_life[i]= 1.0
    orb_alive[i] = True

for i in range(N_ORB):
    respawn_orb(i, from_circle=False)

# ══════════════════════════════════════════════════════════════
#  3. ФЕЙЕРВЕРКИ — 400 частиц
# ══════════════════════════════════════════════════════════════
NF = 400
fw_pos  = rng.uniform([-W,-H], [W,H], (NF, 2))
fw_vel  = np.zeros((NF, 2))
fw_life = np.zeros(NF)
fw_col  = np.zeros((NF, 4))
fw_scat = ax.scatter([], [], s=[], c=[], animated=True, zorder=8)
fw_on   = [0]

def boom(n=NF, cx=None, cy=None):
    fw_on[0] = int(3.5*FPS)
    for i in range(n):
        bcx = rng.uniform(-W*0.6, W*0.6) if cx is None else cx + rng.uniform(-1,1)
        bcy = rng.uniform(-H*0.6, H*0.6) if cy is None else cy + rng.uniform(-1,1)
        a   = rng.uniform(0, 2*np.pi)
        sp  = rng.uniform(0.04, 0.42)
        fw_pos[i]   = [bcx, bcy]
        fw_vel[i]   = [sp*np.cos(a), sp*np.sin(a)]
        fw_life[i]  = rng.uniform(0.5, 1.0)
        c = mcolors.to_rgba(rng.choice(
            ['red','orange','gold','yellow','lime','cyan',
             'magenta','white','deepskyblue','hotpink','violet','aqua']))
        fw_col[i] = c

boom()  # стартовый взрыв

# ══════════════════════════════════════════════════════════════
#  4. ПАРАЛЛЕЛЕПИПЕДЫ
# ══════════════════════════════════════════════════════════════
N_BOX = 16
box_cfgs, box_lns = [], []
for i in range(N_BOX):
    ang = 2*np.pi*i/N_BOX + np.pi/N_BOX
    r   = rng.uniform(2.5, 5.5)
    box_cfgs.append(dict(
        cx=r*np.cos(ang), cy=r*np.sin(ang)*0.72,
        verts=box_v(*rng.uniform(0.2, 0.7, 3)),
        ph=rng.uniform(0,2*np.pi), sp=rng.uniform(2,6), hue=i/N_BOX))
    lns = [ax.plot([],[],'-', lw=0.9, animated=True, zorder=4)[0] for _ in BEDGES]
    box_lns.append(lns)

# ══════════════════════════════════════════════════════════════
#  5. ТРЕУГОЛЬНИК
# ══════════════════════════════════════════════════════════════
BASE_TRI = np.array([[0,1.5],[-1.3,-0.75],[1.3,-0.75]])
N_T = 20
tris = [ax.add_patch(Polygon(BASE_TRI, closed=True, animated=True, zorder=5))
        for _ in range(N_T)]
tri_ang = [0.0]

# ══════════════════════════════════════════════════════════════
#  6. ВОРТЕКС СПИРАЛЬ
# ══════════════════════════════════════════════════════════════
N_VORT = 120
vort_ls = [ax.plot([],[],'-', lw=0.6, animated=True, alpha=0.7, zorder=2)[0]
           for _ in range(N_VORT)]
vort_on = [0]

# ══════════════════════════════════════════════════════════════
#  7. МАТРИЦА ЦИФР
# ══════════════════════════════════════════════════════════════
N_DIG = 150
dig_ts  = []
for _ in range(N_DIG):
    t = ax.text(rng.uniform(-W,W), rng.uniform(-H,H),
                str(rng.integers(0,10)),
                color='lime', fontsize=int(rng.integers(7,24)),
                ha='center', va='center', animated=True, visible=False,
                fontfamily='monospace', zorder=6, fontweight='bold')
    dig_ts.append(t)
mat_on = [0]

# ══════════════════════════════════════════════════════════════
#  8. СКРИМЕР + НАДПИСЬ "САНЯ БЛЯТЬ ПИТУХ ЕПТА"
# ══════════════════════════════════════════════════════════════
FACES  = ['😱','💀','👁️','😈','🤡','👻','☠️','🫀','🦴','🔪','🧠']
sc_bg  = ax.fill([-W,-W,W,W],[-H,H,H,-H],
                 color='red', alpha=0, animated=True, zorder=14)[0]

# Главная надпись на весь экран
sc_main = ax.text(0, 1.0, 'САНЯ БЛЯТЬ\nПИТУХ ЕПТА',
                  fontsize=80, ha='center', va='center',
                  color='yellow', fontweight='bold',
                  animated=True, visible=False, zorder=16,
                  style='italic')

sc_face = ax.text(0, -2.2, '', fontsize=100, ha='center', va='center',
                  animated=True, visible=False, zorder=16)

sc_sub  = ax.text(0, -3.8, '', fontsize=26, ha='center', va='center',
                  color='white', fontweight='bold',
                  animated=True, visible=False, zorder=16)

sc_on   = [0]
SC_DUR  = int(2.5*FPS)

SCREAM_LINES = [
    'ВСЕ ЗНАЮТ 🤣', 'ЭТО ПРАВДА!!!', 'УБЕГАЙ!', 'ХА-ХА-ХА',
    'СПАСАЙСЯ', 'ОНО ПРИШЛО', 'КОНЕЦ БЛИЗКО', 'БЕГИ САНЯ'
]

def SCREAM():
    sc_on[0] = SC_DUR
    sc_face.set_text(random.choice(FACES))
    sc_sub.set_text(random.choice(SCREAM_LINES))
    sc_bg.set_facecolor(random.choice(
        ['red','#6b0000','#2a0060','#005500','#00004a']))
    # одновременно взрыв фейерверков
    boom()

# ══════════════════════════════════════════════════════════════
#  9. ВЗРЫВНЫЕ НАДПИСИ (периодически)
# ══════════════════════════════════════════════════════════════
BANGS  = ['ХАОС!','BOOM!','ВАУ!','PANIC!','КАК?!','ААААА!',
          'ЧТО?!','🔥🔥🔥','МОЩЬ!','ЕПТА!!!','САНЯ!!!','ВСЁ!!!']
bang_t = ax.text(0, 0, '', fontsize=55, ha='center', va='center',
                 color='red', fontweight='bold',
                 animated=True, visible=False, zorder=13)
bang_on = [0]

def fire_bang():
    bang_on[0] = int(0.75*FPS)
    bang_t.set_text(random.choice(BANGS))
    bang_t.set_position((rng.uniform(-W*0.6,W*0.6), rng.uniform(-H*0.6,H*0.6)))
    bang_t.set_color(rng.choice(['red','orange','yellow','cyan','magenta','white','lime']))
    bang_t.set_fontsize(int(rng.integers(45,110)))

# ══════════════════════════════════════════════════════════════
#  10. ТАЙТЛ
# ══════════════════════════════════════════════════════════════
title = ax.text(0, H*0.88, '🔥 УЛЬТРА ХАОС МОД v9000 🔥',
                fontsize=22, ha='center', va='center',
                color='white', fontweight='bold',
                animated=True, zorder=17)

# ══════════════════════════════════════════════════════════════
#  ТАЙМЛАЙН ФАЗ
# ══════════════════════════════════════════════════════════════
PHASES = [
    (int(5.0*FPS), 'chaos'),
    (int(SC_DUR),  'scream'),
    (int(3.5*FPS), 'fireworks'),
    (int(3.0*FPS), 'matrix'),
    (int(2.5*FPS), 'vortex'),
]
ph_idx   = [0]
ph_timer = [0]
ph_name  = ['chaos']

# ГЛАВНЫЙ УГОЛ КРУГА
main_angle = [0.0]
main_hue   = [0.0]
cmap_idx   = [0]
cmap_timer = [0]

# ══════════════════════════════════════════════════════════════
#  ALL ARTISTS
# ══════════════════════════════════════════════════════════════
ALL = ([bg] + main_lines + [main_dot] +
       orb_patches + [fw_scat] +
       tris +
       [l for ls in box_lns for l in ls] +
       vort_ls + dig_ts +
       [sc_bg, sc_main, sc_face, sc_sub] +
       [bang_t, title])

# ══════════════════════════════════════════════════════════════
#  UPDATE
# ══════════════════════════════════════════════════════════════
def update(frame):
    t = frame / FPS

    # ── PHASE MANAGER ──────────────────────────────────────
    ph_timer[0] += 1
    dur, _ = PHASES[ph_idx[0]]
    if ph_timer[0] >= dur:
        ph_timer[0] = 0
        ph_idx[0]   = (ph_idx[0]+1) % len(PHASES)
        ph_name[0]  = PHASES[ph_idx[0]][1]
        nxt = ph_name[0]
        if nxt == 'scream':     SCREAM()
        if nxt == 'fireworks':  boom()
        if nxt == 'matrix':
            mat_on[0] = int(3.5*FPS)
            for dt in dig_ts:
                dt.set_position((rng.uniform(-W,W), rng.uniform(-H,H)))
                dt.set_text(str(rng.integers(0,10)))
        if nxt == 'vortex':
            vort_on[0] = int(2.5*FPS)

    cur = ph_name[0]

    # ── ФОН ─────────────────────────────────────────────────
    if cur == 'scream':
        bg.set_facecolor((0.3,0,0,1))
    elif frame % 8 < 2 and cur == 'fireworks':
        strobe_h = (t*0.7) % 1.0
        c = plt.cm.hsv(strobe_h)
        bg.set_facecolor((*c[:3], 0.06))
    else:
        bg.set_facecolor((0,0,0,1))

    # ── ВЗРЫВНЫЕ НАДПИСИ каждые 1.8с ───────────────────────
    if frame % int(1.8*FPS) == int(FPS*0.3):
        fire_bang()
    if bang_on[0] > 0:
        bang_on[0] -= 1
        s = 1.0 + 0.6*math.sin(bang_on[0]*0.55)
        bang_t.set_fontsize(int(60*s))
        bang_t.set_visible(True)
    else:
        bang_t.set_visible(False)

    # ══════════════════════════════════════════════════════
    #  ГЛАВНЫЙ КРУГ — МЕГА СКОРОСТЬ
    # ══════════════════════════════════════════════════════
    SPEED      = 3.2        # рад/кадр  → ~192 об/сек 🚀
    main_angle[0] += SPEED
    a0 = main_angle[0]

    # Сменяем цветовую карту каждые 40 кадров
    cmap_timer[0] += 1
    if cmap_timer[0] >= 40:
        cmap_timer[0] = 0
        cmap_idx[0]   = (cmap_idx[0]+1) % len(CMAPS)
    cmap = CMAPS[cmap_idx[0]]

    # Шлейф дуг
    ARC = 2*np.pi/MAIN_TRAIL
    for i, l in enumerate(main_lines):
        a_start = a0 - i*ARC - ARC
        a_end   = a0 - i*ARC
        th  = np.linspace(a_start, a_end, 20)
        l.set_data(MAIN_R*np.cos(th), MAIN_R*np.sin(th))
        hue = (main_hue[0] - i/MAIN_TRAIL*0.5) % 1.0
        c   = cmap(hue)
        alpha = (MAIN_TRAIL-i)/MAIN_TRAIL
        l.set_color((*c[:3], alpha))
        l.set_linewidth(max(0.3, 4.0 - i*0.10))

    main_hue[0] = (main_hue[0] + 0.025) % 1.0

    # Точка на круге
    main_dot.set_data([MAIN_R*np.cos(a0)], [MAIN_R*np.sin(a0)])
    main_dot.set_color(cmap(main_hue[0]))
    main_dot.set_markersize(16 + 6*abs(math.sin(t*8)))

    # ══════════════════════════════════════════════════════
    #  ОРБИТАЛЬНЫЕ КРУГИ — вылетают из главного
    # ══════════════════════════════════════════════════════
    # Каждые 2 кадра спавним новый с позиции на кольце
    if frame % 2 == 0:
        i_s = frame // 2 % N_ORB
        respawn_orb(i_s, from_circle=True)

    orb_x[:]    += orb_vx
    orb_y[:]    += orb_vy
    orb_life[:] -= 0.006

    for i, l in enumerate(orb_patches):
        if orb_life[i] <= 0:
            respawn_orb(i, from_circle=True)
        x, y, r = orb_x[i], orb_y[i], orb_r[i]
        hue = (orb_hue[i] + t*0.3) % 1.0
        c   = cmap(hue)
        xs  = x + r*np.cos(theta_orb)
        ys  = y + r*np.sin(theta_orb)
        l.set_data(xs, ys)
        l.set_color((*c[:3], max(0.1, orb_life[i])))
        l.set_linewidth(0.8 + orb_r[i]*4)

    # ══════════════════════════════════════════════════════
    #  ТРЕУГОЛЬНИК
    # ══════════════════════════════════════════════════════
    tri_ang[0] += 0.44
    for i, tri in enumerate(tris):
        a   = tri_ang[0] - i*0.22
        pts = r2d(BASE_TRI, a)
        tri.set_xy(pts)
        alpha = (N_T-i)/N_T
        hue   = (tri_ang[0]/(2*np.pi) + i*0.065) % 1.0
        c     = plt.cm.hsv(hue)
        tri.set_facecolor((*c[:3], alpha*0.85))
        tri.set_edgecolor((*c[:3], alpha))
        tri.set_linewidth(3.0 if i==0 else 0.4)

    # ══════════════════════════════════════════════════════
    #  ПАРАЛЛЕЛЕПИПЕДЫ
    # ══════════════════════════════════════════════════════
    for bc, lns in zip(box_cfgs, box_lns):
        ph, sp = bc['ph'], bc['sp']
        rx = t*sp + ph
        ry = t*sp*0.88 + ph*1.15
        rz = math.sin(t*sp*0.55+ph)*2.9
        rv = rot3d(bc['verts'], rx, ry, rz)
        pr = proj3d(rv)
        pr[:,0] += bc['cx']; pr[:,1] += bc['cy']
        hue = (bc['hue'] + t*0.06) % 1.0
        c   = plt.cm.plasma(hue)
        for (e0,e1), ln in zip(BEDGES, lns):
            ln.set_data([pr[e0,0],pr[e1,0]], [pr[e0,1],pr[e1,1]])
            ln.set_color(c)

    # ══════════════════════════════════════════════════════
    #  ВОРТЕКС
    # ══════════════════════════════════════════════════════
    if vort_on[0] > 0:
        vort_on[0] -= 1
        for i, vl in enumerate(vort_ls):
            base = t*7 + i*2*np.pi/N_VORT
            rs   = np.linspace(0.05, 6.5, 50)
            ths  = base + rs*0.9
            vl.set_data(rs*np.cos(ths), rs*np.sin(ths)*0.75)
            hue = (i/N_VORT + t*0.3) % 1.0
            vl.set_color(plt.cm.hsv(hue))
            vl.set_alpha(0.6 + 0.4*math.sin(t*4+i))
            vl.set_visible(True)
    else:
        for vl in vort_ls:
            vl.set_visible(False)

    # ══════════════════════════════════════════════════════
    #  МАТРИЦА
    # ══════════════════════════════════════════════════════
    if mat_on[0] > 0:
        mat_on[0] -= 1
        for dt in dig_ts:
            x, y = dt.get_position()
            y -= 0.24
            if y < -H:
                y = H; x = rng.uniform(-W, W)
                dt.set_text(str(rng.integers(0,10)))
            dt.set_position((x, y))
            dt.set_visible(True)
        if frame % 2 == 0:
            random.choice(dig_ts).set_text(str(rng.integers(0,10)))
    else:
        for dt in dig_ts:
            dt.set_visible(False)

    # ══════════════════════════════════════════════════════
    #  ФЕЙЕРВЕРКИ
    # ══════════════════════════════════════════════════════
    if fw_on[0] > 0:
        fw_on[0] -= 1
        fw_pos  += fw_vel
        fw_vel[:,1] -= 0.003
        fw_life -= 1/(3.5*FPS)
        fw_life  = np.clip(fw_life, 0, 1)
        cols        = fw_col.copy()
        cols[:,3]   = fw_life
        sizes       = fw_life * 120
        fw_scat.set_offsets(fw_pos)
        fw_scat.set_sizes(sizes)
        fw_scat.set_color(cols)
        if fw_on[0] % int(1.1*FPS) == 0:
            boom()
        fw_scat.set_visible(True)
    else:
        fw_scat.set_visible(False)

    # ══════════════════════════════════════════════════════
    #  СКРИМЕР + САНЯ БЛЯТЬ ПИТУХ ЕПТА
    # ══════════════════════════════════════════════════════
    if sc_on[0] > 0:
        sc_on[0] -= 1
        prog = sc_on[0] / SC_DUR

        sc_bg.set_alpha(min(prog*3, 0.90))

        # Мигание цвета текста
        col_cycle = plt.cm.hsv((sc_on[0] * 0.12) % 1.0)
        sc_main.set_color(col_cycle[:3])
        sc_main.set_fontsize(75 + 25*abs(math.sin(sc_on[0]*0.35)))

        # Дрожание
        jx = rng.uniform(-0.5, 0.5)
        jy = rng.uniform(-0.2, 0.2)
        sc_main.set_position((jx, 1.0+jy))
        sc_face.set_position((jx*0.5, -2.2+jy*0.5))
        sc_face.set_fontsize(90 + 30*abs(math.sin(sc_on[0]*0.4)))

        for obj in (sc_main, sc_face, sc_sub):
            obj.set_visible(True)
    else:
        sc_bg.set_alpha(0)
        for obj in (sc_main, sc_face, sc_sub):
            obj.set_visible(False)

    # ══════════════════════════════════════════════════════
    #  ТАЙТЛ
    # ══════════════════════════════════════════════════════
    hue = (t*0.45) % 1.0
    title.set_color(plt.cm.hsv(hue)[:3])
    title.set_fontsize(22 + 6*abs(math.sin(t*3.5)))

    return ALL

# ══════════════════════════════════════════════════════════════
#  ЗАПУСК
# ══════════════════════════════════════════════════════════════
ani = animation.FuncAnimation(
    fig, update,
    frames=1_000_000,
    interval=max(1, 1000//FPS),
    blit=True
)

fig.canvas.mpl_connect('key_press_event',
    lambda e: plt.close() if e.key in ('escape','q') else None)

plt.tight_layout(pad=0)
plt.show()
