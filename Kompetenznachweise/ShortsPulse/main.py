from datetime import date, timedelta, datetime, timezone
import os
import pickle
import json

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pymongo import MongoClient, UpdateOne


SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "shortspulse"
DAILY_COLLECTION_NAME = "analytics_snapshots"
VIDEO_COLLECTION_NAME = "video_analytics_snapshots"


def get_authenticated_services():
    credentials = None

    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token_file:
            credentials = pickle.load(token_file)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json",
            SCOPES
        )

        credentials = flow.run_local_server(port=0)

        with open("token.pickle", "wb") as token_file:
            pickle.dump(credentials, token_file)

    youtube_analytics = build("youtubeAnalytics", "v2", credentials=credentials)
    youtube_data = build("youtube", "v3", credentials=credentials)

    return youtube_analytics, youtube_data


def parse_report(response):
    headers = [header["name"] for header in response.get("columnHeaders", [])]
    rows = response.get("rows", [])

    parsed_rows = []

    for row in rows:
        data = dict(zip(headers, row))

        parsed_rows.append({
            "date": data.get("day"),
            "views": int(data.get("views", 0)),
            "likes": int(data.get("likes", 0)),
            "comments": int(data.get("comments", 0)),
            "shares": int(data.get("shares", 0)),
            "estimatedMinutesWatched": int(data.get("estimatedMinutesWatched", 0)),
            "averageViewDuration": float(data.get("averageViewDuration", 0)),
        })

    return parsed_rows

def fetch_video_report(youtube_analytics, start_date, end_date):
    response = youtube_analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        metrics="views,likes,comments,shares,estimatedMinutesWatched,averageViewDuration",
        dimensions="video",
        sort="-views",
        maxResults=10
    ).execute()

    return parse_video_report(response)

def fetch_video_titles(youtube_data, video_ids):
    if not video_ids:
        return {}

    response = youtube_data.videos().list(
        part="snippet",
        id=",".join(video_ids)
    ).execute()

    titles = {}

    for item in response.get("items", []):
        video_id = item["id"]
        title = item["snippet"]["title"]
        published_at = item["snippet"].get("publishedAt")
        channel_title = item["snippet"].get("channelTitle")

        titles[video_id] = {
            "title": title,
            "publishedAt": published_at,
            "channelTitle": channel_title
        }

    return titles

def enrich_video_rows_with_titles(video_rows, video_titles):
    enriched_rows = []

    for row in video_rows:
        video_id = row["videoId"]
        metadata = video_titles.get(video_id, {})

        enriched_rows.append({
            **row,
            "title": metadata.get("title", "Unbekannter Titel"),
            "publishedAt": metadata.get("publishedAt"),
            "channelTitle": metadata.get("channelTitle")
        })

    return enriched_rows

def parse_video_report(response):
    headers = [header["name"] for header in response.get("columnHeaders", [])]
    rows = response.get("rows", [])

    parsed_rows = []

    for row in rows:
        data = dict(zip(headers, row))

        parsed_rows.append({
            "videoId": data.get("video"),
            "views": int(data.get("views", 0)),
            "likes": int(data.get("likes", 0)),
            "comments": int(data.get("comments", 0)),
            "shares": int(data.get("shares", 0)),
            "estimatedMinutesWatched": int(data.get("estimatedMinutesWatched", 0)),
            "averageViewDuration": float(data.get("averageViewDuration", 0)),
        })

    return parsed_rows


def save_snapshots_to_mongodb(rows):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[DAILY_COLLECTION_NAME]

    now = datetime.now(timezone.utc)

    operations = []

    for row in rows:
        document = {
            **row,
            "importedAt": now
        }

        operations.append(
            UpdateOne(
                {"date": row["date"]},
                {"$set": document},
                upsert=True
            )
        )

    if not operations:
        print("Keine Daten zum Speichern.")
        return

    result = collection.bulk_write(operations)

    print("\nMongoDB Import abgeschlossen:")
    print(f"Neue Dokumente: {result.upserted_count}")
    print(f"Aktualisierte Dokumente: {result.modified_count}")

