# Feito por Guilherme Prazeres 
import math
from dataclasses import dataclass, field
from aerocalc import std_atm as ISA

# ---------------------------------------------------------------------------
# DEFINIR CLASSES DE CONFIGURAÇÃO (INPUTS) COM DATACLASSES
# ---------------------------------------------------------------------------

@dataclass
class GeometriaConfig:
    """Parâmetros Geométricos da Aeronave."""
    AR_: float = 13  # Alongamento (Adimensional)

@dataclass
class PesoConfig:
    """Parâmetros de Peso da Aeronave."""
    maxGrossWeight_kg: float = 40

@dataclass
class AerodinamicaConfig:
    """Parâmetros Aerodinâmicos Fundamentais."""
    CDmin_: float = 0.0418  # Coeficiente de arrasto parasita mínimo
    CLTO_: float = 0.97     # Coeficiente de sustentação na decolagem
    CDTO_: float = 0.0898    # Coeficiente de arrasto na decolagem
    CLmaxApproach_: float = 1.6 # CL máximo na aproximação

@dataclass
class PerformanceConfig:
    """Requisitos de Performance."""
    # Geral
    PropEff_: float = 0.6  # Eficiência da hélice
    ServiceCeiling_m: float = 120 # Teto de serviço

    # Decolagem
    GroundRunTakeOff_m: float = 120
    TakeOffSpeed_mps: float = 16
    TakeOffElevation_m: float = 0
    muTO_: float = 0.17  # Coeficiente de atrito no solo

    # Cruzeiro
    CruisingAlt_m: float = 120
    CruisingSpeed_mps: float = 30

    # Subida
    RateOfClimb_mps: float = 3.0
    ROCAlt_m: float = 0.0

    # Curva
    angleOfBank_deg: float = 35

    # Pouso
    GroundrunLanding_m: float = 100
    StallReserveFactor_: float = 1.1
    TopOfFinalApproach_m = 15.24  # 50 ft utilizando FAR-23 para sizing

@dataclass
class Config:
    """Agregador de todas as configurações de design."""
    geo: GeometriaConfig = field(default_factory=GeometriaConfig)
    peso: PesoConfig = field(default_factory=PesoConfig)
    aero: AerodinamicaConfig = field(default_factory=AerodinamicaConfig)
    perf: PerformanceConfig = field(default_factory=PerformanceConfig)


# ---------------------------------------------------------------------------
# PASSO 2: CRIAR A CLASSE PRINCIPAL "AERONAVE" (FACADE PATTERN)
# Esta classe é o ponto central. Ela recebe a configuração e expõe todos os
# parâmetros (de entrada e calculados) de forma simples.
# ---------------------------------------------------------------------------

