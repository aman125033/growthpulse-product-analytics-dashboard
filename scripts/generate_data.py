
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

np.random.seed(42)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "growthpulse.db")

N_USERS = 50000

start_date = datetime(2025, 1, 1)
end_date = datetime(2025, 12, 31)

devices = ["Mobile", "Desktop", "Tablet"]
countries = ["US", "Canada", "UK", "India", "Australia"]
campaigns = ["Organic", "Paid Social", "Search Ads", "Email", "Referral"]

users = []

for user_id in range(1, N_USERS + 1):
    signup_date = start_date + timedelta(days=np.random.randint(0, 365))
    device = np.random.choice(devices, p=[0.62, 0.30, 0.08])
    country = np.random.choice(countries, p=[0.45, 0.15, 0.15, 0.15, 0.10])
    campaign = np.random.choice(campaigns, p=[0.35, 0.25, 0.20, 0.10, 0.10])
    experiment_group = np.random.choice(["Control", "Variant"], p=[0.5, 0.5])

    users.append([
        user_id,
        signup_date.date(),
        device,
        country,
        campaign,
        experiment_group
    ])

users_df = pd.DataFrame(users, columns=[
    "user_id", "signup_date", "device", "country", "campaign", "experiment_group"
])

events = []
purchases = []

for _, row in users_df.iterrows():
    user_id = row["user_id"]
    signup_date = pd.to_datetime(row["signup_date"])
    device = row["device"]
    campaign = row["campaign"]
    group = row["experiment_group"]

    events.append([user_id, "Visited Site", signup_date])

    signup_prob = 0.72
    activation_prob = 0.58
    purchase_prob = 0.28

    if device == "Mobile":
        activation_prob -= 0.08

    if campaign == "Paid Social":
        purchase_prob -= 0.04

    if group == "Variant":
        activation_prob += 0.06
        purchase_prob += 0.05

    if np.random.rand() < signup_prob:
        events.append([user_id, "Signed Up", signup_date + timedelta(hours=np.random.randint(1, 24))])

        if np.random.rand() < activation_prob:
            activation_time = signup_date + timedelta(days=np.random.randint(1, 4))
            events.append([user_id, "Activated", activation_time])

            if np.random.rand() < purchase_prob:
                purchase_time = activation_time + timedelta(days=np.random.randint(1, 10))
                amount = round(np.random.choice([19, 29, 49, 99], p=[0.35, 0.35, 0.20, 0.10]), 2)

                events.append([user_id, "Purchased", purchase_time])
                purchases.append([user_id, purchase_time, amount])

    for day, prob in [(1, 0.46), (7, 0.29), (30, 0.14)]:
        if np.random.rand() < prob:
            events.append([user_id, f"Returned Day {day}", signup_date + timedelta(days=day)])

events_df = pd.DataFrame(events, columns=["user_id", "event_name", "event_timestamp"])
purchases_df = pd.DataFrame(purchases, columns=["user_id", "purchase_timestamp", "purchase_amount"])

conn = sqlite3.connect(DB_PATH)

users_df.to_sql("users", conn, if_exists="replace", index=False)
events_df.to_sql("events", conn, if_exists="replace", index=False)
purchases_df.to_sql("purchases", conn, if_exists="replace", index=False)

conn.close()

print("Database created successfully!")
print(f"Users: {len(users_df)}")
print(f"Events: {len(events_df)}")
print(f"Purchases: {len(purchases_df)}")
print(f"Database path: {DB_PATH}")