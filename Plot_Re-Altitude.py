import matplotlib.pyplot as plt
from reynolds_by_altitude import reynolds_by_altitude
import numpy as np

# Parâmetros
altitudes = np.arange(0, 3000, 10)  # Altitude de 0 a 11.000 m
V = 30      # Velocidade (m/s)
L = 0.358     # Comprimento característico (m)

# Cálculo
Re = reynolds_by_altitude(altitudes, V, L)

# Plot
plt.figure(figsize=(8,5))
plt.plot(altitudes, Re, marker='o')
plt.xlabel('Altitude (m)')
plt.ylabel('Número de Reynolds')
plt.title('Reynolds vs Altitude')
plt.grid(True)
plt.tight_layout()
plt.show()



