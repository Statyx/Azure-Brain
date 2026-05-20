# Sample Data Generation — Python Scripts for Demo Data

## Philosophy

Demo data must be:
- **Realistic** — proper distributions, not random noise
- **Consistent** — IDs match across tables, FKs are valid
- **Deterministic** — same seed produces same data (reproducible demos)
- **Scalable** — easy to adjust row counts

---

## Universal Data Generator Framework

```python
"""
Universal Fabric Demo Data Generator
Generates consistent dimension + fact CSV files for any domain model.
"""
import csv
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import math
import uuid

class DemoDataGenerator:
    """Base class for generating consistent demo data."""
    
    def __init__(self, seed: int = 42, output_dir: str = "data/raw"):
        self.seed = seed
        self.output_dir = output_dir
        random.seed(seed)
        os.makedirs(output_dir, exist_ok=True)
        self._dimension_cache = {}  # Cache dimension IDs for FK consistency
    
    def write_csv(self, filename: str, rows: List[Dict[str, Any]]):
        """Write rows to CSV file (BOM-free UTF-8)."""
        if not rows:
            return
        filepath = os.path.join(self.output_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"✅ {filepath}: {len(rows)} rows")
    
    def register_dimension(self, name: str, ids: List[str]):
        """Cache dimension IDs for FK consistency."""
        self._dimension_cache[name] = ids
    
    def get_random_fk(self, dimension_name: str) -> str:
        """Get a random FK from a registered dimension."""
        return random.choice(self._dimension_cache[dimension_name])
    
    def random_date(self, start: str, end: str) -> str:
        """Generate random date between start and end (YYYY-MM-DD)."""
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        delta = (e - s).days
        return (s + timedelta(days=random.randint(0, delta))).strftime("%Y-%m-%d")
    
    def random_datetime(self, start: str, end: str) -> str:
        """Generate random datetime (ISO 8601)."""
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        delta = int((e - s).total_seconds())
        return (s + timedelta(seconds=random.randint(0, delta))).strftime("%Y-%m-%dT%H:%M:%SZ")
```

---

## Manufacturing / IoT Data Generator

