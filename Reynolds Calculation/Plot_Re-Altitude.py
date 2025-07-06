import matplotlib.pyplot as plt
import numpy as np
from aerocalc.std_atm import alt2density, alt2dynamic_viscosity

# Função para cálculo do número de Reynolds
def reynolds_by_altitude(h_m, V, L):
    h_ft = h_m * 3.281
    rho = alt2density(h_ft, density_units='kg/m**3', alt_units='ft')
    mu = alt2dynamic_viscosity(h_ft, alt_units='ft')
    Re = (rho * V * L) / mu
    return Re

# Parâmetros da curva
altitudes = np.arange(0, 3000, 10)  # metros
V = 30      # m/s
L = 0.358   # m
Re_array = np.array([reynolds_by_altitude(h, V, L) for h in altitudes])

# Entrada do usuário
try:
    h_user = float(input("Digite uma altitude (em metros): "))
    Re_user = reynolds_by_altitude(h_user, V, L)
    print(f"Número de Reynolds para {h_user:.0f} m: {Re_user:.0f}")
except Exception as e:
    print("Erro na entrada:", e)
    h_user = None
    Re_user = None

# Plot
plt.figure(figsize=(8, 5))
plt.plot(altitudes, Re_array, label='Reynolds vs Altitude', color='blue')
plt.xlabel('Altitude (m)')
plt.ylabel('Número de Reynolds')
plt.title('Número de Reynolds em função da Altitude')
plt.grid(True)

# Ponto digitado
if h_user is not None:
    plt.plot(h_user, Re_user, 'ro', label=f'Ponto ({h_user:.0f} m)')
    plt.annotate(f"{Re_user:.0f}", (h_user, Re_user),
                 textcoords="offset points", xytext=(10,10), ha='left', color='red')

plt.legend()
plt.tight_layout()
plt.show()
