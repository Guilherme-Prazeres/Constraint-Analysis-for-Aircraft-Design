import numpy as np

def reynolds_properties(h, V, L):
    # Constantes da atmosfera padrão
    T0 = 288.15       # K
    P0 = 101325       # Pa
    Lb = 0.0065       # K/m
    R = 8.3144598     # J/(mol·K)
    g = 9.80665       # m/s²
    M = 0.0289644     # kg/mol
    mu0 = 1.716e-5    # Pa·s
    C = 110.4         # K

    # Temperatura
    T = T0 - Lb * h

    # Pressão
    P = P0 * (T / T0)**(g * M / (R * Lb))

    # Densidade
    rho = (P * M) / (R * T)

    # Viscosidade dinâmica
    mu = mu0 * (T / T0)**1.5 * (T0 + C) / (T + C)

    # Número de Reynolds
    Re = (rho * V * L) / mu

    return Re, mu, rho, P, T


if __name__ == "__main__":
    # Entrada do usuário
    try:
        h = float(input("Digite a altitude (em metros): "))
        V = float(input("Digite a velocidade (m/s): "))
        L = float(input("Digite o comprimento característico (m): "))

        Re, mu, rho, P, T = reynolds_properties(h, V, L)

        # Resultados formatados
        print("\nResultados:")
        print(f"Temperatura (T):       {T:.2f} K")
        print(f"Pressão (P):           {P:.2f} Pa")
        print(f"Densidade (rho):       {rho:.4f} kg/m³")
        print(f"Viscosidade (mu):      {mu:.6e} Pa·s")
        print(f"Número de Reynolds:    {Re:.0f}")

    except ValueError:
        print("Por favor, digite apenas valores numéricos.")
