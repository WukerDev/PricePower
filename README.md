Price Power 🎮📊
Wielowymiarowa aplikacja analityczna służąca do porównywania siły nabywczej graczy w różnych państwach. Projekt został zrealizowany jako praktyczna implementacja koncepcji Hurtowni Danych (Data Warehouse) oraz systemów OLAP.

🚀 Główne funkcjonalności
Analiza Wielowymiarowa (OLAP Slice & Dice): Zestawienie cen gier ze Steama (API GG.deals) z medianą i płacą minimalną w wybranych przekrojach geograficznych.

Bogate Wizualizacje: Wykorzystanie zaawansowanych wykresów do prezentacji danych:

Radar Chart – Wielowymiarowy profil ekonomiczny regionu.

Waffle Chart – Wizualizacja siły nabywczej (ilość kopii gry za pensję).

Doughnut Chart – Interaktywny symulator podziału kosztów życia.

Bar Chart – Globalny benchmark i indeksowanie regionów.

Line Chart – Historyczna analiza szeregów czasowych (Time-Series) 2019-2024.

Integracja Steam API: Pobieranie metadanych o grach w czasie rzeczywistym (zwiastuny, liczba aktywnych graczy, oceny Metacritic, gatunki).

Asynchroniczna Hurtownia Danych: Zapisywanie faktów analitycznych w bazie MongoDB z zachowaniem pełnej ciągłości działania aplikacji (Non-blocking I/O) nawet przy braku połączenia z klastrem bazy danych.

Nowoczesny UX/UI: Responsywny interfejs zbudowany w oparciu o Vuetify 3 z dynamicznym oświetleniem, maskowaniem wektorowym SVG oraz interaktywnym tłem cząsteczkowym (Plexus).

🛠 Technologie
Frontend
Vue 3 (Composition API)

TypeScript

Vuetify 3 (Material Design)

Chart.js + vue-chartjs

Axios

Vite

Backend
Python 3.12

FastAPI

Motor (Asynchroniczny sterownik MongoDB)

Uvicorn

Baza Danych / OLAP
MongoDB (Architektura pod hurtownię danych)

🏗 Architektura Hurtowni Danych
Aplikacja mapuje klasyczne zagadnienia modelowania wielowymiarowego:

Tabela Faktów (fact_economy): Przechowuje wyliczone miary (cena w regionie 1, cena w regionie 2, wyliczona ilość kopii, różnice walutowe).

Wymiary (Dimensions): Dim_Game (gra, gatunek), Dim_Region (kraj, waluta), Dim_Time (data zapytania i analizy).

Kostka OLAP: Możliwość filtrowania danych przez konkretny tytuł i porównywania dowolnych par regionów względem zarobków minimalnych i średnich.

⚙️ Uruchomienie projektu
Wymagania wstępne
Node.js (wersja 18+)

Python 3.10+

Docker (do lokalnej bazy danych)

1. Baza Danych (MongoDB)
Uruchom bazę lokalnie za pomocą Dockera:

Bash
docker run -d --name purchasing_db -p 27017:27017 mongo:latest
2. Backend (FastAPI)
Przejdź do folderu backend/ i skonfiguruj środowisko wirtualne:

Bash
python -m venv venv
.\venv\Scripts\activate
pip install fastapi uvicorn requests python-dotenv motor pymongo
Utwórz plik .env w folderze backend/:

Fragment kodu
GG_DEALS_API_KEY=twój_klucz_api
MONGO_URL=mongodb://localhost:27017
Uruchom serwer aplikacji:

Bash
uvicorn main:app --reload --port 8000
3. Frontend (Vue 3)
Przejdź do folderu frontend/, zainstaluj zależności i uruchom serwer deweloperski:

Bash
npm install
npm install chart.js vue-chartjs axios
npm run dev