def save_video_snapshots_to_mongodb(rows, start_date, end_date):
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[VIDEO_COLLECTION_NAME]

    now = datetime.now(timezone.utc)

    operations = []

    for row in rows:
        document = {
            **row,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "importedAt": now
        }

        operations.append(
            UpdateOne(
                {
                    "videoId": row["videoId"],
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat()
                },
                {"$set": document},
                upsert=True
            )
        )

    if not operations:
        print("Keine Video-Daten zum Speichern.")
        return

    result = collection.bulk_write(operations)

    print("\nMongoDB Video-Import abgeschlossen:")
    print(f"Neue Video-Dokumente: {result.upserted_count}")
    print(f"Aktualisierte Video-Dokumente: {result.modified_count}")

def print_video_report(rows):
    if not rows:
        print("\nKeine Video-Daten gefunden.")
        return

    print("\nVideo Analytics Report\n")

    for row in rows:
        print(f"Titel: {row.get('title', 'Unbekannter Titel')}")
        print(f"Video-ID: {row['videoId']}")
        print(f"Views: {row['views']}")
        print(f"Likes: {row['likes']}")
        print(f"Kommentare: {row['comments']}")
        print(f"Shares: {row['shares']}")
        print(f"Watchtime Minuten: {row['estimatedMinutesWatched']}")
        print(f"Durchschnittliche View-Dauer: {row['averageViewDuration']} Sekunden")

        if row["views"] > 0:
            engagement_rate = (row["likes"] + row["comments"] + row["shares"]) / row["views"]
            print(f"Engagement Rate: {engagement_rate:.4f}")

        print("-" * 40)

def print_saved_snapshots_from_mongodb():
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[DAILY_COLLECTION_NAME]

    snapshots = list(collection.find().sort("date", 1))

    if not snapshots:
        print("\nKeine gespeicherten Snapshots in MongoDB gefunden.")
        return

    print("\nGespeicherte MongoDB Snapshots:\n")

    total_views = 0
    total_likes = 0
    total_comments = 0
    total_shares = 0

    for snapshot in snapshots:
        total_views += snapshot.get("views", 0)
        total_likes += snapshot.get("likes", 0)
        total_comments += snapshot.get("comments", 0)
        total_shares += snapshot.get("shares", 0)

        print(f"Datum: {snapshot.get('date')}")
        print(f"Views: {snapshot.get('views')}")
        print(f"Likes: {snapshot.get('likes')}")
        print(f"Kommentare: {snapshot.get('comments')}")
        print(f"Shares: {snapshot.get('shares')}")
        print("-" * 40)

    print("\nZusammenfassung aus MongoDB:")
    print(f"Gesamt Views: {total_views}")
    print(f"Gesamt Likes: {total_likes}")
    print(f"Gesamt Kommentare: {total_comments}")
    print(f"Gesamt Shares: {total_shares}")

    if total_views > 0:
        engagement_rate = (total_likes + total_comments + total_shares) / total_views
        print(f"Engagement Rate: {engagement_rate:.4f}")


def print_report(rows):
    if not rows:
        print("Keine Daten gefunden.")
        return

    print("\nYouTube Analytics Report\n")

    for row in rows:
        print(f"Datum: {row['date']}")
        print(f"Views: {row['views']}")
        print(f"Likes: {row['likes']}")
        print(f"Kommentare: {row['comments']}")
        print(f"Shares: {row['shares']}")
        print(f"Watchtime Minuten: {row['estimatedMinutesWatched']}")
        print(f"Durchschnittliche View-Dauer: {row['averageViewDuration']} Sekunden")
        print("-" * 40)

def main():
    youtube_analytics, youtube_data = get_authenticated_services()

    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=30)

    response = youtube_analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date.isoformat(),
        endDate=end_date.isoformat(),
        metrics="views,likes,comments,shares,estimatedMinutesWatched,averageViewDuration",
        dimensions="day",
        sort="day"
    ).execute()

    rows = parse_report(response)

    print_report(rows)

    print("\nAls JSON-Struktur:\n")
    print(json.dumps(rows, indent=2, ensure_ascii=False))

    save_snapshots_to_mongodb(rows)

    print_saved_snapshots_from_mongodb()

    video_rows = fetch_video_report(youtube_analytics, start_date, end_date)
    video_ids = [row["videoId"] for row in video_rows]
    video_titles = fetch_video_titles(youtube_data, video_ids)
    video_rows = enrich_video_rows_with_titles(video_rows, video_titles)

    print_video_report(video_rows)

    print("\nVideo-Daten als JSON-Struktur:\n")
    print(json.dumps(video_rows, indent=2, ensure_ascii=False))

    save_video_snapshots_to_mongodb(video_rows, start_date, end_date)

if __name__ == "__main__":
    main()