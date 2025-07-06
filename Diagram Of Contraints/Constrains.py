from DesignParameters import DesignParameters
from AuxiliaryFunctions import ConstraintPoly, PlotSetUp
import matplotlib.pyplot as plt
import numpy as np


Resolution = 2000
Start_Pa = 0.1

Airplane = DesignParameters()

print(Airplane.resume())

PropEff = 0.6

# Turn constraint (Curva nivelada)
WSlistCVT_Pa = np.linspace(Start_Pa, 8500, Resolution)
WSlistCVT_kgm2 = [x * 0.101971621 for x in WSlistCVT_Pa]
PlistCVT_kW = []
for i, WS in enumerate(WSlistCVT_Pa):
	TW = Airplane.aero.qCruise_pa * ((Airplane.aero.CDmin_ / WS) + WS * Airplane.aero.k * (Airplane.perf.nTurn_ / Airplane.aero.qCruise_pa) ** 2)
	P_kW = 9.81 * TW * Airplane.peso.maxGrossWeight_kg * Airplane.perf.CruisingSpeed_mps / PropEff / (1.132 * Airplane.atm.CruisingAltDens_kgm3 / Airplane.atm.SeaLevelDens_kgm3 - 0.132) / 1000
	PlistCVT_kW.append(P_kW)

# Climb constraint (Razão de subida)
WSlistROC_Pa = np.linspace(Start_Pa, 8500, Resolution)
WSlistROC_kgm2 = [x * 0.101971621 for x in WSlistROC_Pa]
PlistROC_kW = []
for i, WS in enumerate(WSlistROC_Pa):
	TW = (Airplane.perf.RateOfClimb_mps / Airplane.perf.ClimbSpeed_mps +
		  Airplane.aero.CDmin_ * Airplane.aero.qClimb_pa / WS +
		  Airplane.aero.k * WS / Airplane.aero.qClimb_pa)
	P_kW = 9.81 * TW * Airplane.peso.maxGrossWeight_kg * Airplane.perf.ClimbSpeed_mps / PropEff / (1.132 * Airplane.atm.ClimbAltDens_kgm3 / Airplane.atm.SeaLevelDens_kgm3 - 0.132) / 1000
	PlistROC_kW.append(P_kW)

# Takeoff constraint (Decolagem)
WSlistGR_Pa = np.linspace(Start_Pa, 8500, Resolution)
WSlistGR_kgm2 = [x * 0.101971621 for x in WSlistGR_Pa]
PlistGR_kW = []
for i, WS in enumerate(WSlistGR_Pa):
	TW = (Airplane.perf.TakeOffSpeed_mps ** 2) / (2 * 9.81 * Airplane.perf.GroundRunTakeOff_m) + \
		 Airplane.aero.qTO_pa * Airplane.perf.CDTO_ / WS + \
		 Airplane.perf.muTO_ * (1 - Airplane.aero.qTO_pa * Airplane.perf.CLTO_ / WS)
	P_kW = 9.81 * TW * Airplane.peso.maxGrossWeight_kg * Airplane.perf.TakeOffSpeed_mps / PropEff / (1.132 * Airplane.atm.TakeOffDens_kgm3 / Airplane.atm.SeaLevelDens_kgm3 - 0.132) / 1000
	PlistGR_kW.append(P_kW)

# Cruise constraint (Cruseiro)
WSlistCR_Pa = np.linspace(Start_Pa, 8500, Resolution)
WSlistCR_kgm2 = [x * 0.101971621 for x in WSlistCR_Pa]
PlistCR_kW = []
for i, WS in enumerate(WSlistCR_Pa):
	TW = Airplane.aero.qCruise_pa * Airplane.aero.CDmin_ / WS + Airplane.aero.k * WS / Airplane.aero.qCruise_pa
	P_kW = 9.81 * TW * Airplane.peso.maxGrossWeight_kg * Airplane.perf.CruisingSpeed_mps / PropEff / (1.132 * Airplane.atm.CruisingAltDens_kgm3 / Airplane.atm.SeaLevelDens_kgm3 - 0.132) / 1000
	PlistCR_kW.append(P_kW)

# Approach constraint (Velocidade de aproximação)
WS_APP_Pa = Airplane.aero.qApproach_pa * Airplane.perf.CLmaxApproach_
WS_APP_kgm2 = WS_APP_Pa * 0.101971621
WSlistAPP_kgm2 = [WS_APP_kgm2, Airplane.rest.WSmax_kgm2, Airplane.rest.WSmax_kgm2, WS_APP_kgm2, WS_APP_kgm2]
PlistAPP_kW = [0, 0, Airplane.rest.Pmax_kW, Airplane.rest.Pmax_kW, 0]

# Plotting
figCOMP = plt.figure(figsize=(10, 10))
axCOMP = figCOMP.add_subplot(111)
PlotSetUp(0, Airplane.rest.WSmax_kgm2, 0, Airplane.rest.Pmax_kW, '$W/S\\,[\\,kg/m^2]$', '$P\\,[\\,kW]$')

ConstVeloTurnPoly = ConstraintPoly(WSlistCVT_kgm2, PlistCVT_kW, 'magenta', 0.4)
axCOMP.add_patch(ConstVeloTurnPoly)
RateOfClimbPoly = ConstraintPoly(WSlistROC_kgm2, PlistROC_kW, 'blue', 0.4)
axCOMP.add_patch(RateOfClimbPoly)
TORunPoly = ConstraintPoly(WSlistGR_kgm2, PlistGR_kW, 'green', 0.4)
axCOMP.add_patch(TORunPoly)
CruisePoly = ConstraintPoly(WSlistCR_kgm2, PlistCR_kW, 'red', 0.4)
axCOMP.add_patch(CruisePoly)
AppStallPoly = ConstraintPoly(WSlistAPP_kgm2, PlistAPP_kW, 'grey', 0.4)
axCOMP.add_patch(AppStallPoly)

axCOMP.legend(['Turn', 'Climb', 'T/O run', 'Cruise', 'App Stall'])
textstr = '\n The feasible aeroplane lives in this white space'
axCOMP.text(0.05, 0.95, textstr, transform=axCOMP.transAxes, fontsize=14, verticalalignment='top')

plt.show()