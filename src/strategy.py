# src/strategy.py

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
