import numpy as np
import scipy.stats as sps
import matplotlib.pyplot as plt
from scipy.signal import chirp

x_dist = np.linspace(-1, 2, 1000)
pdf = sps.uniform.pdf(x_dist, loc=0, scale=1)
#(равномерного распределения) (плотности вероятности)

plt.figure(1, figsize=(8, 4))
plt.plot(x_dist, pdf, color='blue', lw=2)
plt.fill_between(x_dist, pdf, color='blue', alpha=0.2)
plt.title('Равномерное распределение')
plt.xlabel('Значение')
plt.ylabel('Плотность')
plt.grid(True)

# t = np.linspace(6, 10, 1000)
# w = chirp(t, f0=4, f1=1, t1=10, method='linear')
#
# plt.figure(2, figsize=(8, 4))
# plt.plot(t, w, color='red', lw=1.5)
# plt.title('Сигнал')
# plt.xlabel('Время')
# plt.ylabel('Амплитуда')
# plt.grid(True)
plt.show()