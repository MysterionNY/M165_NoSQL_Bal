import time
import random
import redis
import json

# KONFIGURATION
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print("Verbunden mit Redis")
except Exception as e:
    print(f"Konnte nicht mit Redis verbinden: {e}")
    r = None

def fetch_crypto_history(coin_symbol):
    """Simuliert eine API mit starkem Rate-Limit und langsamer Antwortzeit"""
    print(f"... Umgehe Rate-Limit und lade Blockchain-Historie für '{coin_symbol}' (bitte warten) ...")
    time.sleep(3.5)

    history = {
        "symbol": coin_symbol,
        "current_price": random.uniform(20000, 60000),
        "24h_high": 61000,
        "24h_low": 19500,
        "trend": random.choice(["bullish", "bearish", "neutral"])
    }

    return json.dumps(history)

def get_crypto_data(coin_symbol):
    cache_key = f"crypto:{coin_symbol}"

    if r:
        cached_data = r.get(cache_key)

        if cached_data:
            print("Cache Hit: Daten wurden aus Redis geladen")
            return cached_data

    print("Cache Miss: Daten nicht im Cache gefunden")
    data = fetch_crypto_history(coin_symbol)

    if r:
        r.setex(cache_key, 60, data)
        print("Daten wurden für 60 Sekunden in Redis gespeichert")

    return data

# TEST-ABLAUF
test_coin = "BTC"

print("\n--- Erster Aufruf (Cache Miss - sollte langsam sein) ---")
start = time.time()
print(f"Krypto-Daten: {get_crypto_data(test_coin)}")
print(f"Dauer: {time.time() - start:.4f} Sekunden")

print("\n--- Zweiter Aufruf (Cache Hit - sollte blitzschnell sein) ---")
start = time.time()
print(f"Krypto-Daten: {get_crypto_data(test_coin)}")
print(f"Dauer: {time.time() - start:.4f} Sekunden")