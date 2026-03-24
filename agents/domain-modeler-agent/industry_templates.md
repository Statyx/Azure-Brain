# Industry Templates — Pre-Built Domain Models

## How to Use Templates

Each template provides a complete domain model for a specific industry. Copy the relevant template and customize:
1. Adjust dimension attributes to match your client's terminology
2. Add/remove measures based on KPIs they care about
3. Scale sample data counts for your demo duration

---

## Template 1: Manufacturing / IoT

**Scenario**: Smart factory monitoring — sensors on equipment, real-time alerts, production tracking.

### Dimensions
| Table | Key | Attributes | Rows (Demo) |
|-------|-----|-----------|-------------|
| `dim_sites` | site_id | site_name, address, latitude, longitude, timezone | 3-5 |
| `dim_zones` | zone_id | zone_name, site_id (FK), zone_type (Production/Storage/Utility) | 10-20 |
| `dim_equipment` | equipment_id | equipment_name, zone_id (FK), equipment_type, manufacturer, model, install_date | 20-50 |
| `dim_sensors` | sensor_id | sensor_name, equipment_id (FK), sensor_type (Temperature/Pressure/Vibration/Humidity), unit, min_threshold, max_threshold | 50-200 |
| `dim_operators` | operator_id | operator_name, role, shift, certification_level | 10-30 |

### Facts
| Table | Grain | Keys | Measures |
|-------|-------|------|----------|
| `fact_sensor_readings` | One reading per sensor per second | sensor_id, equipment_id, zone_id, site_id, timestamp | value, quality_score |
| `fact_alerts` | One alert event | sensor_id, equipment_id, alert_type, timestamp | severity (1-5), duration_minutes |
| `fact_work_orders` | One work order | equipment_id, operator_id, created_date, completed_date | estimated_hours, actual_hours, cost |

### KQL Tables (Streaming)
```
SensorReading(sensor_id, equipment_id, zone_id, site_id, value, unit, quality, timestamp)
EquipmentAlert(alert_id, sensor_id, equipment_id, alert_type, severity, message, timestamp)
OperationalEvent(event_id, equipment_id, event_type, operator_id, details, timestamp)
```

### Ontology Entities
```
Site → Zone → Equipment → Sensor
Relationships: SensorMonitorsEquipment, EquipmentInZone, ZoneInSite
```

### Key DAX Measures
```dax
Avg Sensor Value = AVERAGE(fact_sensor_readings[value])
Alert Count = COUNTROWS(fact_alerts)
Critical Alert Count = CALCULATE([Alert Count], fact_alerts[severity] >= 4)
Equipment Uptime % = DIVIDE([Running Hours], [Total Hours], 0)
MTBF (Mean Time Between Failures) = DIVIDE([Total Running Hours], [Failure Count], 0)
```

---

## Template 2: Retail / E-Commerce

**Scenario**: Multi-store retail chain — sales analytics, inventory management, customer segmentation.

### Dimensions
| Table | Key | Attributes | Rows (Demo) |
|-------|-----|-----------|-------------|
| `dim_customers` | customer_id | customer_name, email, segment (VIP/Regular/New), region, city, loyalty_tier | 500-2000 |
| `dim_products` | product_id | product_name, category, subcategory, brand, unit_price, cost_price | 100-500 |
| `dim_stores` | store_id | store_name, store_type (Physical/Online), region, city, area_sqm, open_date | 5-20 |
| `dim_dates` | date_key | (standard date dimension) | 1095 (3 years) |
| `dim_promotions` | promotion_id | promotion_name, type (Discount/BOGO/Coupon), start_date, end_date, discount_pct | 20-50 |

### Facts
| Table | Grain | Keys | Measures |
|-------|-------|------|----------|
| `fact_sales` | One sale transaction line item | customer_id, product_id, store_id, sale_date, promotion_id | quantity, unit_price, discount, total_amount |
| `fact_inventory` | Daily snapshot per product per store | product_id, store_id, snapshot_date | qty_on_hand, qty_on_order, qty_sold_today |
| `fact_web_events` | One web interaction | customer_id, product_id, event_date, event_type | page_views, add_to_cart, purchase |

### KQL Tables (Streaming)
```
WebClickstream(session_id, customer_id, page_url, event_type, product_id, timestamp)
POSTransaction(transaction_id, store_id, customer_id, product_id, quantity, amount, timestamp)
```

### Key DAX Measures
```dax
Total Revenue = SUM(fact_sales[total_amount])
Basket Size = DIVIDE([Total Revenue], DISTINCTCOUNT(fact_sales[transaction_id]), 0)
Customer Count = DISTINCTCOUNT(fact_sales[customer_id])
Revenue per Customer = DIVIDE([Total Revenue], [Customer Count], 0)
Sell-Through Rate = DIVIDE([Qty Sold], [Qty Received], 0)
Inventory Days of Supply = DIVIDE([Qty On Hand], [Avg Daily Sales], 0)
```

---

## Template 3: Energy / Utilities

**Scenario**: Power grid monitoring — smart meters, consumption analytics, generation tracking.

### Dimensions
| Table | Key | Attributes | Rows (Demo) |
|-------|-----|-----------|-------------|
| `dim_meters` | meter_id | meter_type (Electric/Gas/Water), customer_id, location, install_date, protocol | 100-500 |
| `dim_customers` | customer_id | customer_name, account_type (Residential/Commercial/Industrial), tariff_plan, region | 50-200 |
| `dim_substations` | substation_id | substation_name, region, capacity_MW, voltage_level | 5-15 |
| `dim_generators` | generator_id | generator_name, fuel_type (Solar/Wind/Gas/Hydro), capacity_MW, location | 10-30 |

### Facts
| Table | Grain | Keys | Measures |
|-------|-------|------|----------|
| `fact_meter_readings` | One reading per meter per 15-min interval | meter_id, customer_id, reading_datetime | kwh_consumed, demand_kw, voltage, power_factor |
| `fact_generation` | Hourly per generator | generator_id, generation_date, hour | kwh_generated, capacity_factor, co2_tons |
| `fact_grid_events` | One event | substation_id, event_datetime, event_type | duration_minutes, customers_affected, mwh_lost |

### KQL Tables (Streaming)
```
MeterReading(meter_id, customer_id, kwh, demand_kw, voltage, power_factor, timestamp)
GridEvent(event_id, substation_id, event_type, severity, customers_affected, timestamp)
GeneratorOutput(generator_id, kwh_generated, capacity_pct, timestamp)
```

### Key DAX Measures
```dax
Total Consumption kWh = SUM(fact_meter_readings[kwh_consumed])
Peak Demand kW = MAX(fact_meter_readings[demand_kw])
Avg Power Factor = AVERAGE(fact_meter_readings[power_factor])
Total Generation kWh = SUM(fact_generation[kwh_generated])
Renewable % = DIVIDE([Renewable Generation], [Total Generation kWh], 0)
Grid Reliability % = 1 - DIVIDE([Outage Hours], [Total Hours], 0)
```

---

## Template 4: Healthcare

**Scenario**: Hospital operations — patient flow, bed occupancy, treatment outcomes.

### Dimensions
| Table | Key | Attributes | Rows (Demo) |
|-------|-----|-----------|-------------|
| `dim_patients` | patient_id | patient_name (anonymized), age_group, gender, insurance_type, zip_code | 200-1000 |
| `dim_departments` | department_id | department_name (ER/ICU/Surgery/General), floor, building, bed_count | 5-15 |
| `dim_physicians` | physician_id | physician_name, specialty, department_id, years_experience | 20-50 |
| `dim_procedures` | procedure_id | procedure_name, category, avg_duration_min, avg_cost | 30-100 |
| `dim_diagnoses` | diagnosis_id | diagnosis_code (ICD-10), description, category, is_chronic | 50-200 |

### Facts
| Table | Grain | Keys | Measures |
|-------|-------|------|----------|
| `fact_visits` | One patient visit | patient_id, department_id, physician_id, admission_date, discharge_date | length_of_stay_days, total_charges, patient_satisfaction |
| `fact_procedures` | One procedure performed | patient_id, physician_id, procedure_id, procedure_date | duration_min, cost, outcome_score |
| `fact_bed_census` | Daily snapshot per department | department_id, census_date | occupied_beds, available_beds, waitlist_count |

### Key DAX Measures
```dax
Avg Length of Stay = AVERAGE(fact_visits[length_of_stay_days])
Bed Occupancy % = DIVIDE([Occupied Beds], [Total Beds], 0)
Patient Satisfaction Avg = AVERAGE(fact_visits[patient_satisfaction])
Readmission Rate = DIVIDE([Readmissions 30D], [Total Discharges], 0)
Revenue per Visit = DIVIDE([Total Charges], [Visit Count], 0)
```

