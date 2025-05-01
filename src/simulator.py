# src/simulator.py

import sys
import itertools
import os
import pandas as pd
from pyomo.environ import ConcreteModel, Var, Objective, Constraint, SolverFactory, Binary, RangeSet, maximize
# Ajoute le chemin du dossier racine (le dossier parent de notebooks/)
project_path = os.path.abspath(os.path.join(os.getcwd(), ".."))
if project_path not in sys.path:
    sys.path.append(project_path)


def run_simulation(prices, battery, timestep_h=1.0):
    history = []
    
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

# First hedging strategy
def simple_threshold_strategy(price, low_threshold=25, high_threshold=80):
    """
    prix : eur/MWh
    Stratégie simple :
    - Charger si le prix < low_threshold
    - Décharger si le prix > high_threshold
    - Ne rien faire sinon
    """
    if price < low_threshold:
        return "charge"
    elif price > high_threshold:
        return "discharge"
    else:
        return "idle"
    
# Simple Optimization strategy
def optimization_based_strategy(price_series, current_time, battery, forecast_horizon=6):
    """
    Horizon glissant : chercher la meilleure séquence d'actions sur plusieurs heures.
    """
    # 1. Regarder l'horizon futur
    future_times = [current_time + pd.Timedelta(hours=i) for i in range(forecast_horizon)]
    future_prices = price_series.reindex(future_times, method='nearest')  # simple récupération

    # 2. Générer toutes les séquences d'actions possibles
    actions = ["charge", "discharge", "idle"]
    all_sequences = list(itertools.product(actions, repeat=forecast_horizon))

    best_sequence = None
    best_revenue = -float('inf')

    # 3. Tester chaque séquence
    for sequence in all_sequences:
        soc = battery.get_soc() * battery.capacity  # copie du SoC initial
        revenue = 0.0

        for i, action in enumerate(sequence):
            price = future_prices.iloc[i]

            if action == "charge" and soc < battery.capacity * battery.soc_max:
                energy = min(battery.power, (battery.capacity * battery.soc_max - soc))
                energy *= battery.efficiency
                soc += energy
                revenue -= energy * price
            elif action == "discharge" and soc > battery.capacity * battery.soc_min:
                energy = min(battery.power, (soc - battery.capacity * battery.soc_min))
                energy /= battery.efficiency
                soc -= energy
                revenue += energy * price
            # idle ne fait rien

        if revenue > best_revenue:
            best_revenue = revenue
            best_sequence = sequence

    # 4. Retourner uniquement la première action de la meilleure séquence
    return best_sequence[0]


# Linear programming optimization for larger windows

# src/pyomo_strategy.py


import pandas as pd

def pyomo_optimization_strategy(price_series, current_time, battery, forecast_horizon=6):
    """
    Optimisation horizon glissant avec Pyomo pour choisir l'action optimale (charge/décharge/idle).
    
    Inputs :
    - price_series : pandas Series avec les prix horaires
    - current_time : instant actuel
    - battery : instance de Battery (avec .capacity, .power, .efficiency, .soc_min, .soc_max)
    - forecast_horizon : nombre d'heures à optimiser
    
    Output :
    - action ("charge", "discharge", "idle")
    """

    # 1. 🔍 Sélectionner les prix pour les heures futures
    future_times = [current_time + pd.Timedelta(hours=i) for i in range(forecast_horizon)]
    future_prices = price_series.reindex(future_times, method='nearest')

    # 2. 📦 Créer un modèle Pyomo
    model = ConcreteModel()

    # 3. 📅 Définir l'ensemble des heures futures
    model.T = RangeSet(0, forecast_horizon-1)

    # 4. 🛠️ Définir les variables de décision
    # x_charge[t] = 1 si on charge à l'heure t, 0 sinon
    # x_discharge[t] = 1 si on décharge à l'heure t, 0 sinon
    model.x_charge = Var(model.T, domain=Binary)
    model.x_discharge = Var(model.T, domain=Binary)

    # 5. 🎯 Définir la fonction objectif : maximiser les gains
    def obj_rule(m):
        return sum(
            - future_prices.iloc[t] * m.x_charge[t] + future_prices.iloc[t] * m.x_discharge[t]
            for t in m.T
        )
    model.obj = Objective(rule=obj_rule, sense=maximize)

    # 6. ⚙️ Contrainte de SoC à chaque heure
    soc_init = battery.get_soc() * battery.capacity

    def soc_constraint(m, t):
        # Simulation du SoC jusqu'à l'heure t
        soc = soc_init
        for i in range(t+1):
            soc += battery.power * battery.efficiency * m.x_charge[i]
            soc -= battery.power / battery.efficiency * m.x_discharge[i]
        return (battery.capacity * battery.soc_min, soc, battery.capacity * battery.soc_max)

    model.soc_constraints = Constraint(model.T, rule=soc_constraint)

    # 7. 🔀 Contrainte : ne pas charger ET décharger en même temps
    def exclusive_action(m, t):
        return m.x_charge[t] + m.x_discharge[t] <= 1
    model.exclusive_constraints = Constraint(model.T, rule=exclusive_action)

    # 8. 🚀 Résoudre le problème
    solver = SolverFactory('glpk')  # ou 'cbc' si tu l'as
    solver.solve(model)

    # 9. 📈 Lire la première action optimale
    if model.x_charge[0]() == 1:
        return "charge"
    elif model.x_discharge[0]() == 1:
        return "discharge"
    else:
        return "idle"
