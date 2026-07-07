from fastapi import FastAPI
from pymongo import MongoClient
from bson import ObjectId
from fastapi.responses import Response
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST


MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "shortspulse"
DAILY_COLLECTION_NAME = "analytics_snapshots"
VIDEO_COLLECTION_NAME = "video_analytics_snapshots"
shortspulse_daily_snapshots = Gauge(
    "shortspulse_daily_snapshots",
    "Number of daily analytics snapshots stored in MongoDB"
)

shortspulse_video_snapshots = Gauge(
    "shortspulse_video_snapshots",
    "Number of video analytics snapshots stored in MongoDB"
)

shortspulse_total_views = Gauge(
    "shortspulse_total_views",
    "Total views from stored daily snapshots"
)

shortspulse_total_likes = Gauge(
    "shortspulse_total_likes",
    "Total likes from stored daily snapshots"
)

shortspulse_total_comments = Gauge(
    "shortspulse_total_comments",
    "Total comments from stored daily snapshots"
)

shortspulse_total_shares = Gauge(
    "shortspulse_total_shares",
    "Total shares from stored daily snapshots"
)

shortspulse_engagement_rate = Gauge(
    "shortspulse_engagement_rate",
    "Engagement rate calculated as (likes + comments + shares) / views"
)

shortspulse_video_views = Gauge(
    "shortspulse_video_views",
    "Views per YouTube video",
    ["video_id", "title"]
)

shortspulse_video_likes = Gauge(
    "shortspulse_video_likes",
    "Likes per YouTube video",
    ["video_id", "title"]
)

shortspulse_video_comments = Gauge(
    "shortspulse_video_comments",
    "Comments per YouTube video",
    ["video_id", "title"]
)


app = FastAPI(title="ShortsPulse API")


def serialize_document(document):
    document["_id"] = str(document["_id"])
    return document


def get_db():
    client = MongoClient(MONGO_URI)
    return client[DATABASE_NAME]

def update_prometheus_metrics():
    db = get_db()
    daily_collection = db[DAILY_COLLECTION_NAME]
    video_collection = db[VIDEO_COLLECTION_NAME]

    daily_snapshots = list(daily_collection.find())
    video_snapshots = list(video_collection.find())

    total_views = sum(item.get("views", 0) for item in daily_snapshots)
    total_likes = sum(item.get("likes", 0) for item in daily_snapshots)
    total_comments = sum(item.get("comments", 0) for item in daily_snapshots)
    total_shares = sum(item.get("shares", 0) for item in daily_snapshots)

    engagement_rate = 0

    if total_views > 0:
        engagement_rate = (total_likes + total_comments + total_shares) / total_views

    shortspulse_daily_snapshots.set(len(daily_snapshots))
    shortspulse_video_snapshots.set(len(video_snapshots))
    shortspulse_total_views.set(total_views)
    shortspulse_total_likes.set(total_likes)
    shortspulse_total_comments.set(total_comments)
    shortspulse_total_shares.set(total_shares)
    shortspulse_engagement_rate.set(engagement_rate)

    shortspulse_video_views.clear()
    shortspulse_video_likes.clear()
    shortspulse_video_comments.clear()

    for video in video_snapshots:
        video_id = video.get("videoId", "unknown")
        title = video.get("title", "unknown")

        shortspulse_video_views.labels(
            video_id=video_id,
            title=title
        ).set(video.get("views", 0))

        shortspulse_video_likes.labels(
            video_id=video_id,
            title=title
        ).set(video.get("likes", 0))

        shortspulse_video_comments.labels(
            video_id=video_id,
            title=title
        ).set(video.get("comments", 0))


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "ShortsPulse API"
    }


@app.get("/daily")
def get_daily_snapshots():
    db = get_db()
    collection = db[DAILY_COLLECTION_NAME]

    snapshots = list(collection.find().sort("date", 1))

    return [serialize_document(snapshot) for snapshot in snapshots]


@app.get("/videos")
def get_video_snapshots():
    db = get_db()
    collection = db[VIDEO_COLLECTION_NAME]

    videos = list(collection.find().sort("views", -1))

    return [serialize_document(video) for video in videos]


@app.get("/summary")
def get_summary():
    db = get_db()
    daily_collection = db[DAILY_COLLECTION_NAME]
    video_collection = db[VIDEO_COLLECTION_NAME]

    daily_snapshots = list(daily_collection.find())
    video_snapshots = list(video_collection.find())

    total_views = sum(item.get("views", 0) for item in daily_snapshots)
    total_likes = sum(item.get("likes", 0) for item in daily_snapshots)
    total_comments = sum(item.get("comments", 0) for item in daily_snapshots)
    total_shares = sum(item.get("shares", 0) for item in daily_snapshots)

    engagement_rate = 0

    if total_views > 0:
        engagement_rate = (total_likes + total_comments + total_shares) / total_views

    top_video = None

    if video_snapshots:
        top_video = max(video_snapshots, key=lambda item: item.get("views", 0))
        top_video = serialize_document(top_video)

    return {
        "dailySnapshotCount": len(daily_snapshots),
        "videoSnapshotCount": len(video_snapshots),
        "totalViews": total_views,
        "totalLikes": total_likes,
        "totalComments": total_comments,
        "totalShares": total_shares,
        "engagementRate": round(engagement_rate, 4),
        "topVideo": top_video
    }

@app.get("/metrics")
def metrics():
    update_prometheus_metrics()

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )