import sys
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QSizePolicy, QTreeWidgetItem, QVBoxLayout, QTableWidget, QTableWidgetItem
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton

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
        PropEff = Airplane.perf.PropEff

        # Curvas
        def kW_from_TW(TW, V, rho_alt, rho_sl):
            return 9.81 * TW * Airplane.peso.maxGrossWeight_kg * V / PropEff / (1.132 * rho_alt / rho_sl - 0.132) / 1000

        def compute_curve(WSlist_Pa, TW_expr, Speed, rho):
            WSlist_kgm2 = [x * 0.101971621 for x in WSlist_Pa]
            Plist_kW = [kW_from_TW(TW_expr(ws), Speed, rho, Airplane.atm.SeaLevelDens_kgm3)
                        for ws in WSlist_Pa]
            return WSlist_kgm2, Plist_kW

        WS = np.linspace(Start_Pa, 8500, Resolution)

        def TW_turn(ws):
            return (Airplane.aero.qCruise_pa * ((Airplane.aero.CDmin_ / ws)
                    + ws * Airplane.aero.k * (Airplane.perf.nTurn_ / Airplane.aero.qCruise_pa) ** 2))
        WS_CVT, P_CVT = compute_curve(WS, TW_turn, Airplane.perf.CruisingSpeed_mps, Airplane.atm.CruisingAltDens_kgm3)

        # Climb
        def TW_climb(ws):
            return (Airplane.perf.RateOfClimb_mps / Airplane.perf.ClimbSpeed_mps +
                    (Airplane.aero.CDmin_ * Airplane.aero.qClimb_pa + Airplane.aero.k * ws) / ws)
        WS_ROC, P_ROC = compute_curve(WS, TW_climb, Airplane.perf.ClimbSpeed_mps, Airplane.atm.ClimbAltDens_kgm3)

        # Takeoff
        def TW_to(ws):
            return ((Airplane.perf.TakeOffSpeed_mps ** 2) / (2 * 9.81 * Airplane.perf.GroundRunTakeOff_m) +
                    Airplane.aero.qTO_pa * Airplane.perf.CDTO_ / ws +
                    Airplane.perf.muTO_ * (1 - Airplane.aero.qTO_pa * Airplane.perf.CLTO_ / ws))
        WS_GR, P_GR = compute_curve(WS, TW_to, Airplane.perf.TakeOffSpeed_mps, Airplane.atm.TakeOffDens_kgm3)

        # Cruise
        def TW_cruise(ws):
            return Airplane.aero.qCruise_pa * Airplane.aero.CDmin_ / ws + Airplane.aero.k * ws / Airplane.aero.qCruise_pa
        WS_CR, P_CR = compute_curve(WS, TW_cruise, Airplane.perf.CruisingSpeed_mps, Airplane.atm.CruisingAltDens_kgm3)

        # Approach (reta fechando o envelope)
        WS_APP_Pa = Airplane.aero.qApproach_pa * Airplane.perf.CLmaxApproach_
        WS_APP_kgm2 = WS_APP_Pa * 0.101971621
        WS_APP = [WS_APP_kgm2, Airplane.rest.WSmax_kgm2, Airplane.rest.WSmax_kgm2, WS_APP_kgm2, WS_APP_kgm2]
        P_APP = [0, 0, Airplane.rest.Pmax_kW, Airplane.rest.Pmax_kW, 0]

        # Limpar o eixo antes de plotar
        self.ax.clear()

        # Adiciona patches e curvas com legendas associadas
        line_turn, = self.ax.plot(WS_CVT, P_CVT, linestyle='--', color='magenta')
        self.ax.add_patch(ConstraintPoly(WS_CVT, P_CVT, 'magenta', 0.4))

        line_climb, = self.ax.plot(WS_ROC, P_ROC, linestyle='--', color='blue')
        self.ax.add_patch(ConstraintPoly(WS_ROC, P_ROC, 'blue', 0.4))

        line_to, = self.ax.plot(WS_GR, P_GR, linestyle='--', color='green')
        self.ax.add_patch(ConstraintPoly(WS_GR, P_GR, 'green', 0.4))

        line_cruise, = self.ax.plot(WS_CR, P_CR, linestyle='--', color='red')
        self.ax.add_patch(ConstraintPoly(WS_CR, P_CR, 'red', 0.4))

        line_app, = self.ax.plot(WS_APP, P_APP, linestyle='--', color='grey')
        self.ax.add_patch(ConstraintPoly(WS_APP, P_APP, 'grey', 0.4))

        # Limites dos eixos
        self.ax.set_xlim(0, Airplane.rest.WSmax_kgm2)
        self.ax.set_ylim(0, Airplane.rest.Pmax_kW)

        # Rótulos dos eixos
        self.ax.set_xlabel('$W/S\\,[\\,kg/m^2]$')
        self.ax.set_ylabel('$P\\,[\\,kW]$')

        # Legenda com linhas associadas corretamente
        self.ax.legend(
            [line_turn, line_climb, line_to, line_cruise, line_app],
            ['Turn', 'Climb', 'T/O run', 'Cruise', 'App Stall']
        )

        # Texto explicativo
        self.ax.text(
            0.05, 0.95,
            'The feasible aeroplane lives in this white space',
            transform=self.ax.transAxes,
            fontsize=12,
            verticalalignment='top'
        )


        self.draw()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Design Viewer")
        self.resize(1200, 700)

        # Layout principal
        main_layout = QHBoxLayout(self)

        self.airplane = DesignParameters()

        left_layout = QVBoxLayout()

        # Tabela de parâmetros editáveis
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parâmetro", "Valor"])
        self.table.setMinimumWidth(200)
        self.table.setMaximumWidth(400)
        self.table.itemChanged.connect(self.update_airplane_param_table)

        # Define larguras das colunas
        self.table.setColumnWidth(0, 250)
        self.table.setColumnWidth(1, 100)

        self.attr_table_map = {}  # Mapeia linha -> (obj, attr)
        self.load_editable_attrs()

        left_layout.addWidget(self.table)

        # Botão para atualizar o gráfico
        self.update_btn = QPushButton("Atualizar Gráfico")
        self.update_btn.clicked.connect(self.update_plot)
        left_layout.addWidget(self.update_btn)

        # Adiciona o painel esquerdo ao layout principal
        main_layout.addLayout(left_layout)

        # Canvas com o gráfico à direita
        self.canvas = PlotCanvas(self.airplane)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.canvas)


    def load_editable_attrs(self):
        row = 0

        def add_attrs(obj, prefix=""):
            nonlocal row
            for attr in dir(obj):
                if attr.startswith('_'):
                    continue
                if isinstance(getattr(type(obj), attr, None), property):
                    continue  # Ignora @property

                try:
                    value = getattr(obj, attr)
                except Exception:
                    continue  # Ignora atributos que disparam exceção ao acessar

                if callable(value):
                    continue  # Ignora métodos

                # Ignora tipos não primitivos
                if not isinstance(value, (int, float, str, bool)):
                    continue

                self.table.insertRow(row)

                key_item = QTableWidgetItem(f"{prefix}{attr}")
                key_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, 0, key_item)

                val_item = QTableWidgetItem(str(value))
                val_item.setFlags(val_item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, val_item)

                self.attr_table_map[row] = (obj, attr)
                row += 1

        # Somente os subobjetos desejados
        for sub in ["peso", "aero", "perf", "atm", "rest"]:
            add_attrs(getattr(self.airplane, sub), prefix=sub + ".")

    def update_airplane_param_table(self, item):
        if item.column() != 1:
            return

        row = item.row()
        if row in self.attr_table_map:
            obj, attr = self.attr_table_map[row]
            new_value_str = item.text()
            old_value = getattr(obj, attr)

            try:
                if isinstance(old_value, bool):
                    new_value = new_value_str.lower() in ['1', 'true', 'yes']
                elif isinstance(old_value, int):
                    new_value = int(new_value_str)
                elif isinstance(old_value, float):
                    new_value = float(new_value_str)
                else:
                    new_value = new_value_str
                setattr(obj, attr, new_value)
                print(f"Atualizado: {attr} = {new_value}")
            except Exception as e:
                print(f"Erro ao atualizar '{attr}': {e}")


    def update_plot(self):
        # Remove canvas antigo do layout e do widget
        self.layout().removeWidget(self.canvas)
        self.canvas.setParent(None)
        self.canvas.deleteLater()

        # Cria novo canvas com dados atualizados
        self.canvas = PlotCanvas(self.airplane)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Adiciona de novo ao layout
        self.layout().addWidget(self.canvas)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
