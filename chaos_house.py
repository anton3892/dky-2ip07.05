"""
██████╗██╗  ██╗ █████╗  ██████╗ ███████╗    ███╗   ███╗ ██████╗ ██████╗ ███████╗
██╔════╝██║  ██║██╔══██╗██╔═══██╗██╔════╝    ████╗ ████║██╔═══██╗██╔══██╗██╔════╝
██║     ███████║███████║██║   ██║███████╗    ██╔████╔██║██║   ██║██║  ██║█████╗
██║     ██╔══██║██╔══██║██║   ██║╚════██║    ██║╚██╔╝██║██║   ██║██║  ██║██╔══╝
╚██████╗██║  ██║██║  ██║╚██████╔╝███████║    ██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.colors as mcolors
from matplotlib.patches import Polygon
import random

# ═══════════════════════════════════════════════════════════════════
#  ФИГУРА
# ═══════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(13, 10), facecolor='black')
ax  = fig.add_axes([0, 0, 1, 1])
ax.set_facecolor('black')
ax.set_xlim(-6.5, 6.5)
ax.set_ylim(-5.5, 5.5)
ax.set_aspect('equal')
ax.axis('off')

FPS = 60
rng = np.random.default_rng(7)

# ═══════════════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════
def r2d(pts, a):
    c, s = np.cos(a), np.sin(a)
    return pts @ np.array([[c,-s],[s,c]]).T

def rot3d(pts, rx, ry, rz):
    Rx=np.array([[1,0,0],[0,np.cos(rx),-np.sin(rx)],[0,np.sin(rx),np.cos(rx)]])
    Ry=np.array([[np.cos(ry),0,np.sin(ry)],[0,1,0],[-np.sin(ry),0,np.cos(ry)]])
    Rz=np.array([[np.cos(rz),-np.sin(rz),0],[np.sin(rz),np.cos(rz),0],[0,0,1]])
    return pts @ (Rz@Ry@Rx).T

def proj3d(pts, fov=8):
    d = pts[:,2]/fov + 2.0
    return np.column_stack([pts[:,0]/d, pts[:,1]/d])

def box_v(w,h,d):
    hw,hh,hd=w/2,h/2,d/2
    return np.array([
        [-hw,-hh,-hd],[hw,-hh,-hd],[hw,hh,-hd],[-hw,hh,-hd],
        [-hw,-hh, hd],[hw,-hh, hd],[hw,hh, hd],[-hw,hh, hd]
    ],dtype=float)

BEDGES=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]

# ═══════════════════════════════════════════════════════════════════
#  ОБЪЕКТЫ
# ═══════════════════════════════════════════════════════════════════

# ── 1. ТРЕУГОЛЬНИК ──────────────────────────────────────────────
BASE_TRI = np.array([[0,1.6],[-1.38,-0.8],[1.38,-0.8]])
N_T = 18
tris = [ax.add_patch(Polygon(BASE_TRI, closed=True, animated=True, zorder=5)) for _ in range(N_T)]

# ── 2. КРУГИ ─────────────────────────────────────────────────────
N_CIRC = 12
circ_lines = []
for i in range(N_CIRC):
    l, = ax.plot([],[],'-', lw=1.5+i*0.1, animated=True, zorder=3)
    circ_lines.append(l)

# ── 3. КВАДРАТЫ ──────────────────────────────────────────────────
N_SQ = 16
sq_cfgs = [(
    rng.uniform(-4.5,4.5), rng.uniform(-3.5,3.5),
    rng.uniform(0.2,0.9),
    rng.uniform(0,2*np.pi),
    rng.uniform(1.5,6.5),
    rng.uniform(0,1)
) for _ in range(N_SQ)]
sq_lines = [ax.plot([],[],'-', lw=1.4, animated=True, zorder=4)[0] for _ in range(N_SQ)]

# ── 4. ПАРАЛЛЕЛЕПИПЕДЫ ───────────────────────────────────────────
N_BOX = 12
box_cfgs = []
box_ln   = []
for i in range(N_BOX):
    ang = 2*np.pi*i/N_BOX + np.pi/N_BOX
    r   = rng.uniform(2.0,4.2)
    box_cfgs.append(dict(
        cx=r*np.cos(ang), cy=r*np.sin(ang)*0.75,
        verts=box_v(*rng.uniform(0.25,0.65,3)),
        ph=rng.uniform(0,2*np.pi),
        sp=rng.uniform(1.8,5.0),
        hue=i/N_BOX
    ))
    lns = [ax.plot([],[],'-',lw=1.0,animated=True,zorder=4)[0] for _ in BEDGES]
    box_ln.append(lns)

# ── 5. ВОРТЕКС ───────────────────────────────────────────────────
N_VORT = 80
vort_lines = [ax.plot([],[],'-',lw=0.7,animated=True,alpha=0.75,zorder=2)[0] for _ in range(N_VORT)]
vort_on = [0]

# ── 6. МАТРИЦА ЦИФР ──────────────────────────────────────────────
N_DIG = 120
dig_texts = []
for _ in range(N_DIG):
    t=ax.text(rng.uniform(-6.5,6.5),rng.uniform(-5.5,5.5),
              str(rng.integers(0,10)),
              color='lime', fontsize=int(rng.integers(8,26)),
              ha='center',va='center',
              animated=True,visible=False,
              fontfamily='monospace',zorder=6,fontweight='bold')
    dig_texts.append(t)
mat_on = [0]

# ── 7. ФЕЙЕРВЕРКИ ────────────────────────────────────────────────
NF = 300
fw_pos   = np.zeros((NF,2))
fw_vel   = np.zeros((NF,2))
fw_life  = np.zeros(NF)
fw_col   = np.zeros((NF,4))
fw_scat  = ax.scatter([],[],s=[],c=[],animated=True,zorder=7)
fw_on    = [0]

def boom():
    fw_on[0] = int(4*FPS)
    for i in range(NF):
        cx = rng.uniform(-3,3)
        cy = rng.uniform(-2,2)
        a  = rng.uniform(0,2*np.pi)
        sp = rng.uniform(0.03,0.35)
        fw_pos[i]  = [cx, cy]
        fw_vel[i]  = [sp*np.cos(a), sp*np.sin(a)]
        fw_life[i] = rng.uniform(0.4,1.0)
        c = mcolors.to_rgba(rng.choice(
            ['red','orange','gold','yellow','lime','cyan','magenta','white','deepskyblue','hotpink']))
        fw_col[i] = c

# ── 8. СКРИМЕР ───────────────────────────────────────────────────
FACES   = ['😱','💀','👁️','😈','🤡','👻','🫀','🦴','🔪','☠️']
WORDS   = [('ТЫ НЕ ГОТОВ','БЕГИ'),('ОНО ПРИШЛО','СПАСАЙСЯ'),
           ('СМОТРИ НАЗАД','ОНО ТАМ'),('КОНЕЦ БЛИЗКО','ХА-ХА-ХА'),
           ('ДОБРО ПОЖАЛОВ.','В АД'),('Я ВИЖУ ТЕБЯ','ОНО ЗНАЕТ'),
           ('НЕ СМОТРИ','УЖЕ ПОЗДНО')]
sc_bg  = ax.fill([-6.5,-6.5,6.5,6.5],[-5.5,5.5,5.5,-5.5],
                 color='red',alpha=0,animated=True,zorder=8)[0]
sc_face= ax.text(0,0.8,'',fontsize=140,ha='center',va='center',
                 animated=True,visible=False,zorder=9)
sc_t1  = ax.text(0,-1.6,'',fontsize=34,ha='center',va='center',
                 color='white',fontweight='bold',animated=True,visible=False,zorder=9)
sc_t2  = ax.text(0,-2.7,'',fontsize=22,ha='center',va='center',
                 color='yellow',animated=True,visible=False,zorder=9)
sc_on  = [0]

def SCREAM():
    sc_on[0] = int(1.8*FPS)
    face   = random.choice(FACES)
    w1, w2 = random.choice(WORDS)
    sc_face.set_text(face)
    sc_t1.set_text(w1)
    sc_t2.set_text(w2)
    sc_bg.set_facecolor(random.choice(['red','#7b0000','purple','#1a0050']))

# ── 9. ВЗРЫВНЫЕ НАДПИСИ ──────────────────────────────────────────
BANGS = ['ХАОС!','BOOM!','ВАУ!','PANIC!','КАК?!','ААААА!','ЧТО?!','🔥🔥🔥','ХЕЛП!','МОЩЬ!']
bang_t = ax.text(0,0,'',fontsize=50,ha='center',va='center',
                 color='red',fontweight='bold',animated=True,visible=False,zorder=10)
bang_on= [0]

def fire_bang():
    bang_on[0] = int(0.7*FPS)
    bang_t.set_text(random.choice(BANGS))
    bang_t.set_position((rng.uniform(-3,3),rng.uniform(-2.5,2.5)))
    bang_t.set_color(rng.choice(['red','orange','yellow','cyan','magenta','white']))
    bang_t.set_fontsize(int(rng.integers(40,90)))

# ── 10. ТАЙТЛ ────────────────────────────────────────────────────
title = ax.text(0,5.0,'🔥 CHAOS MODE 🔥',fontsize=28,ha='center',va='center',
                color='white',fontweight='bold',animated=True,zorder=10)

# ── 11. СТРОБОСКОП ФОН ──────────────────────────────────────────
bg_fill = ax.fill([-6.5,-6.5,6.5,6.5],[-5.5,5.5,5.5,-5.5],
                  color='black',alpha=1.0,animated=True,zorder=0)[0]

# ═══════════════════════════════════════════════════════════════════
#  ТАЙМЛАЙН: 0..10s цикл
#  0–6.5s  : normal chaos
#  6.5–8s  : SCREAMER
#  8–11.5s : FIREWORKS
#  11.5–14.5s: MATRIX
#  14.5–16.5s: VORTEX
# ═══════════════════════════════════════════════════════════════════
PHASES = [
    (int(6.5*FPS), 'chaos'),
    (int(1.8*FPS), 'scream'),
    (int(3.5*FPS), 'fireworks'),
    (int(3.0*FPS), 'matrix'),
    (int(2.0*FPS), 'vortex'),
]
ph_timer = [0]
ph_idx   = [0]
ph_name  = ['chaos']

tri_ang  = [0.0]

# ═══════════════════════════════════════════════════════════════════
#  ALL ARTISTS для blit
# ═══════════════════════════════════════════════════════════════════
ALL = ([bg_fill] + tris + circ_lines + sq_lines +
       [l for ls in box_ln for l in ls] +
       vort_lines + [fw_scat] + dig_texts +
       [sc_bg, sc_face, sc_t1, sc_t2] +
       [bang_t, title])

# ═══════════════════════════════════════════════════════════════════
#  UPDATE
# ═══════════════════════════════════════════════════════════════════
def update(frame):
    t = frame / FPS

    # ── PHASE MANAGER ──
    ph_timer[0] += 1
    dur, _ = PHASES[ph_idx[0]]
    if ph_timer[0] >= dur:
        ph_timer[0] = 0
        ph_idx[0]   = (ph_idx[0]+1) % len(PHASES)
        ph_name[0]  = PHASES[ph_idx[0]][1]
        if ph_name[0] == 'scream':      SCREAM()
        if ph_name[0] == 'fireworks':   boom()
        if ph_name[0] == 'matrix':
            mat_on[0] = int(3.0*FPS)
            for dt in dig_texts:
                dt.set_position((rng.uniform(-6.5,6.5), rng.uniform(-5.5,5.5)))
                dt.set_text(str(rng.integers(0,10)))
                dt.set_color(rng.choice(['lime','cyan','#00ff88','#aaff00','white']))
        if ph_name[0] == 'vortex':
            vort_on[0] = int(2.0*FPS)

    cur = ph_name[0]

    # случайный взрыв фраз каждые ~2 сек
    if frame % (2*FPS) == (FPS//3):
        fire_bang()

    # ── СТРОБОСКОП / ФОН ──
    if cur == 'scream':
        bg_fill.set_facecolor((0.4,0,0,1))
    elif cur == 'fireworks':
        hue = (t*0.6) % 1.0
        c   = plt.cm.hsv(hue)
        bg_fill.set_facecolor((*c[:3], 0.05))
    elif cur == 'vortex':
        bg_fill.set_facecolor((0,0,0.2,1))
    else:
        bg_fill.set_facecolor((0,0,0,1))

    # ── ТРЕУГОЛЬНИК ──
    tri_ang[0] += 0.42
    for i,tri in enumerate(tris):
        a   = tri_ang[0] - i*0.21
        pts = r2d(BASE_TRI, a)
        tri.set_xy(pts)
        alpha = (N_T-i)/N_T
        hue   = (tri_ang[0]/(2*np.pi)+i*0.065) % 1.0
        c     = plt.cm.hsv(hue)
        tri.set_facecolor((*c[:3], alpha*0.9))
        tri.set_edgecolor((*c[:3], alpha))
        tri.set_linewidth(3.0 if i==0 else 0.4)

    # ── КРУГИ ──
    for i,l in enumerate(circ_lines):
        r    = 0.35 + i*0.5
        sq   = 0.55 + 0.45*np.sin(t*1.3+i)
        off  = t*(1.2+i*0.28) + i*0.5
        th   = np.linspace(0,2*np.pi,100) + off
        l.set_data(r*np.cos(th), r*np.sin(th)*sq)
        hue  = (i/N_CIRC + t*0.12) % 1.0
        c    = plt.cm.cool(hue)
        l.set_color(c)
        l.set_alpha(0.5+0.5*np.abs(np.sin(t+i)))
        l.set_linewidth(0.8+2.0*np.abs(np.sin(t*0.7+i*0.3)))

    # ── КВАДРАТЫ ──
    for (cx,cy,sz,ph,sp,h),l in zip(sq_cfgs, sq_lines):
        ang  = t*sp + ph
        orb  = 0.6*np.sin(t*1.1+ph)
        pts  = r2d(np.array([[1,1],[-1,1],[-1,-1],[1,-1],[1,1]])*sz/2, ang)
        l.set_data(pts[:,0]+cx+orb, pts[:,1]+cy+orb*0.7)
        hue  = (h + t*0.09) % 1.0
        l.set_color(plt.cm.rainbow(hue))
        l.set_linewidth(1.8)

    # ── ПАРАЛЛЕЛЕПИПЕДЫ ──
    for bc,lns in zip(box_cfgs, box_ln):
        ph,sp = bc['ph'], bc['sp']
        rx    = t*sp + ph
        ry    = t*sp*0.85 + ph*1.2
        rz    = np.sin(t*sp*0.55+ph)*2.8
        rv    = rot3d(bc['verts'], rx, ry, rz)
        pr    = proj3d(rv)
        pr[:,0] += bc['cx']
        pr[:,1] += bc['cy']
        hue = (bc['hue'] + t*0.06) % 1.0
        c   = plt.cm.plasma(hue)
        for (e0,e1),ln in zip(BEDGES, lns):
            ln.set_data([pr[e0,0],pr[e1,0]], [pr[e0,1],pr[e1,1]])
            ln.set_color(c)

    # ── ВОРТЕКС ──
    if vort_on[0] > 0:
        vort_on[0] -= 1
        for i,vl in enumerate(vort_lines):
            theta = t*6 + i*2*np.pi/N_VORT
            rs    = np.linspace(0.05,5.5,40)
            ths   = theta + rs*0.85
            vl.set_data(rs*np.cos(ths), rs*np.sin(ths)*0.78)
            hue  = (i/N_VORT + t*0.25) % 1.0
            vl.set_color(plt.cm.hsv(hue))
            vl.set_visible(True)
    else:
        for vl in vort_lines:
            vl.set_visible(False)

    # ── ФЕЙЕРВЕРКИ ──
    if fw_on[0] > 0:
        fw_on[0] -= 1
        fw_pos  += fw_vel
        fw_vel[:,1] -= 0.004
        fw_life -= 1/(3.5*FPS)
        fw_life  = np.clip(fw_life, 0, 1)
        alive    = fw_life > 0
        if alive.any():
            cols      = fw_col.copy()
            cols[:,3] = fw_life
            sizes     = fw_life * 90
            sizes[~alive] = 0
            fw_scat.set_offsets(fw_pos)
            fw_scat.set_sizes(sizes)
            fw_scat.set_color(cols)
        # периодически перезапускаем взрыв
        if fw_on[0] % int(1.2*FPS) == 0:
            boom()
        fw_scat.set_visible(True)
    else:
        fw_scat.set_visible(False)

    # ── МАТРИЦА ──
    if mat_on[0] > 0:
        mat_on[0] -= 1
        for dt in dig_texts:
            x,y = dt.get_position()
            y  -= 0.22
            if y < -5.5:
                y = 5.5
                x = rng.uniform(-6.5,6.5)
                dt.set_text(str(rng.integers(0,10)))
            dt.set_position((x,y))
            dt.set_visible(True)
        if frame % 3 == 0:
            random.choice(dig_texts).set_text(str(rng.integers(0,10)))
    else:
        for dt in dig_texts:
            dt.set_visible(False)

    # ── СКРИМЕР ──
    if sc_on[0] > 0:
        sc_on[0] -= 1
        prog = sc_on[0]/(1.8*FPS)
        sc_bg.set_alpha(min(prog*2.5, 0.93))
        sc_face.set_visible(True)
        sc_t1.set_visible(True)
        sc_t2.set_visible(True)
        jx,jy = rng.uniform(-0.35,0.35), rng.uniform(-0.2,0.2)
        sc_face.set_position((jx, 0.8+jy))
        sc_face.set_fontsize(130+40*np.sin(sc_on[0]*0.4))
    else:
        sc_bg.set_alpha(0)
        sc_face.set_visible(False)
        sc_t1.set_visible(False)
        sc_t2.set_visible(False)

    # ── ВЗРЫВНЫЕ НАДПИСИ ──
    if bang_on[0] > 0:
        bang_on[0] -= 1
        bang_t.set_visible(True)
        scale = 1.0 + 0.5*np.sin(bang_on[0]*0.5)
        bang_t.set_fontsize(int(50*scale))
    else:
        bang_t.set_visible(False)

    # ── ТАЙТЛ ──
    hue = (t*0.5) % 1.0
    title.set_color(plt.cm.hsv(hue)[:3])
    title.set_fontsize(28 + 5*np.sin(t*4))

    return ALL

ani = animation.FuncAnimation(fig, update, frames=500_000, interval=1000//FPS, blit=True)
plt.tight_layout(pad=0)
plt.show()
