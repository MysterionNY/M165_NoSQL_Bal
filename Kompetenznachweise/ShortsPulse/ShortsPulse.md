# Youtube Analytics Auswertung mit Prometheus & Grafana

# Inhaltsverzeichnis
- [Youtube Analytics Auswertung mit Prometheus \& Grafana](#youtube-analytics-auswertung-mit-prometheus--grafana)
- [Inhaltsverzeichnis](#inhaltsverzeichnis)
  - [Phase 1: Projektidee](#phase-1-projektidee)
  - [Phase 1.1: Ausgangslage](#phase-11-ausgangslage)
  - [Phase 1.2 Verwendete Technologien](#phase-12-verwendete-technologien)
  - [Phase 1.3 MongoDB als NoSQL-Datenbank](#phase-13-mongodb-als-nosql-datenbank)
    - [Collection: `analytics_snapshots`](#collection-analytics_snapshots)
    - [Collection: `video_analytics_snapshots`](#collection-video_analytics_snapshots)
  - [Phase 2: YouTube API Import](#phase-2-youtube-api-import)
    - [Tagesreport](#tagesreport)
    - [Videoreport](#videoreport)
  - [Phase 2.1: FastAPI-Endpunkte](#phase-21-fastapi-endpunkte)
  - [Phase 3: Prometheus-Metriken](#phase-3-prometheus-metriken)
  - [Phase 4: Grafana Dashboard](#phase-4-grafana-dashboard)
  - [Phase 4.1: Docker Compose](#phase-41-docker-compose)
  - [Phase 5: Starten des Projekts](#phase-5-starten-des-projekts)
    - [Virtuelle Umgebung aktivieren](#virtuelle-umgebung-aktivieren)
    - [MongoDB, Prometheus und Grafana starten](#mongodb-prometheus-und-grafana-starten)
    - [FastAPI starten](#fastapi-starten)
    - [YouTube-Daten importieren](#youtube-daten-importieren)
    - [Wichtige URLs](#wichtige-urls)
  - [Erkenntnisse](#erkenntnisse)
  - [Fazit](#fazit)
  - [Anmerkung](#anmerkung)


## Phase 1: Projektidee

ShortsPulse ist eine kleine NoSQL- und Monitoring-Anwendung zur Auswertung von YouTube Shorts.  
Die Anwendung ruft echte Analytics-Daten über die YouTube Analytics API ab, speichert diese in MongoDB, stellt sie über eine FastAPI-Anwendung bereit und exportiert Metriken für Prometheus. Anschließend werden die Daten in Grafana visualisiert.

Das Ziel des Projekts war es, ein kleines, aber praxisnahes NoSQL-Projekt umzusetzen, das echte Daten verwendet und gleichzeitig mehrere Inhalte aus Modul 165 verbindet.

## Phase 1.1: Ausgangslage

Ich betreibe einen YouTube-Kanal mit mehreren Shorts. Im Moment werden alle Analytics auf Youtube Analytics angezeigt, jedoch hat mir da ein persönlicher Touch, mit der gewissen Visualisierung gefehlt. Ausserdem ist mir aufgefallen, dass die Werte nicht immer gleich aktuell mit der API waren (Die API hat die Werte schneller ausgewertet, als diese eigentlich auf Youtube Analytics angezeigt werden.)

Daher gab es gewisse Analytics die mich interessiert hatten in einem persönlich ausgesuchten Stil auszuwerten und ebenfalls die aktuellen Daten schneller zu erhalten. Dabei haben sich dann diese Metriken ergeben.

Aktuell wurden folgende Werte ausgewertet:

| Metriken | Wert |
|---|---:|
| Anzahl gespeicherter Tages-Snapshots | 29 |
| Anzahl ausgewerteter Videos | 10 |
| Gesamtaufrufe | 118'313 |
| Gesamtlikes | 2'875 |
| Gesamtkommentare | 26 |
| Gesamtshares | 74 |

Die Werte beziehen sich auf den abgefragten Zeitraum und werden aus den gespeicherten YouTube-Analytics-Daten berechnet.

## Phase 1.2 Verwendete Technologien

| Technologie | Verwendung |
|---|---|
| Python | Hauptsprache für Import, API und Verarbeitung |
| YouTube Analytics API | Abfrage von Kanal- und Videostatistiken |
| YouTube Data API v3 | Abfrage von Videotiteln und Metadaten |
| MongoDB | NoSQL-Datenbank für Analytics-Snapshots |
| FastAPI | Kleine Web-API für gespeicherte Daten |
| Prometheus | Scraping und Speicherung von Metriken |
| Grafana | Visualisierung der Metriken |
| Docker Compose | Starten von MongoDB, Prometheus und Grafana |

## Phase 1.3 MongoDB als NoSQL-Datenbank

MongoDB wurde verwendet, weil die Daten flexibel und dokumentenbasiert gespeichert werden können. Für dieses Projekt passt MongoDB besonders gut, da Tagesdaten, Videodaten und Metadaten unterschiedlich aufgebaut sein können.

### Collection: `analytics_snapshots`

Diese Collection speichert Tageswerte des gesamten Kanals.

Beispiel:

```json
{
  "date": "2026-06-30",
  "views": 15956,
  "likes": 206,
  "comments": 3,
  "shares": 2,
  "estimatedMinutesWatched": 3277,
  "averageViewDuration": 20.0,
  "importedAt": "2026-07-06T12:00:00Z"
}
```

### Collection: `video_analytics_snapshots`

Diese Collection speichert Auswertungen pro Video.

Beispiel:

```json
{
  "videoId": "HThLC9oNLbA",
  "title": "Ranking the biggest cat fails 🐈 #cats #fails #shorts",
  "views": 82,
  "likes": 4,
  "comments": 3,
  "shares": 0,
  "estimatedMinutesWatched": 155,
  "averageViewDuration": 273.0,
  "publishedAt": "2026-06-27T16:01:54Z",
  "channelTitle": "Hype Hub",
  "startDate": "2026-06-05",
  "endDate": "2026-07-03",
  "importedAt": "2026-07-06T12:00:00Z"
}
```

![Terminal Analytics](/Kompetenznachweise/ShortsPulse/Images/Terminal-Analytics.png)

![Terminal JSON](/Kompetenznachweise/ShortsPulse/Images/Terminal-JSON.png)

![Terminal Auswertung der Total Dokumente](/Kompetenznachweise/ShortsPulse/Images/Terminal-Auswertung%20der%20Total%20Dokumente.png)

![Terminal Ausgabe mit allen Werten](/Kompetenznachweise/ShortsPulse/Images/Terminal-JSON%20Ausgabe%20mit%20allen%20Werten.png)

![Terminal Ausgabe der Totalwerte](/Kompetenznachweise/ShortsPulse/Images/Terminal-Ausgabe%20der%20Totalwerte%20für%20einne%20bestimmten%20Zeitraum.png)

Damit die Daten beim erneuten Import nicht doppelt gespeichert werden, wird mit `upsert` gearbeitet. Bereits vorhandene Einträge werden aktualisiert, neue Einträge werden eingefügt.

## Phase 2: YouTube API Import

Zuerst wurde ein OAuth-Zugang über Google Cloud eingerichtet. Dafür wurden die folgenden APIs aktiviert:

* YouTube Analytics API
* YouTube Data API v3

Die YouTube Analytics API wird verwendet, um Performance-Daten wie Views, Likes, Kommentare, Shares und Watchtime abzufragen.

Die YouTube Data API v3 wird zusätzlich verwendet, um zu den Video-IDs die passenden Titel und Metadaten zu laden.

Der Import fragt zwei Arten von Reports ab:

### Tagesreport

```text
dimensions=day
```

Dieser Report zeigt, wie sich der gesamte Kanal pro Tag entwickelt hat.

### Videoreport

```text
dimensions=video
```

Dieser Report zeigt, welche Videos im gewählten Zeitraum wie viele Aufrufe, Likes, Kommentare und Shares erhalten haben.

## Phase 2.1: FastAPI-Endpunkte

Die FastAPI-Anwendung stellt die gespeicherten Daten über mehrere Endpunkte bereit.

| Endpunkt       | Beschreibung                                           |
| -------------- | ------------------------------------------------------ |
| `GET /health`  | Prüft, ob die API läuft                                |
| `GET /daily`   | Gibt alle Tages-Snapshots aus MongoDB zurück           |
| `GET /videos`  | Gibt alle Video-Snapshots sortiert nach Views zurück   |
| `GET /summary` | Gibt eine Zusammenfassung der wichtigsten Werte zurück |
| `GET /metrics` | Gibt Prometheus-kompatible Metriken zurück             |

Beispiel für `/summary`:

```json
{
  "dailySnapshotCount": 29,
  "videoSnapshotCount": 10,
  "totalViews": 118313,
  "totalLikes": 2875,
  "totalComments": 26,
  "totalShares": 74,
  "engagementRate": 0.0252,
  "topVideo": {
    "title": "..."
  }
}
```

![Metrics Ausgabe](/Kompetenznachweise/ShortsPulse/Images/Metrics%20Ausgabe.png)

## Phase 3: Prometheus-Metriken

Über den Endpunkt `/metrics` stellt die Anwendung eigene Metriken bereit.

Beispiele:

```text
shortspulse_daily_snapshots 29
shortspulse_video_snapshots 10
shortspulse_total_views 118313
shortspulse_total_likes 2875
shortspulse_total_comments 26
shortspulse_total_shares 74
shortspulse_engagement_rate 0.0252
```

Zusätzlich werden auch Metriken pro Video bereitgestellt:

```text
shortspulse_video_views{video_id="HThLC9oNLbA",title="Ranking the biggest cat fails 🐈 #cats #fails #shorts"} 82
shortspulse_video_likes{video_id="HThLC9oNLbA",title="Ranking the biggest cat fails 🐈 #cats #fails #shorts"} 4
shortspulse_video_comments{video_id="HThLC9oNLbA",title="Ranking the biggest cat fails 🐈 #cats #fails #shorts"} 3
```

Prometheus ruft diese Metriken regelmäßig ab und speichert sie als Zeitreihen.

![Prompetheus](/Kompetenznachweise/ShortsPulse/Images/Prompetheus%20Ausgabe.png)

## Phase 4: Grafana Dashboard

In Grafana wurde ein Dashboard erstellt, das die wichtigsten Kennzahlen visualisiert.

Verwendete Panels:

| Panel                  | Metrik                              |
| ---------------------- | ----------------------------------- |
| Total Views            | `shortspulse_total_views`           |
| Total Likes            | `shortspulse_total_likes`           |
| Engagement Rate        | `shortspulse_engagement_rate * 100` |
| Views per Video        | `shortspulse_video_views`           |
| Likes per Video        | `shortspulse_video_likes`           |
| Stored Daily Snapshots | `shortspulse_daily_snapshots`       |
| Stored Video Snapshots | `shortspulse_video_snapshots`       |

Damit lassen sich die Performance der Shorts und der aktuelle Datenbestand übersichtlich darstellen.

![Grafana Visualisierung](/Kompetenznachweise/ShortsPulse/Images/Grafana%20Visualisierung.png)

## Phase 4.1: Docker Compose

MongoDB, Prometheus und Grafana werden über Docker Compose gestartet.

```yaml
services:
  mongo:
    image: mongo:7
    container_name: shortspulse-mongo
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  prometheus:
    image: prom/prometheus
    container_name: shortspulse-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    depends_on:
      - mongo

  grafana:
    image: grafana/grafana
    container_name: shortspulse-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  mongo_data:
  grafana_data:
```

Prometheus verwendet folgende Konfiguration:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "shortspulse"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["host.docker.internal:8000"]
```

Da FastAPI lokal auf dem Host läuft und Prometheus in Docker, wird `host.docker.internal:8000` verwendet.

## Phase 5: Starten des Projekts

### Virtuelle Umgebung aktivieren

```bash
source .venv/bin/activate
```

### MongoDB, Prometheus und Grafana starten

```bash
docker compose up -d
```

### FastAPI starten

```bash
uvicorn app.api:app --reload
```

### YouTube-Daten importieren

```bash
python main.py
```

### Wichtige URLs

| Dienst       | URL                          |
| ------------ | ---------------------------- |
| FastAPI      | `http://127.0.0.1:8000`      |
| FastAPI Docs | `http://127.0.0.1:8000/docs` |
| Prometheus   | `http://localhost:9090`      |
| Grafana      | `http://localhost:3000`      |

## Erkenntnisse

Durch das Projekt wurde deutlich, wie verschiedene NoSQL- und Monitoring-Komponenten zusammenspielen können.

MongoDB eignet sich gut für die Speicherung von flexiblen Analytics-Daten, weil Tageswerte, Videowerte und Metadaten nicht zwingend in ein starres relationales Schema passen müssen.

Prometheus eignet sich dagegen nicht als normale Datenbank für Dokumente, sondern als Zeitreihen-System für Metriken. Deshalb werden die eigentlichen Daten in MongoDB gespeichert, während Prometheus nur die wichtigsten Kennzahlen regelmäßig abfragt.

Grafana bietet darauf aufbauend eine einfache Möglichkeit, diese Metriken visuell darzustellen.

## Fazit

ShortsPulse ist ein kleines, aber praxisnahes Projekt, das echte YouTube-Daten auswertet.
Es verbindet mehrere Themen aus Modul 165:

* dokumentenorientierte Speicherung mit MongoDB
* API-Anbindung mit OAuth
* Verarbeitung echter Analytics-Daten
* Bereitstellung einer FastAPI-Anwendung
* Monitoring mit Prometheus
* Visualisierung mit Grafana

Besonders sinnvoll war die nachträgliche Erweiterung um einzelne Videos. Dadurch werden nicht nur allgemeine Kanalwerte sichtbar, sondern auch die Performance einzelner Shorts. Das macht das Projekt realistischer und nützlicher.

## Anmerkung

Für das Erstellen der Python files ```main.py``` und ```àpp/api.py``` wurde KI zur Hilfe genutzt. Da der Umfang sonst zu gross gewesen wäre für dieses Projekt, ich jedoch die Projekt-Idee sehr cool fand und daher mir die Umsetzung wichtig war.