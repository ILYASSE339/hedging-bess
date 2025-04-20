import sys
import os

# Ajouter le chemin de la racine du projet au PYTHONPATH
sys.path.append(os.path.abspath(".."))

from src.battery_model import Battery

batt = Battery(capacity_kwh=100, power_kw=50, efficiency=0.9)
print("SoC initial :", batt.get_soc())

batt.charge(30, 1)  # charge 30 kW pendant 1h
print("SoC après charge :", batt.get_soc())

batt.discharge(40, 1)
print("SoC après décharge :", batt.get_soc())
