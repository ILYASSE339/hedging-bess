# src/simulator.py

import sys
import os
import pandas as pd
# Ajoute le chemin du dossier racine (le dossier parent de notebooks/)
project_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
if project_path not in sys.path:
    sys.path.append(project_path)


def run_simulation(prices, battery, timestep_h=1.0):
    history = []
    from strategy import simple_threshold_strategy
    for timestamp, price in prices.items():
        action = simple_threshold_strategy(price)
        soc_before = battery.get_soc()
        energy = 0.0
        revenue = 0.0

        if action == "charge":
            energy = battery.charge(battery.power, timestep_h)
            revenue = -energy * price  # on paie l'électricité
        elif action == "discharge":
            energy = battery.discharge(battery.power, timestep_h)
            revenue = energy * price   # on vend l'électricité

        soc_after = battery.get_soc()

        history.append({
            "time": timestamp,
            "price": price,
            "action": action,
            "soc_before": soc_before,
            "soc_after": soc_after,
            "energy": energy,
            "revenue": revenue
        })

    return pd.DataFrame(history)