class Aeronave:
    """
    Classe principal que representa a aeronave.
    
    Objeto de configuração e todos os cálculos são realizados internamente como
    propriedades.
    """
    def __init__(self, config: Config):
        self._config = config
    
    # --- Acesso simplificado às configurações de entrada ---
    @property
    def config(self) -> Config:
        return self._config

    # --- Propriedades Atmosféricas ---
    @property
    def SeaLevelDens_kgm3(self) -> float:
        return ISA.alt2density(0, density_units='kg/m**3', alt_units='m')

    @property
    def TakeOffDens_kgm3(self) -> float:
        return ISA.alt2density(self.config.perf.TakeOffElevation_m, density_units='kg/m**3', alt_units='m')

    @property
    def CruisingAltDens_kgm3(self) -> float:
        return ISA.alt2density(self.config.perf.CruisingAlt_m, density_units='kg/m**3', alt_units='m')
        
    @property
    def ClimbAltDens_kgm3(self) -> float:
        return ISA.alt2density(self.config.perf.ROCAlt_m, density_units='kg/m**3', alt_units='m')
    
    @property
    def ApproachDens_kgm3(self) -> float:
        return ISA.alt2density(self.config.perf.TopOfFinalApproach_m, density_units='kg/m**3', alt_units='m')

    # --- Propriedades Aerodinâmicas  ---
    @property
    def oswaldFactor_e0(self) -> float:
        # Equação para estimar fator de oswald segundo Raymer cap12
        return 1.78 * (1 - 0.045 * self.config.geo.AR_**0.68) - 0.64
    
    @property
    def inducedDragFactor_k(self) -> float:
        return 1.0 / (math.pi * self.config.geo.AR_ * self.oswaldFactor_e0)
    
    @property
    def q_Cruise_pa(self) -> float:
        return 0.5 * self.CruisingAltDens_kgm3 * (self.config.perf.CruisingSpeed_mps**2)

    @property
    def q_Climb_pa(self) -> float:
        return 0.5 * self.ClimbAltDens_kgm3 * (self.ClimbSpeed_mps**2)
        
    @property
    def q_TakeOff_pa(self) -> float:
        # Velocidade média durante a corrida de decolagem (V_LOF / sqrt(2))
        return 0.5 * self.TakeOffDens_kgm3 * (self.config.perf.TakeOffSpeed_mps / math.sqrt(2))**2

    @property
    def q_Approach_pa(self) -> float:
        return 0.5 * self.ApproachDens_kgm3 * (self.ApproachSpeed_mps**2)

    # --- Propriedades de Performance ---
        
    @property
    def TimeToServiceCeiling_sec(self) -> int:
        return self.config.perf.ServiceCeiling_m / self.config.perf.RateOfClimb_mps

    @property
    def ClimbSpeed_mps(self) -> float:
        # Exemplo: velocidade de subida como 80% da velocidade de cruzeiro
        return self.config.perf.CruisingSpeed_mps * 0.8
        
    @property
    def loadFactorTurn_n(self) -> float:
        # Fator de carga em curva (n)
        return 1 / math.cos(math.radians(self.config.perf.angleOfBank_deg))
        
    @property
    def StallSpeedLanding_mps(self) -> float:
       # Estimativa baseada em Gudmundsson, "General Aviation Aircraft Design", eq. 17.30
       # V_stall = sqrt(S_G / 0.5136) em nós, depois convertido para m/s
       s_g_ft = self.config.perf.GroundrunLanding_m * 3.281
       v_stall_knots = math.sqrt(s_g_ft / 0.5136)
       return v_stall_knots * 0.514444

    @property
    def ApproachSpeed_mps(self) -> float:
        return self.StallSpeedLanding_mps * self.config.perf.StallReserveFactor_
    

    # --- Método de Resumo ---
    def resume(self):
        """Imprime um resumo completo dos parâmetros de entrada e calculados."""
        print("=============== RESUMO DOS PARÂMETROS DA AERONAVE ===============")
        
        def print_config_section(name, config_obj):
            print(f"\n--- {name} (Inputs) ---")
            for key, value in config_obj.__dict__.items():
                if isinstance(value, (int, float)):
                    print(f"{key:35}: {value:.3f}")
                else:
                    print(f"{key:35}: {value}")

        print_config_section("Configurações de Geometria", self.config.geo)
        print_config_section("Configurações de Peso", self.config.peso)
        print_config_section("Configurações de Aerodinâmica", self.config.aero)
        print_config_section("Configurações de Performance", self.config.perf)
        
        print("\n--- Parâmetros Calculados ---")
        calculated_props = {
            "Densidade ao Nível do Mar (kg/m³)": self.SeaLevelDens_kgm3,
            "Densidade na Altitude de Decolagem (kg/m³)": self.TakeOffDens_kgm3,
            "Densidade na Altitude de Cruzeiro (kg/m³)": self.CruisingAltDens_kgm3,
            "Fator de Oswald (e0)": self.oswaldFactor_e0,
            "Fator de Arrasto Induzido (k)": self.inducedDragFactor_k,
            "Pressão Dinâmica em Cruzeiro (Pa)": self.q_Cruise_pa,
            "Pressão Dinâmica na Subida (Pa)": self.q_Climb_pa,
            "Pressão Dinâmica na Decolagem (Pa)": self.q_TakeOff_pa,
            "Razão de Subida (m/s)": self.RateOfClimb_mps,
            "Fator de Carga em Curva (n)": self.loadFactorTurn_n,
            "Velocidade de Estol no Pouso (m/s)": self.StallSpeedLanding_mps,
            "Velocidade de Aproximação (m/s)": self.ApproachSpeed_mps,
        }
        
        for key, value in calculated_props.items():
            print(f"{key:45}: {value:.4f}")
        
        print("\n========================= FIM DO RESUMO =========================")