```python
class ManufacturingDataGenerator(DemoDataGenerator):
    """Generate manufacturing/IoT demo data."""
    
    def generate_all(self, n_sites=3, n_zones_per_site=4, n_equipment_per_zone=3, 
                     n_sensors_per_equipment=3, n_readings=5000, n_alerts=100):
        """Generate complete manufacturing dataset."""
        sites = self.generate_sites(n_sites)
        zones = self.generate_zones(sites, n_zones_per_site)
        equipment = self.generate_equipment(zones, n_equipment_per_zone)
        sensors = self.generate_sensors(equipment, n_sensors_per_equipment)
        self.generate_sensor_readings(sensors, n_readings)
        self.generate_alerts(sensors, n_alerts)
        return self
    
    def generate_sites(self, n: int):
        site_names = ["Paris Factory", "Lyon Plant", "Toulouse Hub", "Marseille Works", "Bordeaux Mill"]
        rows = []
        ids = []
        for i in range(n):
            site_id = f"SITE-{i+1:03d}"
            ids.append(site_id)
            rows.append({
                "site_id": site_id,
                "site_name": site_names[i % len(site_names)],
                "address": f"{random.randint(1,200)} Rue de l'Industrie",
                "latitude": round(43.0 + random.random() * 5, 6),
                "longitude": round(1.0 + random.random() * 4, 6),
                "timezone": "Europe/Paris"
            })
        self.register_dimension("sites", ids)
        self.write_csv("dim_sites.csv", rows)
        return rows
    
    def generate_zones(self, sites, n_per_site: int):
        zone_types = ["Production", "Assembly", "Storage", "Quality Control", "Shipping"]
        rows = []
        ids = []
        for site in sites:
            for j in range(n_per_site):
                zone_id = f"ZONE-{site['site_id'][-3:]}-{j+1:02d}"
                ids.append(zone_id)
                rows.append({
                    "zone_id": zone_id,
                    "zone_name": f"{zone_types[j % len(zone_types)]} {j+1}",
                    "site_id": site["site_id"],
                    "zone_type": zone_types[j % len(zone_types)]
                })
        self.register_dimension("zones", ids)
        self.write_csv("dim_zones.csv", rows)
        return rows
    
    def generate_equipment(self, zones, n_per_zone: int):
        equipment_types = ["CNC Machine", "Robot Arm", "Conveyor", "Press", "Furnace", "Mixer"]
        rows = []
        ids = []
        for zone in zones:
            for k in range(n_per_zone):
                equip_id = f"EQ-{zone['zone_id'][-5:]}-{k+1:02d}"
                ids.append(equip_id)
                rows.append({
                    "equipment_id": equip_id,
                    "equipment_name": f"{equipment_types[k % len(equipment_types)]} #{k+1}",
                    "zone_id": zone["zone_id"],
                    "site_id": zone["site_id"],
                    "equipment_type": equipment_types[k % len(equipment_types)],
                    "manufacturer": random.choice(["Siemens", "ABB", "Fanuc", "Bosch", "Schneider"]),
                    "install_date": self.random_date("2020-01-01", "2024-01-01")
                })
        self.register_dimension("equipment", ids)
        self.write_csv("dim_equipment.csv", rows)
        return rows
    
    def generate_sensors(self, equipment, n_per_equipment: int):
        sensor_configs = [
            {"type": "Temperature", "unit": "°C", "min": 15, "max": 85, "baseline": 45, "std": 5},
            {"type": "Pressure", "unit": "bar", "min": 0.5, "max": 10, "baseline": 5, "std": 0.5},
            {"type": "Vibration", "unit": "mm/s", "min": 0, "max": 25, "baseline": 3, "std": 1},
            {"type": "Humidity", "unit": "%", "min": 20, "max": 90, "baseline": 55, "std": 8},
            {"type": "Power", "unit": "kW", "min": 0, "max": 500, "baseline": 150, "std": 20}
        ]
        rows = []
        ids = []
        sensor_meta = {}
        for equip in equipment:
            for s in range(n_per_equipment):
                config = sensor_configs[s % len(sensor_configs)]
                sensor_id = f"SENS-{equip['equipment_id'][-7:]}-{config['type'][:3].upper()}"
                ids.append(sensor_id)
                sensor_meta[sensor_id] = {
                    "equipment_id": equip["equipment_id"],
                    "zone_id": equip["zone_id"],
                    "site_id": equip["site_id"],
                    **config
                }
                rows.append({
                    "sensor_id": sensor_id,
                    "sensor_name": f"{config['type']} Sensor",
                    "equipment_id": equip["equipment_id"],
                    "sensor_type": config["type"],
                    "unit": config["unit"],
                    "min_threshold": config["min"],
                    "max_threshold": config["max"]
                })
        self.register_dimension("sensors", ids)
        self._sensor_meta = sensor_meta
        self.write_csv("dim_sensors.csv", rows)
        return rows
    
    def generate_sensor_readings(self, sensors, n_total: int):
        """Generate realistic sensor readings with trends and anomalies."""
        rows = []
        base_time = datetime(2024, 11, 1, 0, 0, 0)
        sensor_ids = list(self._sensor_meta.keys())
        
        for i in range(n_total):
            sensor_id = sensor_ids[i % len(sensor_ids)]
            meta = self._sensor_meta[sensor_id]
            
            # Time progression
            timestamp = base_time + timedelta(seconds=i * 5)
            
            # Realistic value: baseline + sine wave (daily cycle) + noise
            hour_angle = (timestamp.hour / 24) * 2 * math.pi
            daily_cycle = math.sin(hour_angle) * meta["std"]
            noise = random.gauss(0, meta["std"] * 0.3)
            value = meta["baseline"] + daily_cycle + noise
            
            # Occasional anomaly (2% chance)
            if random.random() < 0.02:
                value = meta["baseline"] + random.choice([-1, 1]) * meta["std"] * 4
            
            value = round(max(meta["min"], min(meta["max"], value)), 2)
            
            rows.append({
                "sensor_id": sensor_id,
                "equipment_id": meta["equipment_id"],
                "zone_id": meta["zone_id"],
                "site_id": meta["site_id"],
                "value": value,
                "unit": meta["unit"],
                "quality": "Good" if meta["min"] <= value <= meta["max"] else "Bad",
                "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
            })
        
        self.write_csv("fact_sensor_readings.csv", rows)
    
    def generate_alerts(self, sensors, n_alerts: int):
        """Generate equipment alert events."""
        alert_types = ["HighTemperature", "LowPressure", "ExcessiveVibration", "PowerSurge", "SensorFault"]
        rows = []
        for i in range(n_alerts):
            sensor_id = random.choice(list(self._sensor_meta.keys()))
            meta = self._sensor_meta[sensor_id]
            rows.append({
                "alert_id": f"ALT-{i+1:06d}",
                "sensor_id": sensor_id,
                "equipment_id": meta["equipment_id"],
                "alert_type": random.choice(alert_types),
                "severity": random.choices([1, 2, 3, 4, 5], weights=[10, 25, 35, 20, 10])[0],
                "message": f"Alert on {sensor_id}: threshold exceeded",
                "timestamp": self.random_datetime("2024-11-01", "2024-12-01")
            })
        self.write_csv("fact_alerts.csv", rows)


# Quick usage
if __name__ == "__main__":
    gen = ManufacturingDataGenerator(seed=42, output_dir="data/raw")
    gen.generate_all(n_sites=3, n_zones_per_site=4, n_equipment_per_zone=3,
                     n_sensors_per_equipment=3, n_readings=10000, n_alerts=200)
```

