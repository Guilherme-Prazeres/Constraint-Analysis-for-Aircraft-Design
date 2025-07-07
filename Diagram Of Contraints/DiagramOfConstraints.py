import sys
import json
import inspect
import numpy as np
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QSizePolicy,
                             QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QGroupBox, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from math import sqrt

# Assuming your refactored code is in 'DesignParameters.py'
from DesignParameters import Aeronave, Config
from AuxiliaryFunctions import ConstraintPoly


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(figsize=(10, 8))
        self.ax = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

        self.airplane = None
        self.coordinate_table = None
        self.clicked_point_marker = None

        self.mpl_connect('button_press_event', self.on_click)

    def on_click(self, event):
        if event.inaxes and self.airplane:
            x_WS = event.xdata
            y_P = event.ydata
            self.update_output_table(x_WS, y_P)
            self.update_plot_marker(x_WS, y_P)


    def update_plot_marker(self, x_WS, y_P):
        if self.clicked_point_marker:
            self.clicked_point_marker.remove()

        self.clicked_point_marker, = self.ax.plot(x_WS, y_P, 'o', color='black', markersize=8, markeredgewidth=1.5, markerfacecolor='yellow', label='Ponto de Projeto')
        self.draw()

    def update_output_table(self, x_WS, y_P):
        """Calculates and updates the output table based on given W/S and P values."""
        if not self.airplane or not self.coordinate_table:
            return

        max_gross_weight_kg = self.airplane.config.peso.maxGrossWeight_kg
        AR_design = self.airplane.config.geo.AR_
        time_to_service_ceiling_sec = self.airplane.TimeToServiceCeiling_sec
        peso = self.airplane.config.peso.maxGrossWeight_kg
        rho_sl = self.airplane.SeaLevelDens_kgm3
        CL_lan = self.airplane.config.aero.CLmaxApproach_

        S_wing_m2 = max_gross_weight_kg / x_WS if x_WS != 0 else 0
        b_m = np.sqrt(AR_design * S_wing_m2) if S_wing_m2 >= 0 and AR_design >= 0 else 0
        P_hp = y_P * 1.341 if y_P != 0 else 0
        
        try:
            V_stall = sqrt((2 * peso) / (rho_sl * CL_lan * S_wing_m2)) if S_wing_m2 > 0 else 0
        except ZeroDivisionError:
            V_stall = 0

        self.coordinate_table.blockSignals(True)
        self.coordinate_table.setItem(0, 1, QTableWidgetItem(f"{x_WS:.2f}"))
        self.coordinate_table.setItem(1, 1, QTableWidgetItem(f"{y_P:.2f}"))
        self.coordinate_table.setItem(2, 1, QTableWidgetItem(f"{S_wing_m2:.2f}"))
        self.coordinate_table.setItem(3, 1, QTableWidgetItem(f"{b_m:.2f}"))
        self.coordinate_table.setItem(4, 1, QTableWidgetItem(f"{AR_design:.0f}"))
        self.coordinate_table.setItem(5, 1, QTableWidgetItem(f"{P_hp:.2f}"))
        self.coordinate_table.setItem(6, 1, QTableWidgetItem(f"{time_to_service_ceiling_sec:.0f}"))
        self.coordinate_table.setItem(7, 1, QTableWidgetItem(f"{V_stall:.2f}"))
        self.coordinate_table.blockSignals(False)

    def plot_constraints(self, airplane):
        """Receives an instance of Aeronave and plots its constraints."""
        self.airplane = airplane

        # --- Initial Parameters ---
        Resolution = 2000
        Start_Pa = 0.1
        WSmax_kgm2 = 30  # use this Value DO NOT CHANGE
        TWmax = 0.6  # use this Value DO NOT CHANGE
        Pmax_kW = 12 # use this Value DO NOT CHANGE

        WS = np.linspace(Start_Pa, 8500, Resolution)

        # --- Airplane Configuration and Calculated Values ---
        PropEff = airplane.config.perf.PropEff_
        maxGrossWeight_kg = airplane.config.peso.maxGrossWeight_kg
        SeaLevelDens_kgm3 = airplane.SeaLevelDens_kgm3
        CruisingSpeed_mps = airplane.config.perf.CruisingSpeed_mps
        CruisingAltDens_kgm3 = airplane.CruisingAltDens_kgm3
        CDmin_ = airplane.config.aero.CDmin_
        inducedDragFactor_k = airplane.inducedDragFactor_k
        loadFactorTurn_n = airplane.loadFactorTurn_n
        q_Cruise_pa = airplane.q_Cruise_pa
        RateOfClimb_mps = airplane.config.perf.RateOfClimb_mps
        ClimbSpeed_mps = airplane.ClimbSpeed_mps
        ClimbAltDens_kgm3 = airplane.ClimbAltDens_kgm3
        q_Climb_pa = airplane.q_Climb_pa
        TakeOffSpeed_mps = airplane.config.perf.TakeOffSpeed_mps
        GroundRunTakeOff_m = airplane.config.perf.GroundRunTakeOff_m
        CDTO_ = airplane.config.aero.CDTO_
        muTO_ = airplane.config.perf.muTO_
        CLTO_ = airplane.config.aero.CLTO_
        TakeOffDens_kgm3 = airplane.TakeOffDens_kgm3
        q_TakeOff_pa = airplane.q_TakeOff_pa
        CLmaxApproach_ = airplane.config.aero.CLmaxApproach_
        q_Approach_pa = airplane.q_Approach_pa


        # --- Helper Functions ---
        def kW_from_TW(TW, V, rho_alt, rho_sl):
            return 9.81 * TW * maxGrossWeight_kg * V / PropEff / ((1.132 * rho_alt / rho_sl) - 0.132) / 1000

        def compute_curve(WSlist_Pa, TW_expr, Speed, rho):
            WSlist_kgm2 = [x * 0.101971621 for x in WSlist_Pa]
            Plist_kW = [kW_from_TW(TW_expr(ws), Speed, rho, SeaLevelDens_kgm3) for ws in WSlist_Pa]
            return WSlist_kgm2, Plist_kW

        # --- Constraint Curves Calculation ---
        def TW_turn(ws):
            return (q_Cruise_pa * ((CDmin_ / ws) + ws * inducedDragFactor_k * (loadFactorTurn_n / q_Cruise_pa) ** 2))
        WS_CVT, P_CVT = compute_curve(WS, TW_turn, CruisingSpeed_mps, CruisingAltDens_kgm3)

        def TW_climb(ws):
            return (RateOfClimb_mps / ClimbSpeed_mps + (CDmin_ * q_Climb_pa + inducedDragFactor_k * ws) / ws)
        WS_ROC, P_ROC = compute_curve(WS, TW_climb, ClimbSpeed_mps, ClimbAltDens_kgm3)

        def TW_to(ws):
            return ((TakeOffSpeed_mps ** 2) / (2 * 9.81 * GroundRunTakeOff_m) + q_TakeOff_pa * CDTO_ / ws + muTO_ * (1 - q_TakeOff_pa * CLTO_ / ws))
        WS_GR, P_GR = compute_curve(WS, TW_to, TakeOffSpeed_mps, TakeOffDens_kgm3)

        def TW_cruise(ws):
            return q_Cruise_pa * CDmin_ / ws + inducedDragFactor_k * ws / q_Cruise_pa
        WS_CR, P_CR = compute_curve(WS, TW_cruise, CruisingSpeed_mps, CruisingAltDens_kgm3)

        WS_APP_Pa = q_Approach_pa * CLmaxApproach_
        WS_APP_kgm2 = WS_APP_Pa * 0.101971621
        WS_APP = [WS_APP_kgm2, WSmax_kgm2, WSmax_kgm2, WS_APP_kgm2, WS_APP_kgm2]
        P_APP = [0, 0, Pmax_kW, Pmax_kW, 0]

        self.ax.clear()
        self.clicked_point_marker = None

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

        self.ax.set_xlim(0, WSmax_kgm2)
        self.ax.set_ylim(0, Pmax_kW)
        xtick = np.arange(0, WSmax_kgm2, 2)
        self.ax.set_xticks(xtick)
        ytick = np.arange(0, Pmax_kW, 1)
        self.ax.set_yticks(ytick)
        self.ax.set_xlabel('$W/S\\,[\\,kg/m^2]$')
        self.ax.set_ylabel('$P\\,[\\,kW]$')
        self.ax.legend([line_turn, line_climb, line_to, line_cruise, line_app], ['Turn', 'Climb', 'T/O run', 'Cruise', 'App Stall'])
        self.ax.text(0.18, 0.95, 'Aeronave possível está dentro da área branca', transform=self.ax.transAxes, fontsize=12, verticalalignment='top')
        self.ax.grid(True, color="#000000", linestyle='-', linewidth=0.5, alpha=0.3)
        self.draw()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aircraft Design Viewer")
        self.resize(1600, 700)
        main_layout = QHBoxLayout(self)

        self.config = Config()
        self.airplane = Aeronave(self.config)

        # --- Left Layout (Controls) ---
        left_layout = QVBoxLayout()

        # Parameters Table
        param_group_box = QGroupBox("Design Parameters")
        param_table_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.table.itemChanged.connect(self.update_airplane_param_from_table)
        self.table.setColumnWidth(0, 400)
        self.table.setColumnWidth(1, 110)
        param_table_layout.addWidget(self.table)
        param_group_box.setLayout(param_table_layout)
        left_layout.addWidget(param_group_box)

        self.attr_table_map = {}
        self.load_editable_attrs()

        self.update_btn = QPushButton("Update Plot")
        self.update_btn.clicked.connect(self.update_plot)
        left_layout.addWidget(self.update_btn)

        # Clicked Point Table
        clicked_point_group_box = QGroupBox("Project Point Data")
        clicked_point_table_layout = QVBoxLayout()
        self.clicked_point_table = QTableWidget()
        self.clicked_point_table.setRowCount(8)
        self.clicked_point_table.setColumnCount(2)
        self.clicked_point_table.setHorizontalHeaderLabels(["Output", "Value"])

        headers = ["W/S [kg/m²]", "P [kW]", "S_wing [m²]", "Wingspan [m]", "AR", "P [HP]", "Time to Service Ceiling [s]", "Approach Velocity [m/s]"]
        for i, header in enumerate(headers):
            item = QTableWidgetItem(header)
            # Make W/S and P editable
            if i in [0, 1]:  # W/S is row 0, P is row 1
                item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
            else:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.clicked_point_table.setItem(i, 0, item)
            self.clicked_point_table.setItem(i, 1, QTableWidgetItem(""))

        self.clicked_point_table.setColumnWidth(0, 400)
        self.clicked_point_table.setColumnWidth(1, 110)
        # Connect itemChanged signal for the clicked_point_table
        self.clicked_point_table.itemChanged.connect(self.update_plot_from_output_table)
        
        clicked_point_table_layout.addWidget(self.clicked_point_table)
        clicked_point_group_box.setLayout(clicked_point_table_layout)
        left_layout.addWidget(clicked_point_group_box)

        self.save_btn = QPushButton("Save Data to JSON")
        self.save_btn.clicked.connect(self.save_data_to_json)
        left_layout.addWidget(self.save_btn)

        main_layout.addLayout(left_layout)

        # --- Right Layout (Plot) ---
        self.canvas = PlotCanvas(self)
        self.canvas.coordinate_table = self.clicked_point_table
        self.canvas.plot_constraints(self.airplane)
        main_layout.addWidget(self.canvas)

    def load_editable_attrs(self):
        """Loads editable attributes from the self.config object."""
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        self.attr_table_map = {}
        row = 0

        def add_attrs(config_obj, prefix=""):
            nonlocal row
            for attr_name in config_obj.__dataclass_fields__:
                value = getattr(config_obj, attr_name)

                self.table.insertRow(row)
                key_item = QTableWidgetItem(f"{attr_name}")
                key_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.table.setItem(row, 0, key_item)

                val_item = QTableWidgetItem(str(value))
                self.table.setItem(row, 1, val_item)

                self.attr_table_map[row] = (config_obj, attr_name)
                row += 1

        for config_name in self.config.__dataclass_fields__:
            config_instance = getattr(self.config, config_name)
            add_attrs(config_instance, prefix=f"{config_name}.")

        self.table.blockSignals(False)

    def update_airplane_param_from_table(self, item):
        """Updates the corresponding parameter in the self.config object."""
        if item.column() != 1:
            return

        row = item.row()
        if row in self.attr_table_map:
            config_obj, attr = self.attr_table_map[row]
            new_value_str = item.text()
            old_value = getattr(config_obj, attr)

            try:
                new_value = type(old_value)(new_value_str)
                setattr(config_obj, attr, new_value)
                print(f"Updated: {attr} = {new_value}")
            except (ValueError, TypeError) as e:
                print(f"Error updating '{attr}': {e}. Reverting.")
                item.setText(str(old_value))

    def update_plot_from_output_table(self, item):
        """Updates the plot and recalculates other outputs when W/S or P in the output table is changed."""
        if item.column() != 1:
            return

        row = item.row()
        if row not in [0, 1]:  # Only react to changes in W/S (row 0) or P (row 1)
            return

        self.clicked_point_table.blockSignals(True) # Temporarily block signals to prevent recursive calls

        try:
            ws_item = self.clicked_point_table.item(0, 1)
            p_item = self.clicked_point_table.item(1, 1)

            x_WS = float(ws_item.text()) if ws_item and ws_item.text() else 0.0
            y_P = float(p_item.text()) if p_item and p_item.text() else 0.0

            # Update the plot marker
            self.canvas.update_plot_marker(x_WS, y_P)
            # Recalculate and update the other output fields
            self.canvas.update_output_table(x_WS, y_P)

        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Please enter a valid number for W/S or P. Error: {e}")
            # Revert to previous value or clear if invalid
            ws_item = self.clicked_point_table.item(0, 1)
            p_item = self.clicked_point_table.item(1, 1)
            
            # This part needs careful handling, ideally store previous valid values
            # For simplicity, we'll just print a warning.
            print(f"Invalid input in output table: {e}")
        finally:
            self.clicked_point_table.blockSignals(False)


    def update_plot(self):
        """Recalculates and redraws the constraints on the canvas."""
        print("Updating plot with new parameters...")
        self.canvas.plot_constraints(self.airplane)
        # After updating the plot, clear the selected point data or recalculate if there was a previous selection
        # For now, let's clear it, user can click to re-select.
        self.canvas.update_output_table(0, 0) # Clear or reset the output table


    def save_data_to_json(self):
        """Gathers all data and saves it to a user-specified JSON file."""
        print("Gathering data for JSON export...")

        # 1. Gather Input Parameters from self.config
        input_params = {}
        for config_name in self.config.__dataclass_fields__:
            config_instance = getattr(self.config, config_name)
            input_params[config_name] = {
                attr: getattr(config_instance, attr)
                for attr in config_instance.__dataclass_fields__
            }

        # 2. Gather Calculated Properties from self.airplane
        calculated_props = {}
        # Use inspect to get properties, avoiding methods and private attributes
        for name, value in inspect.getmembers(self.airplane):
            if not name.startswith('_') and not inspect.ismethod(value) and name != 'config':
                # Ensure the value is JSON-serializable
                if isinstance(value, (int, float, str, bool, list, dict)) or value is None:
                    calculated_props[name] = value
                else:
                    # For other types like numpy arrays, convert them to string
                    calculated_props[name] = str(value)


        # 3. Gather Selected Point Data
        selected_point_data = {}
        for i in range(self.clicked_point_table.rowCount()):
            key_item = self.clicked_point_table.item(i, 0)
            val_item = self.clicked_point_table.item(i, 1)
            if key_item and val_item:
                key = key_item.text()
                value = val_item.text()
                selected_point_data[key] = value

        # 4. Consolidate all data
        all_data = {
            "input_parameters": input_params,
            "calculated_properties": calculated_props,
            "selected_design_point": selected_point_data
        }

        # 5. Open File Dialog and Save
        filePath, _ = QFileDialog.getSaveFileName(self, "Save Data File", "", "JSON Files (*.json);;All Files (*)")

        if filePath:
            try:
                with open(filePath, 'w') as f:
                    json.dump(all_data, f, indent=4)

                QMessageBox.information(self, "Success", f"Data successfully saved to:\n{filePath}")
                print(f"Data saved to {filePath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file.\nError: {e}")
                print(f"Error saving file: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())