---

## Template 5: Supply Chain / Logistics

**Scenario**: Distribution network — shipments, warehouses, delivery tracking.

### Dimensions
| Table | Key | Attributes | Rows (Demo) |
|-------|-----|-----------|-------------|
| `dim_warehouses` | warehouse_id | warehouse_name, region, capacity_pallets, type (DC/FC/Hub) | 5-15 |
| `dim_carriers` | carrier_id | carrier_name, carrier_type (Road/Rail/Air/Sea), contract_type | 5-10 |
| `dim_products` | product_id | product_name, category, weight_kg, volume_m3, sku | 100-500 |
| `dim_destinations` | destination_id | destination_name, city, country, type (Store/Customer/Warehouse) | 50-200 |

### Facts
| Table | Grain | Keys | Measures |
|-------|-------|------|----------|
| `fact_shipments` | One shipment | warehouse_id, carrier_id, destination_id, ship_date, delivery_date | weight_kg, volume_m3, cost, delivery_days |
| `fact_warehouse_inventory` | Daily snapshot per product per warehouse | warehouse_id, product_id, snapshot_date | qty_on_hand, qty_inbound, qty_outbound |
| `fact_delivery_events` | One tracking event | shipment_id, event_datetime, event_type | location, status |

### KQL Tables (Streaming)
```
VehicleTracking(vehicle_id, shipment_id, latitude, longitude, speed_kmh, timestamp)
DeliveryEvent(shipment_id, event_type, location, status, timestamp)
```

### Key DAX Measures
```dax
Avg Delivery Days = AVERAGE(fact_shipments[delivery_days])
On-Time Delivery % = DIVIDE([On-Time Count], [Total Shipments], 0)
Shipping Cost per kg = DIVIDE([Total Shipping Cost], [Total Weight], 0)
Warehouse Utilization % = DIVIDE([Used Pallets], [Total Capacity], 0)
Perfect Order Rate = DIVIDE([Perfect Orders], [Total Orders], 0)
```

---

## Template 6: Financial Services

**Scenario**: Banking analytics — transactions, accounts, risk scoring.

### Dimensions
| Table | Key | Attributes | Rows (Demo) |
|-------|-----|-----------|-------------|
| `dim_accounts` | account_id | account_type (Checking/Savings/Credit), customer_id, open_date, branch_id, status | 200-1000 |
| `dim_customers` | customer_id | customer_name, segment (Retail/Wealth/Corporate), risk_rating, region | 100-500 |
| `dim_branches` | branch_id | branch_name, city, region, type (Physical/Digital) | 10-30 |
| `dim_products` | product_id | product_name, category (Loan/Deposit/Card/Insurance), interest_rate | 20-50 |

### Facts
| Table | Grain | Keys | Measures |
|-------|-------|------|----------|
| `fact_transactions` | One financial transaction | account_id, transaction_date, transaction_type | amount, balance_after, is_fraud_flag |
| `fact_daily_balances` | Daily snapshot per account | account_id, balance_date | closing_balance, accrued_interest |
| `fact_loan_payments` | One payment event | account_id, payment_date | principal, interest, remaining_balance, is_late |

### Key DAX Measures
```dax
Total Deposits = CALCULATE(SUM(fact_transactions[amount]), fact_transactions[type] = "Credit")
Total Withdrawals = CALCULATE(SUM(fact_transactions[amount]), fact_transactions[type] = "Debit")
Net Flow = [Total Deposits] - [Total Withdrawals]
Avg Account Balance = AVERAGE(fact_daily_balances[closing_balance])
Fraud Rate % = DIVIDE([Fraud Count], [Transaction Count], 0)
Loan Delinquency Rate = DIVIDE([Late Payments], [Total Payments], 0)
```

---

## Customization Guide

When adapting a template:

1. **Add/Remove attributes** based on available data — don't model what you can't populate
2. **Adjust cardinalities** — Demo: dozens of dimensions, thousands of facts. POC: hundreds/millions.
3. **Rename to match client vocabulary** — "customer" might be "member", "patient", "account holder"
4. **Add calculated columns** where the client expects derived fields
5. **Choose KQL tables** only for data with sub-second freshness requirements
6. **Choose ontology entities** only for dimension tables that need graph-based relationship queries
