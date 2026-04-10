import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
import json
import csv
from io import StringIO
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GG_DEALS_API_KEY = os.getenv("GG_DEALS_API_KEY")
GG_DEALS_URL = "https://api.gg.deals/v1/prices/by-steam-app-id/"
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017")

try:
    client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
    db = client.purchasing_dw
except Exception as e:
    print(f"Baza danych MongoDB jest niedostępna: {e}")
    db = None

class CompareResponse(BaseModel):
    game_title: str
    region1_price: float
    region1_currency: str
    region1_copies: float
    region2_price: float
    region2_currency: str
    region2_copies: float

@app.get("/api/dw/history")
def get_dw_history(region1: str, region2: str):
    base_power = {"pl": 12, "de": 35, "us": 40, "gb": 30, "fr": 32, "au": 38, "se": 45}
    def generate_trend(base):
        return [round(base * 0.75, 1), round(base * 0.82, 1), round(base * 0.88, 1), round(base * 1.1, 1),
                round(base * 0.95, 1), base]
    r1_base = base_power.get(region1, 15)
    r2_base = base_power.get(region2, 15)
    return {
        "years": ["2019", "2020", "2021", "2022", "2023", "2024"],
        "region1_data": generate_trend(r1_base),
        "region2_data": generate_trend(r2_base)
    }

@app.get("/api/dw/basket")
def get_dw_basket(region1: str, region2: str, wage1: float, wage2: float):
    basket_prices = {"pl": 850, "de": 250, "us": 280, "gb": 220, "fr": 250, "au": 350, "se": 2800}
    p1 = basket_prices.get(region1, 300)
    p2 = basket_prices.get(region2, 300)
    return {
        "region1_basket_price": p1,
        "region1_pct": round((p1 / wage1) * 100, 2) if wage1 else 0,
        "region2_basket_price": p2,
        "region2_pct": round((p2 / wage2) * 100, 2) if wage2 else 0
    }

@app.get("/api/wages")
def get_wages():
    url = "https://docs.google.com/spreadsheets/d/10SWFijTAHJRiN1v5SEtQ5GRoEu4K0XZwBh_26KNhz9A/export?format=csv"
    try:
        response = requests.get(url)
        response.raise_for_status()
        response.encoding = 'utf-8'
        csv_reader = csv.DictReader(StringIO(response.text))
        wages_data = {}
        for row in csv_reader:
            wages_data[row['region']] = {
                "min": float(row['min']),
                "avg": float(row['avg']),
                "currency": row['currency']
            }
        return wages_data
    except Exception as e:
        raise HTTPException(status_code=500, detail="Brak dostepu do bazy zarobkow")

@app.get("/api/top-games")
def get_top_games():
    url = "https://steamspy.com/api.php?request=top100in2weeks"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Nie udało się pobrać listy gier.")
    data = response.json()
    games_list = []
    for app_id, details in data.items():
        price = str(details.get("price", "0"))
        if price != "0" and price != "":
            games_list.append({"appid": app_id, "name": details.get("name")})
    return {"games": games_list}

@app.get("/api/search")
def search_games(query: str):
    if not query or len(query) < 3:
        return {"games": []}
    url = f"https://store.steampowered.com/api/storesearch/?term={query}&l=english&cc=US"
    try:
        response = requests.get(url)
        data = response.json()
        games = []
        for item in data.get("items", []):
            games.append({"title": item.get("name"), "value": str(item.get("id"))})
        return {"games": games}
    except Exception:
        return {"games": []}

def fetch_game_price(app_id: str, region: str):
    if not GG_DEALS_API_KEY:
        raise HTTPException(status_code=500, detail="Brak klucza API.")
    params = {"key": GG_DEALS_API_KEY, "ids": app_id, "region": region}
    response = requests.get(GG_DEALS_URL, params=params)
    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="Przekroczono limit.")
    data = response.json()
    if not data.get("success"):
        raise HTTPException(status_code=400, detail="Blad API GG.deals")
    game_data = data["data"].get(str(app_id))
    if not game_data:
        raise HTTPException(status_code=404, detail="Brak danych.")
    prices = game_data.get("prices", {})
    price_str = prices.get("currentRetail") or prices.get("currentKeyshops")
    if not price_str:
        raise HTTPException(status_code=404, detail="Brak ceny.")
    return {
        "title": game_data.get("title"),
        "price": float(price_str),
        "currency": prices.get("currency")
    }

@app.get("/api/compare", response_model=CompareResponse)
async def compare_power(app_id: str, region1: str, region2: str, wage1: float, wage2: float):
    data1 = fetch_game_price(app_id, region1)
    data2 = fetch_game_price(app_id, region2)
    copies1 = round(wage1 / data1["price"], 2) if data1["price"] > 0 else 0
    copies2 = round(wage2 / data2["price"], 2) if data2["price"] > 0 else 0

    response_data = {
        "game_title": data1["title"],
        "region1_price": data1["price"],
        "region1_currency": data1["currency"],
        "region1_copies": copies1,
        "region2_price": data2["price"],
        "region2_currency": data2["currency"],
        "region2_copies": copies2
    }

    if db is not None:
        try:
            fact_entry = response_data.copy()
            fact_entry["app_id"] = app_id
            fact_entry["region1"] = region1
            fact_entry["region2"] = region2
            fact_entry["timestamp"] = datetime.utcnow()
            await db.fact_economy.insert_one(fact_entry)
        except Exception as e:
            print(f"Nie udalo sie zapisac faktu do MongoDB: {e}")

    return response_data