import sys
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QTextEdit, QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from DesignParameters import DesignParameters
from AuxiliaryFunctions import ConstraintPoly, PlotSetUp
import numpy as np

class PlotCanvas(FigureCanvas):
    def __init__(self, airplane, parent=None):
        fig = Figure(figsize=(6, 6))
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)
        self.plot_constraints(airplane)

    def plot_constraints(self, Airplane):
        Resolution = 2000
        Start_Pa = 0.1
        PropEff = 0.6

        # Curvas
        def kW_from_TW(TW, V, rho_alt, rho_sl):
            return 9.81 * TW * Airplane.peso.maxGrossWeight_kg * V / PropEff / (1.132 * rho_alt / rho_sl - 0.132) / 1000

        def compute_curve(WSlist_Pa, TW_expr):
            WSlist_kgm2 = [x * 0.101971621 for x in WSlist_Pa]
            Plist_kW = [kW_from_TW(TW_expr(ws), Airplane.perf.CruisingSpeed_mps, Airplane.atm.CruisingAltDens_kgm3, Airplane.atm.SeaLevelDens_kgm3)
                        for ws in WSlist_Pa]
            return WSlist_kgm2, Plist_kW

        WS = np.linspace(Start_Pa, 8500, Resolution)

        # Turn
        TW_turn = lambda ws: Airplane.aero.qCruise_pa * ((Airplane.aero.CDmin_ / ws) + ws * Airplane.aero.k * (Airplane.perf.nTurn_ / Airplane.aero.qCruise_pa) ** 2)
        WS_CVT, P_CVT = compute_curve(WS, TW_turn)

        # Climb
        def TW_climb(ws):
            return (Airplane.perf.RateOfClimb_mps / Airplane.perf.ClimbSpeed_mps +
                    Airplane.aero.CDmin_ * Airplane.aero.qClimb_pa / ws +
                    Airplane.aero.k * ws / Airplane.aero.qClimb_pa)
        WS_ROC, P_ROC = compute_curve(WS, TW_climb)

        # Takeoff
        def TW_to(ws):
            return ((Airplane.perf.TakeOffSpeed_mps ** 2) / (2 * 9.81 * Airplane.perf.GroundRunTakeOff_m) +
                    Airplane.aero.qTO_pa * Airplane.perf.CDTO_ / ws +
                    Airplane.perf.muTO_ * (1 - Airplane.aero.qTO_pa * Airplane.perf.CLTO_ / ws))
        WS_GR, P_GR = compute_curve(WS, TW_to)

        # Cruise
        def TW_cruise(ws):
            return Airplane.aero.qCruise_pa * Airplane.aero.CDmin_ / ws + Airplane.aero.k * ws / Airplane.aero.qCruise_pa
        WS_CR, P_CR = compute_curve(WS, TW_cruise)

        # Approach (reta fechando o envelope)
        WS_APP_Pa = Airplane.aero.qApproach_pa * Airplane.perf.CLmaxApproach_
        WS_APP_kgm2 = WS_APP_Pa * 0.101971621
        WS_APP = [WS_APP_kgm2, Airplane.rest.WSmax_kgm2, Airplane.rest.WSmax_kgm2, WS_APP_kgm2, WS_APP_kgm2]
        P_APP = [0, 0, Airplane.rest.Pmax_kW, Airplane.rest.Pmax_kW, 0]

        # Plot setup
        PlotSetUp(0, Airplane.rest.WSmax_kgm2, 0, Airplane.rest.Pmax_kW, '$W/S\\,[\\,kg/m^2]$', '$P\\,[\\,kW]$', ax=self.ax)
        self.ax.add_patch(ConstraintPoly(WS_CVT, P_CVT, 'magenta', 0.4))
        self.ax.add_patch(ConstraintPoly(WS_ROC, P_ROC, 'blue', 0.4))
        self.ax.add_patch(ConstraintPoly(WS_GR, P_GR, 'green', 0.4))
        self.ax.add_patch(ConstraintPoly(WS_CR, P_CR, 'red', 0.4))
        self.ax.add_patch(ConstraintPoly(WS_APP, P_APP, 'grey', 0.4))

        self.ax.legend(['Turn', 'Climb', 'T/O run', 'Cruise', 'App Stall'])
        self.ax.text(0.05, 0.95, 'The feasible aeroplane lives in this white space',
                     transform=self.ax.transAxes, fontsize=12, verticalalignment='top')

        self.draw()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Design Viewer")
        self.resize(1200, 700)

        layout = QHBoxLayout(self)

        self.airplane = DesignParameters()

        self.text = QTextEdit()
        self.text.setText(self.airplane.resume())
        self.text.setReadOnly(True)
        self.text.setMinimumWidth(400)

        self.canvas = PlotCanvas(self.airplane)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout.addWidget(self.text)
        layout.addWidget(self.canvas)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