---

## Retail Data Generator

```python
class RetailDataGenerator(DemoDataGenerator):
    """Generate retail/e-commerce demo data."""
    
    def generate_all(self, n_customers=500, n_products=100, n_stores=10, n_sales=5000):
        self.generate_customers(n_customers)
        self.generate_products(n_products)
        self.generate_stores(n_stores)
        self.generate_dates("2023-01-01", "2025-12-31")
        self.generate_sales(n_sales)
        return self
    
    def generate_customers(self, n: int):
        segments = ["VIP", "Regular", "New", "At-Risk"]
        regions = ["North", "South", "East", "West", "Central"]
        rows = []
        ids = []
        for i in range(n):
            cid = f"CUST-{i+1:05d}"
            ids.append(cid)
            rows.append({
                "customer_id": cid,
                "customer_name": f"Customer {i+1}",
                "email": f"customer{i+1}@example.com",
                "segment": random.choices(segments, weights=[10, 50, 25, 15])[0],
                "region": random.choice(regions),
                "loyalty_tier": random.choice(["Gold", "Silver", "Bronze", "None"]),
                "created_date": self.random_date("2020-01-01", "2024-06-01")
            })
        self.register_dimension("customers", ids)
        self.write_csv("dim_customers.csv", rows)
    
    def generate_products(self, n: int):
        categories = {
            "Electronics": ["Laptop", "Phone", "Tablet", "Headphones", "Camera"],
            "Clothing": ["Shirt", "Pants", "Jacket", "Shoes", "Hat"],
            "Home": ["Chair", "Table", "Lamp", "Rug", "Curtain"],
            "Food": ["Coffee", "Tea", "Chocolate", "Cheese", "Wine"]
        }
        rows = []
        ids = []
        for i in range(n):
            cat = random.choice(list(categories.keys()))
            subcat = random.choice(categories[cat])
            pid = f"PROD-{i+1:04d}"
            ids.append(pid)
            price = round(random.uniform(5, 500), 2)
            rows.append({
                "product_id": pid,
                "product_name": f"{subcat} {random.choice(['Pro', 'Elite', 'Basic', 'Plus'])}",
                "category": cat,
                "subcategory": subcat,
                "brand": random.choice(["BrandA", "BrandB", "BrandC", "BrandD"]),
                "unit_price": price,
                "cost_price": round(price * random.uniform(0.4, 0.7), 2)
            })
        self.register_dimension("products", ids)
        self.write_csv("dim_products.csv", rows)
    
    def generate_stores(self, n: int):
        rows = []
        ids = []
        cities = ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes", "Strasbourg", "Bordeaux"]
        for i in range(n):
            sid = f"STORE-{i+1:03d}"
            ids.append(sid)
            rows.append({
                "store_id": sid,
                "store_name": f"Store {cities[i % len(cities)]}",
                "store_type": random.choice(["Physical", "Physical", "Online"]),
                "region": random.choice(["North", "South", "East", "West"]),
                "city": cities[i % len(cities)],
                "area_sqm": random.randint(200, 5000),
                "open_date": self.random_date("2018-01-01", "2023-12-31")
            })
        self.register_dimension("stores", ids)
        self.write_csv("dim_stores.csv", rows)
    
    def generate_dates(self, start: str, end: str):
        """Generate date dimension CSV."""
        import calendar
        rows = []
        current = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")
        while current <= end_dt:
            rows.append({
                "date_key": current.strftime("%Y-%m-%d"),
                "year": current.year,
                "quarter": (current.month - 1) // 3 + 1,
                "month": current.month,
                "month_name": current.strftime("%B"),
                "week": current.isocalendar()[1],
                "day_of_week": current.isoweekday(),
                "day_name": current.strftime("%A"),
                "is_weekend": current.weekday() >= 5,
                "is_holiday": False
            })
            current += timedelta(days=1)
        self.write_csv("dim_dates.csv", rows)
    
    def generate_sales(self, n: int):
        """Generate sales transactions with realistic patterns."""
        rows = []
        for i in range(n):
            qty = random.choices([1, 2, 3, 4, 5], weights=[40, 30, 15, 10, 5])[0]
            price = round(random.uniform(10, 300), 2)
            discount = round(random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20]), 2)
            rows.append({
                "transaction_id": f"TXN-{i+1:07d}",
                "customer_id": self.get_random_fk("customers"),
                "product_id": self.get_random_fk("products"),
                "store_id": self.get_random_fk("stores"),
                "sale_date": self.random_date("2024-01-01", "2024-12-31"),
                "quantity": qty,
                "unit_price": price,
                "discount_pct": discount,
                "total_amount": round(qty * price * (1 - discount), 2)
            })
        self.write_csv("fact_sales.csv", rows)


# Quick usage
if __name__ == "__main__":
    gen = RetailDataGenerator(seed=42, output_dir="data/raw")
    gen.generate_all(n_customers=500, n_products=100, n_stores=10, n_sales=5000)
```

