import numpy as np

def reynolds_by_altitude(h, V, L):
    # Constantes da atmosfera padrão
    T0 = 288.15        # Temperatura ao nível do mar [K]
    P0 = 101325        # Pressão ao nível do mar [Pa]
    Lb = 0.0065        # Gradiente térmico [K/m]
    R = 8.3144598      # Constante universal dos gases [J/(mol·K)]
    g = 9.80665        # Gravidade [m/s²]
    M = 0.0289644      # Massa molar do ar [kg/mol]
    mu0 = 1.716e-5     # Viscosidade dinâmica ao nível do mar [Pa·s]
    C = 110.4          # Constante de Sutherland [K]

    # Garantir vetor numpy
    h = np.array(h)

    # Temperatura [K]
    T = T0 - Lb * h

    # Pressão [Pa]
    P = P0 * (T / T0) ** (g * M / (R * Lb))

    # Densidade [kg/m³]
    rho = (P * M) / (R * T)

    # Viscosidade dinâmica [Pa·s] - Sutherland
    mu = mu0 * (T / T0)**1.5 * (T0 + C) / (T + C)

    # Número de Reynolds (adimensional)
    Re = (rho * V * L) / mu

    return Re

