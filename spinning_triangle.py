import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

fig, ax = plt.subplots(figsize=(6, 6), facecolor='black')
ax.set_facecolor('black')
ax.set_xlim(-2, 2)
ax.set_ylim(-2, 2)
ax.set_aspect('equal')
ax.axis('off')

# Базовые вершины треугольника
base_triangle = np.array([
    [0,  1.2],
    [-1.04, -0.6],
    [ 1.04, -0.6],
])

# Создаём несколько треугольников для эффекта шлейфа
n_trail = 12
triangles = []
colors = []

for i in range(n_trail):
    tri = Polygon(base_triangle, closed=True)
    triangles.append(tri)
    ax.add_patch(tri)

angle_ref = [0.0]

def rotate(points, angle):
    c, s = np.cos(angle), np.sin(angle)
    R = np.array([[c, -s], [s, c]])
    return points @ R.T

def update(frame):
    speed = 0.35  # радиан за кадр — очень быстро
    angle_ref[0] += speed

    for i, tri in enumerate(triangles):
        trail_angle = angle_ref[0] - i * 0.18
        rotated = rotate(base_triangle, trail_angle)
        tri.set_xy(rotated)

        alpha = (n_trail - i) / n_trail
        # Радужный цвет по углу
        hue = (angle_ref[0] / (2 * np.pi) + i * 0.08) % 1.0
        color = plt.cm.hsv(hue)
        tri.set_facecolor((*color[:3], alpha * 0.85))
        tri.set_edgecolor((*color[:3], alpha))
        tri.set_linewidth(2 if i == 0 else 0.5)

    return triangles

ani = animation.FuncAnimation(
    fig, update,
    frames=1000,
    interval=16,   # ~60 FPS
    blit=True
)

plt.title("⚡ SPINNING TRIANGLE ⚡", color='white', fontsize=14, pad=10)
plt.tight_layout()
plt.show()
