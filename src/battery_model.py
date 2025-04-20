# src/battery_model.py

class Battery:
    def __init__(self, capacity_kwh, power_kw, efficiency, soc_min=0.1, soc_max=0.9):
        self.capacity = capacity_kwh        # kWh
        self.power = power_kw              # kW max charge/discharge
        self.efficiency = efficiency       # entre 0 et 1
        self.soc_min = soc_min             # SoC minimal (fraction)
        self.soc_max = soc_max             # SoC maximal (fraction)
        self.soc = soc_max * capacity_kwh  # initialisation pleine

    def charge(self, power_input_kw, duration_h):
        power_input_kw = min(power_input_kw, self.power)
        energy_in = power_input_kw * duration_h * self.efficiency
        available_capacity = self.capacity * self.soc_max - self.soc
        energy_charged = min(energy_in, available_capacity)
        self.soc += energy_charged
        return energy_charged

    def discharge(self, power_output_kw, duration_h):
        power_output_kw = min(power_output_kw, self.power)
        energy_out = power_output_kw * duration_h / self.efficiency
        energy_available = self.soc - self.capacity * self.soc_min
        energy_discharged = min(energy_out, energy_available)
        self.soc -= energy_discharged
        return energy_discharged * self.efficiency

    def get_soc(self):
        return self.soc / self.capacity
