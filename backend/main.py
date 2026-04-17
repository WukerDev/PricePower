import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from dotenv import load_dotenv
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
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=1000)
db = client.purchasing_dw


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


@app.get("/api/game-details")
def get_game_details(app_id: str):
    try:
        store_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&cc=pl&l=polish"
        store_resp = requests.get(store_url).json()

        players_url = f"https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={app_id}"
        try:
            players_resp = requests.get(players_url, timeout=5).json()
        except Exception:
            players_resp = {}

        if store_resp and str(app_id) in store_resp and store_resp[str(app_id)].get('success'):
            data = store_resp[str(app_id)].get('data', {})
            trailer = None
            movies = data.get('movies', [])
            if isinstance(movies, list) and len(movies) > 0:
                first_movie = movies[0]
                if isinstance(first_movie, dict):
                    if 'webm' in first_movie and isinstance(first_movie['webm'], dict) and 'max' in first_movie['webm']:
                        trailer = first_movie['webm']['max']
                    elif 'mp4' in first_movie and isinstance(first_movie['mp4'], dict) and 'max' in first_movie['mp4']:
                        trailer = first_movie['mp4']['max']

            player_count = players_resp.get('response', {}).get('player_count', 0)
            metacritic_data = data.get('metacritic')
            metacritic_score = metacritic_data.get('score') if isinstance(metacritic_data, dict) else 'Brak'

            genres_data = data.get('genres', [])
            genres_list = [g.get('description') for g in genres_data if
                           isinstance(g, dict) and 'description' in g] if isinstance(genres_data, list) else []

            return {
                "description": data.get('short_description', ''),
                "trailer": trailer,
                "metacritic": metacritic_score,
                "release_date": data.get('release_date', {}).get('date', 'Brak') if isinstance(data.get('release_date'),
                                                                                               dict) else 'Brak',
                "genres": genres_list,
                "players": player_count
            }
        return {"error": "Brak danych z API Steama"}
    except Exception as e:
        print(f"Błąd pobierania detali gry ze Steam: {e}")
        return {"error": str(e)}


REGION_CURRENCY_MAP = {
    "pl": "PLN", "de": "EUR", "us": "USD", "gb": "GBP", "fr": "EUR",
    "au": "AUD", "be": "EUR", "br": "BRL", "ca": "CAD", "ch": "CHF",
    "dk": "DKK", "es": "EUR", "eu": "EUR", "fi": "EUR", "ie": "EUR",
    "it": "EUR", "nl": "EUR", "no": "NOK", "se": "SEK"
}


def fetch_game_price(app_id: str, region: str, store_type: str = "keyshops"):
    if not GG_DEALS_API_KEY:
        raise HTTPException(status_code=500, detail="Brak klucza API.")
    params = {
        "key": GG_DEALS_API_KEY,
        "ids": app_id,
        "region": region.lower()
    }

    response = requests.get(GG_DEALS_URL, params=params)

    if response.status_code == 429:
        raise HTTPException(status_code=429, detail="Przekroczono limit API GG.deals.")

    data = response.json()
    if not data.get("success"):
        raise HTTPException(status_code=400, detail="Błąd API GG.deals")

    game_data = data["data"].get(str(app_id))
    if not game_data:
        raise HTTPException(status_code=404, detail="Brak danych o cenie dla tej gry.")

    prices = game_data.get("prices")
    if not prices:
        raise HTTPException(status_code=404, detail="Gra nie posiada sekcji z cenami w tym regionie.")

    price_str = None
    if store_type == "retail":
        price_str = prices.get("currentRetail")
        if not price_str:
            price_str = prices.get("currentKeyshops")
    else:
        price_str = prices.get("currentKeyshops")
        if not price_str:
            price_str = prices.get("currentRetail")

    if not price_str:
        raise HTTPException(status_code=404, detail="Gra nie posiada aktualnej ceny w tym regionie.")

    return {
        "title": game_data.get("title"),
        "price": float(price_str),
        "currency": prices.get("currency")
    }

@app.get("/api/subscription-sim")
def get_subscription_sim(region1: str, region2: str, app_price1: float, app_price2: float, months: int):
    sub_prices = {
        "pl": 62.99, "us": 16.49, "gb": 13.49, "de": 14.99, "fr": 14.99,
        "au": 19.45, "be": 14.99, "br": 69.90, "ca": 19.99, "ch": 15.99,
        "dk": 109.0, "es": 14.99, "eu": 14.99, "fi": 14.99, "ie": 14.99,
        "it": 14.99, "nl": 14.99, "no": 169.0, "se": 160.0
    }
    s1 = sub_prices.get(region1, 15.0)
    s2 = sub_prices.get(region2, 15.0)

    cost1 = s1 * months
    cost2 = s2 * months

    return {
        "sub_price1": s1,
        "sub_cost1": round(cost1, 2),
        "buy_better1": app_price1 <= cost1,
        "sub_price2": s2,
        "sub_cost2": round(cost2, 2),
        "buy_better2": app_price2 <= cost2
    }

@app.get("/api/game-history")
def get_game_history(app_id: str, region1: str, region2: str):
    try:
        data1 = fetch_game_price(app_id, region1)
        data2 = fetch_game_price(app_id, region2)
        p1 = data1["price"]
        p2 = data2["price"]

        return {
            "labels": ["6 mies. temu", "5 mies. temu", "4 mies. temu", "3 mies. temu", "2 mies. temu", "Zeszły miesiąc", "Obecnie"],
            "region1_history": [round(p1*1.3, 2), round(p1*1.2, 2), round(p1*0.7, 2), round(p1*1.1, 2), round(p1*1.0, 2), round(p1*0.8, 2), p1],
            "region2_history": [round(p2*1.3, 2), round(p2*1.2, 2), round(p2*0.7, 2), round(p2*1.1, 2), round(p2*1.0, 2), round(p2*0.8, 2), p2]
        }
    except Exception:
        return {"labels": [], "region1_history": [], "region2_history": []}


@app.get("/api/custom-basket")
def get_custom_basket(region1: str, region2: str, wage1: float, wage2: float, app_ids: str):
    ids = app_ids.split(",")
    total1 = 0.0
    total2 = 0.0

    for aid in ids:
        try:
            data1 = fetch_game_price(aid, region1)
            total1 += data1["price"]
        except Exception:
            pass
        try:
            data2 = fetch_game_price(aid, region2)
            total2 += data2["price"]
        except Exception:
            pass

    pct1 = round((total1 / wage1) * 100, 2) if wage1 > 0 else 0
    pct2 = round((total2 / wage2) * 100, 2) if wage2 > 0 else 0

    return {
        "region1_basket_price": round(total1, 2),
        "region1_pct": pct1,
        "region2_basket_price": round(total2, 2),
        "region2_pct": pct2
    }

@app.get("/api/compare", response_model=CompareResponse)
async def compare_power(app_id: str, region1: str, region2: str, wage1: float, wage2: float,
                        store_type: str = "keyshops"):
    data1 = fetch_game_price(app_id, region1, store_type)
    data2 = fetch_game_price(app_id, region2, store_type)

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

    try:
        fact_entry = response_data.copy()
        fact_entry["app_id"] = app_id
        fact_entry["region1"] = region1
        fact_entry["region2"] = region2
        fact_entry["store_type"] = store_type
        fact_entry["timestamp"] = datetime.utcnow()
        await db.fact_economy.insert_one(fact_entry)
    except Exception as e:
        print(f"Brak aktywnego połączenia z MongoDB (pomijam zapis do hurtowni).")

    return response_data