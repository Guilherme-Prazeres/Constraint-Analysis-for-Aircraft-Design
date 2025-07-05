# Essa classe define todos os parametros de design iniciais da aeronave para a estimativa e calulo do diagrama de restrições
# TODOS os Input devem ser feitos em SI

# Cada variavel segue a seguinte notação:
#   NomedaVariavel_unidade
#   NomedaVariavel_ <- Apenas underline significa que é adimensional

# Feito por Guilherme Prazeres 
import math
from aerocalc import std_atm as ISA

class Geometria:
    def __init__(self):
        # Parametros Geometricos iniciais
        self.AR_ = 13

class Performance:
    def __init__(self):
        # Estimativa de performance

        ## Decolagem 
        self.GroundRunTakeOff_m = 120
        self.TakeOffSpeed_mps = 16
        self.TakeOffElevation_m = 0
        self.CLTO_ = 0.97
        self.CDTO_ = 0.0898
        self.muTO_ = 0.17

        ## Cruzeiro
        self.CruisingAlt_m = 120
        self.CruisingSpeed_mps = 30

        ## Subida
        self.RateOfClimb_fpm = 600
        self.ROCAlt_ft = 0  # Altitude em que o Rate Of Climb (ROC) é verificado 

        ## Curva
        self.angleOfBank_deg = 35  # Angulo de bank
        
        ## Teto de serviço
        self.ServiceCeiling_m = 120

        ## Aproximação e pouso
        self.GroundrunLanding_m = 70
        self.StallReserveFactor = 1.1
        self.CLmaxApproach_ = 1.3
        self.TopOfFinalApproach_m = 30

    # ----- Conversoes e calculos -----

    # ------ Take Off ------
    @property
    def GroundRunTakeOff_ft(self):
        return self.GroundRunTakeOff_m * 3.281

    @property
    def TakeOffSpeed_KCAS(self):
        return self.TakeOffSpeed_mps / 1.943844  # Calibrated airspeed

    @property
    def TakeOffElevation_ft(self):
        return self.TakeOffElevation_m * 3.281

    # ------ Cruise ------
    @property
    def CruisingAlt_ft(self):
        return self.CruisingAlt_m * 3.281

    @property
    def CruisingSpeed_KTAS(self):
        return self.CruisingSpeed_mps * 1.943844  # True airspeed

    # ------ Climb ------
    @property
    def ClimbSpeed_KCAS(self):
        return self.CruisingSpeed_KTAS * 0.8

    @property
    def ClimbSpeed_mps(self):
        return self.ClimbSpeed_KCAS / 1.943844
    
    @property
    def RateOfClimb_mps(self):
        return self.RateOfClimb_fpm * 0.00508
    # ------ Curva ------

    @property
    def nTurn_(self):
        # Fator de carga nTurn_ é calculado como 1/cos(theta), onde theta é o angulo de bank
        return 1 / math.cos(math.radians(self.angleOfBank_deg))

    # ------ Teto de serviço ------
    @property
    def ServiceCeiling_ft(self):
        return self.ServiceCeiling_m * 3.281

    # ------ Landing e aproximação  ------
    @property
    def GroundrunLanding_ft(self):
        return self.GroundrunLanding_m * 3.281

    @property
    def StallSpeedLanding_KNOTS(self):
        return math.sqrt(self.GroundrunLanding_ft / 0.5136)

    @property
    def ApproachSpeed_KTAS(self):
        return self.StallSpeedLanding_KNOTS * self.StallReserveFactor
    
    @property
    def ApproachSpeed_mps(self):
        return self.ApproachSpeed_KTAS / 1.944

    @property
    def TopOfFinalApproach_ft(self):
        return self.TopOfFinalApproach_m * 3.281


class Atmosfera:
    def __init__(self, perf: Performance):
        self._perf = perf  # Armazena internamente

    @property
    def SeaLevelDens_kgm3(self):
        return ISA.alt2density(0, density_units='kg/m**3', alt_units='m')

    @property
    def TakeOffDens_kgm3(self):
        return ISA.alt2density(self._perf.TakeOffElevation_m, density_units='kg/m**3', alt_units='m')

    @property
    def ClimbAltDens_kgm3(self):
        return ISA.alt2density(self._perf.ROCAlt_ft, density_units='kg/m**3', alt_units='ft')

    @property
    def CruisingAltDens_kgm3(self):
        return ISA.alt2density(self._perf.CruisingAlt_m, density_units='kg/m**3', alt_units='m')

    @property
    def ApproachDens_kgm3(self):
        return ISA.alt2density(self._perf.TopOfFinalApproach_m, density_units='kg/m**3', alt_units='m')


class Aerodinamica:
    def __init__(self, geo: Geometria, perf: Performance, atm: Atmosfera):
        self.geo = geo
        self.perf = perf
        self.atm = atm

        self.CDmin_ = 0.0418

    @property
    def e0(self):    
        return 1.78*(1-0.045 * self.geo.AR_**0.68) - 0.64 # Equação para estimar fator de oswald segundo Raymer cap12
        
    @property
    def k(self):
        return 1.0/(math.pi*self.geo.AR_*self.e0)
        
    @property
    def qCruise_pa(self):
        return 0.5 * self.atm.CruisingAltDens_kgm3 * (self.perf.CruisingSpeed_mps**2)
        
    @property
    def qClimb_pa(self):
        return 0.5 * self.atm.ClimbAltDens_kgm3 * (self.perf.ClimbSpeed_mps**2)
    @property 
    def qTO_pa(self):
        return 0.5*self.atm.TakeOffDens_kgm3*(self.perf.TakeOffSpeed_mps/math.sqrt(2))**2
    @property
    def qApproach_pa(self):
        return 0.5*self.atm.ApproachDens_kgm3*self.perf.ApproachSpeed_mps**2

class Restricoes:
    def __init__(self):
        # Parametros para o diagrama de restrição
        self.WSmax_kgm2 = 30
        self.TWmax_ = 0.6
        self.Pmax_kW = 8

class Peso:
    def __init__(self):
        # Estimativa de peso
        self.maxGrossWeight_kg = 40

class DesignParameters:
    def __init__(self):
        self.geo = Geometria()
        self.peso = Peso()
        self.perf = Performance()
        self.rest = Restricoes()
        self.atm = Atmosfera(self.perf)
        self.aero = Aerodinamica(self.geo, self.perf, self.atm)
    def resume(self):
        def print_attrs(obj, nome_classe):
            print(f"\n--- {nome_classe} ---")
            for attr in dir(obj):
                if attr.startswith("_"):
                    continue
                try:
                    value = getattr(obj, attr)
                    if callable(value):
                        continue
                    if isinstance(value, (int, float)):
                        print(f"{attr:30}: {value:.3f}")
                    else:
                        print(f"{attr:30}: {value}")
                except Exception as e:
                    print(f"{attr:30}: [Erro ao acessar: {e}]")

        print_attrs(self.peso, "Peso")
        print_attrs(self.geo, "Geometria")
        print_attrs(self.perf, "Performance")
        print_attrs(self.atm, "Atmosfera")
        print_attrs(self.aero, "Aerodinamica")
        print_attrs(self.rest, "Restricoes")


