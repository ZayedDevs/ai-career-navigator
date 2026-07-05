
import os
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

from ..utils.db import get_collection

load_dotenv()

"""
Purpose:
    Fetch top YouTube tutorial videos for a given skill, with MongoDB caching
    to minimize API quota usage.
"""


# ============================================================================
# CONFIGURATION
# ============================================================================

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
RESULTS_PER_SKILL = int(os.getenv("YOUTUBE_RESULTS_PER_SKILL", 3))
CACHE_DAYS = int(os.getenv("YOUTUBE_CACHE_DAYS", 7))

CACHE_COLLECTION_NAME = "youtube_cache"


# ============================================================================
# LAZY-LOADED YOUTUBE CLIENT
# ============================================================================

@lru_cache(maxsize=1)
def get_youtube_client():
    """Build the YouTube API client (cached singleton)."""
    if not YOUTUBE_API_KEY:
        raise RuntimeError(
            "YOUTUBE_API_KEY not found in environment. "
            "Add it to backend/.env"
        )
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


# ============================================================================
# CACHE HELPERS
# ============================================================================

def get_cache_collection():
    """Get the MongoDB collection for YouTube cache."""
    return get_collection(CACHE_COLLECTION_NAME)


def get_cached_videos(skill: str) -> list | None:
    """
    Try to get cached videos for a skill.
    Returns None if cache miss or expired.
    """
    try:
        collection = get_cache_collection()
        cached = collection.find_one({"skill": skill.lower()})

        if not cached:
            return None

        # Check if cache is expired
        cached_at = cached.get("cached_at")
        if not cached_at:
            return None

        # Use timezone-aware UTC datetime (Python 3.12+ best practice)
        now = datetime.now(timezone.utc)
        # cached_at may be naive if stored before this fix
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        age = now - cached_at
        if age > timedelta(days=CACHE_DAYS):
            return None  # Expired

        return cached.get("videos", [])

    except Exception as e:
        # If cache fails, just bypass it (don't break the request)
        print(f"⚠️ Cache read failed for '{skill}': {e}")
        return None


def save_to_cache(skill: str, videos: list) -> None:
    """Save fetched videos to MongoDB cache."""
    try:
        collection = get_cache_collection()
        collection.update_one(
            {"skill": skill.lower()},
            {
                "$set": {
                    "skill": skill.lower(),
                    "videos": videos,
                    "cached_at": datetime.now(timezone.utc),
                    "video_count": len(videos),
                }
            },
            upsert=True,
        )
    except Exception as e:
        print(f"⚠️ Cache write failed for '{skill}': {e}")


# ============================================================================
# YOUTUBE API CALL
# ============================================================================

def _fetch_from_youtube(skill: str) -> list:
    """
    Call YouTube Data API to fetch top videos for a skill.

    Cost: 100 quota units per call.

    Returns:
        List of video dicts with title, channel, url, etc.
    """
    youtube = get_youtube_client()

    # Build a smart query — "<skill> tutorial" tends to return courses
    query = f"{skill} tutorial"

    try:
        response = youtube.search().list(
            q=query,
            part="snippet",
            maxResults=RESULTS_PER_SKILL,
            type="video",
            order="relevance",       # could also use 'viewCount' or 'rating'
            relevanceLanguage="en",  # English content only
        ).execute()

    except HttpError as e:
        print(f"⚠️ YouTube API error for '{skill}': {e}")
        return []

    # Extract clean video data
    videos = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        video_id = item.get("id", {}).get("videoId", "")

        if not video_id:
            continue

        videos.append({
            "title": snippet.get("title", ""),
            "channel": snippet.get("channelTitle", ""),
            "description": snippet.get("description", "")[:200],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
            "published_at": snippet.get("publishedAt", ""),
            "platform": "YouTube",
            "type": "free",
        })

    return videos


# ============================================================================
# PUBLIC API
# ============================================================================

def get_youtube_resources(skill: str, force_refresh: bool = False) -> list:
    """
    Get YouTube tutorial videos for a skill, with MongoDB caching.

    Args:
        skill:         The skill name (e.g., "pytorch")
        force_refresh: If True, bypass cache and fetch fresh data

    Returns:
        List of up to RESULTS_PER_SKILL video dicts. Empty list if API fails.
    """
    skill_normalized = skill.lower().strip()

    # 1. Check cache first (unless forced refresh)
    if not force_refresh:
        cached = get_cached_videos(skill_normalized)
        if cached is not None:
            return cached

    # 2. Cache miss → call YouTube API
    videos = _fetch_from_youtube(skill_normalized)

    # 3. Save to cache (even if empty, to avoid hammering API on failures)
    save_to_cache(skill_normalized, videos)

    return videos


def get_cache_stats() -> dict:
    """Return statistics about the YouTube cache."""
    try:
        collection = get_cache_collection()
        total = collection.count_documents({})

        # Recent (within cache TTL)
        cutoff = datetime.now(timezone.utc) - timedelta(days=CACHE_DAYS)
        fresh = collection.count_documents({"cached_at": {"$gte": cutoff}})

        return {
            "total_cached_skills": total,
            "fresh_entries": fresh,
            "expired_entries": total - fresh,
            "cache_ttl_days": CACHE_DAYS,
        }
    except Exception as e:
        return {"error": str(e)}


def clear_cache() -> int:
    """
    Clear all cached YouTube data. Returns number of entries deleted.
    Useful for testing.
    """
    try:
        collection = get_cache_collection()
        result = collection.delete_many({})
        return result.deleted_count
    except Exception as e:
        print(f"⚠️ Clear cache failed: {e}")
        return 0


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    """
    Test runner: fetch videos for a sample skill.

    Usage:
        python -m app.services.youtube_fetcher
    """
    print("\n" + "=" * 70)
    print("  YOUTUBE FETCHER — TEST")
    print("=" * 70)

    # Show cache stats
    stats = get_cache_stats()
    print(f"\nCache stats before test:")
    print(f"  {stats}")

    # Test with 3 skills
    test_skills = ["python", "pytorch", "kubernetes"]

    for skill in test_skills:
        print(f"\n{'─' * 70}")
        print(f"  Fetching: '{skill}'")
        print(f"{'─' * 70}")

        # First call → may hit API or cache
        videos = get_youtube_resources(skill)

        if not videos:
            print(f"  ⚠️ No videos returned (check API key + internet)")
            continue

        print(f"  ✓ Got {len(videos)} videos:")
        for i, v in enumerate(videos, 1):
            print(f"\n    {i}. {v['title'][:60]}")
            print(f"       Channel: {v['channel']}")
            print(f"       URL:     {v['url']}")

    # Show cache stats again
    stats = get_cache_stats()
    print(f"\n{'=' * 70}")
    print(f"Cache stats after test:")
    print(f"  {stats}")
    print(f"{'=' * 70}")

    # Test cache hit (second call should be from cache)
    print(f"\nTesting cache (calling 'python' again — should be instant):")
    import time
    start = time.time()
    videos = get_youtube_resources("python")
    elapsed = (time.time() - start) * 1000
    print(f"  Got {len(videos)} videos in {elapsed:.1f}ms (cached = <50ms)")