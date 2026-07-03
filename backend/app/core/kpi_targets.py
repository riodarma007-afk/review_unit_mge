# Target KPI Default (Standar industri)
KPI_TARGETS = {
    "ma": 85.0,   # Mechanical Availability (%)
    "pa": 90.0,   # Physical Availability (%)
    "ua": 80.0,   # Use of Availability (%)
    "eu": 70.0,   # Effective Utilization (%)
}

# Mapping kategori mekanikal yang mempengaruhi MA
# Di database riil, nilainya berupa string pada kolom Event.
MECHANICAL_CODES = ("Schedule Maintanance", "Unshedule Maintanance", "Schedule Maintenance", "Unscheduled Maintenance")