---

## Streaming Data Generator (For EventStream)

```python
"""Generate continuous streaming events for EventStream/Event Hub injection."""
import json
import time
import math
import random
from datetime import datetime

def generate_sensor_event(sensor_id: str, baseline: float, std: float, 
                         unit: str, site_id: str, zone_id: str) -> dict:
    """Generate a single realistic sensor event."""
    now = datetime.utcnow()
    hour_angle = (now.hour + now.minute / 60) / 24 * 2 * math.pi
    daily_cycle = math.sin(hour_angle) * std
    noise = random.gauss(0, std * 0.3)
    value = round(baseline + daily_cycle + noise, 2)
    
    return {
        "sensor_id": sensor_id,
        "site_id": site_id,
        "zone_id": zone_id,
        "value": value,
        "unit": unit,
        "quality": "Good" if abs(value - baseline) < std * 3 else "Bad",
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    }

def continuous_stream(sensors_config: list, events_per_second: float = 10, 
                     duration_seconds: int = 300):
    """Generate a continuous stream of events (for azure-eventhub injection)."""
    interval = 1.0 / events_per_second
    end_time = time.time() + duration_seconds
    count = 0
    
    while time.time() < end_time:
        sensor = random.choice(sensors_config)
        event = generate_sensor_event(**sensor)
        yield json.dumps(event)
        count += 1
        time.sleep(interval)
    
    print(f"Generated {count} events in {duration_seconds}s")

# Usage with azure-eventhub
# from azure.eventhub import EventHubProducerClient, EventData
# producer = EventHubProducerClient.from_connection_string(conn_str, eventhub_name=eh_name)
# for event_json in continuous_stream(sensors, events_per_second=10, duration_seconds=60):
#     batch = producer.create_batch()
#     batch.add(EventData(event_json))
#     producer.send_batch(batch)
```

---

## Tips

1. **Always use a seed** — `random.seed(42)` ensures reproducible demo data
2. **Match cardinalities** — 5 sites × 4 zones = 20 zones, not 500
3. **Keep dimension sizes small** — Large dimensions slow down Trial capacity
4. **Use weighted random** — `random.choices(items, weights=...)` for realistic distributions
5. **Time series data** — Use sine waves + gaussian noise for sensor data, not pure random
6. **Anomalies** — Inject 2-5% anomalies for interesting alerts and dashboards
7. **BOM-free CSV** — Always use `encoding="utf-8"` (not `utf-8-sig`) when writing
8. **Consistent timestamps** — Use ISO 8601 format: `2024-01-15T10:30:00Z`
