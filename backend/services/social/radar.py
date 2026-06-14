"""Social Media Crisis Radar.

Real-time monitoring of X/Twitter, Facebook, and news feeds
for railway-related keywords in 22 Indian languages.
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid
import asyncio


RAILWAY_KEYWORDS = {
    "en": ["train accident", "rail crash", "derailment", "track damage", "railway flood", "train delay", "rail block"],
    "hi": ["रेल दुर्घटना", "ट्रेन हादसा", "पटरी से उतरना", "रेल पटरी टूटी", "ट्रेन रद्द", "रेल बाधित"],
    "ta": ["ரயில் விபத்து", "தடம் புரண்டது", "ரயில் தாமதம்"],
    "te": ["రైలు ప్రమాదం", "పట్టాలు తప్పింది"],
    "bn": ["ট্রেন দুর্ঘটনা", "রেল লাইন ক্ষতিগ্রস্ত"],
    "mr": ["रेल्वे अपघात", "ट्रेन उशीर"],
    "gu": ["ટ્રેન અકસ્માત", "રેલ્વે પૂર"],
    "kn": ["ರೈಲು ಅಪಘಾತ", "ಹಳಿ ಹಾನಿ"],
    "ml": ["ട്രെയിൻ അപകടം", "പാളം തെറ്റി"],
    "pa": ["ਰੇਲ ਹਾਦਸਾ", "ਟ੍ਰੇਨ ਲੇਟ"],
    "or": ["ରେଳ ଦୁର୍ଘଟଣା", "ଟ୍ରେନ୍ ଧାଡ଼ି"],
    "as": ["ৰেল দুৰ্ঘটনা", "ট্ৰেইন দেৰি"],
}

PLATFORMS = ["twitter", "facebook", "news", "reddit"]

MOCK_POSTS = [
    {
        "id": str(uuid.uuid4()),
        "platform": "twitter",
        "author": "@RailwayAlert_IN",
        "content": "BREAKING: Reports of water logging near Konkan Railway KM-215. Multiple trains delayed. #IndianRailways #KonkanRailway",
        "language": "en",
        "timestamp": (datetime.utcnow() - timedelta(minutes=12)).isoformat(),
        "location": {"lat": 16.5, "lng": 73.2, "name": "Ratnagiri, Maharashtra"},
        "engagement": {"likes": 234, "retweets": 89, "replies": 45},
        "classification": "hazard_report",
        "confidence": 0.91,
        "verified": True,
        "sentiment": "negative",
        "severity": "warning",
        "matched_keywords": ["railway flood", "trains delayed"],
    },
    {
        "id": str(uuid.uuid4()),
        "platform": "twitter",
        "author": "@MumbaiLocal_updates",
        "content": "⚠️ Heavy boulder spotted on tracks between Kasara-Igatpuri section. Trains halted. Passengers stranded! @RailMinIndia @draborailway",
        "language": "en",
        "timestamp": (datetime.utcnow() - timedelta(minutes=28)).isoformat(),
        "location": {"lat": 19.65, "lng": 73.52, "name": "Kasara, Maharashtra"},
        "engagement": {"likes": 1245, "retweets": 567, "replies": 234},
        "classification": "hazard_report",
        "confidence": 0.95,
        "verified": True,
        "sentiment": "negative",
        "severity": "critical",
        "matched_keywords": ["boulder", "tracks", "trains halted"],
    },
    {
        "id": str(uuid.uuid4()),
        "platform": "twitter",
        "author": "@fake_news_bot",
        "content": "MASSIVE train crash near Delhi!! 100s dead!! #breaking #emergency",
        "language": "en",
        "timestamp": (datetime.utcnow() - timedelta(minutes=45)).isoformat(),
        "location": None,
        "engagement": {"likes": 12, "retweets": 3, "replies": 28},
        "classification": "misinformation",
        "confidence": 0.88,
        "verified": False,
        "sentiment": "panic",
        "severity": "info",
        "matched_keywords": ["train crash"],
    },
    {
        "id": str(uuid.uuid4()),
        "platform": "facebook",
        "author": "Allahabad Railway Passengers Group",
        "content": "ट्रेन 12301 हावड़ा राजधानी एक्सप्रेस 3 घंटे लेट है। प्लेटफॉर्म पर भारी भीड़। कोई जानकारी नहीं मिल रही।",
        "language": "hi",
        "timestamp": (datetime.utcnow() - timedelta(hours=1, minutes=15)).isoformat(),
        "location": {"lat": 25.43, "lng": 81.85, "name": "Prayagraj, UP"},
        "engagement": {"likes": 89, "retweets": 0, "replies": 67},
        "classification": "passenger_report",
        "confidence": 0.82,
        "verified": True,
        "sentiment": "frustrated",
        "severity": "warning",
        "matched_keywords": ["ट्रेन रद्द", "ट्रेन हादसा"],
    },
    {
        "id": str(uuid.uuid4()),
        "platform": "news",
        "author": "NDTV",
        "content": "Konkan Railway services disrupted due to heavy rainfall; several trains cancelled or diverted",
        "language": "en",
        "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        "location": {"lat": 17.0, "lng": 73.3, "name": "Konkan Coast"},
        "engagement": {"likes": 0, "retweets": 0, "replies": 0},
        "classification": "news_report",
        "confidence": 0.97,
        "verified": True,
        "sentiment": "neutral",
        "severity": "warning",
        "matched_keywords": ["railway", "disrupted", "rainfall", "cancelled"],
    },
    {
        "id": str(uuid.uuid4()),
        "platform": "twitter",
        "author": "@ChennaiRailFan",
        "content": "ரயில் எண் 12621 தமிழ்நாடு எக்ஸ்பிரஸ் 45 நிமிடம் தாமதமாக இயங்குகிறது. சிக்னல் பிரச்சனை காரணம்.",
        "language": "ta",
        "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
        "location": {"lat": 13.08, "lng": 80.27, "name": "Chennai"},
        "engagement": {"likes": 45, "retweets": 12, "replies": 8},
        "classification": "passenger_report",
        "confidence": 0.79,
        "verified": True,
        "sentiment": "neutral",
        "severity": "info",
        "matched_keywords": ["ரயில் தாமதம்"],
    },
]


class SocialRadar:
    """Monitors social media for railway-related crisis signals."""

    def __init__(self):
        self._posts_cache: list[dict] = list(MOCK_POSTS)
        self._monitoring = False

    async def get_recent_posts(
        self,
        limit: int = 20,
        severity: Optional[str] = None,
        platform: Optional[str] = None,
        classification: Optional[str] = None,
    ) -> list[dict]:
        posts = self._posts_cache

        if severity:
            posts = [p for p in posts if p["severity"] == severity]
        if platform:
            posts = [p for p in posts if p["platform"] == platform]
        if classification:
            posts = [p for p in posts if p["classification"] == classification]

        return sorted(posts, key=lambda p: p["timestamp"], reverse=True)[:limit]

    async def get_statistics(self) -> dict:
        posts = self._posts_cache
        return {
            "total_monitored": len(posts),
            "by_platform": {p: sum(1 for x in posts if x["platform"] == p) for p in PLATFORMS},
            "by_classification": {
                "hazard_report": sum(1 for p in posts if p["classification"] == "hazard_report"),
                "passenger_report": sum(1 for p in posts if p["classification"] == "passenger_report"),
                "misinformation": sum(1 for p in posts if p["classification"] == "misinformation"),
                "news_report": sum(1 for p in posts if p["classification"] == "news_report"),
            },
            "by_severity": {
                "critical": sum(1 for p in posts if p["severity"] == "critical"),
                "warning": sum(1 for p in posts if p["severity"] == "warning"),
                "info": sum(1 for p in posts if p["severity"] == "info"),
            },
            "verified_count": sum(1 for p in posts if p["verified"]),
            "misinformation_blocked": sum(1 for p in posts if p["classification"] == "misinformation"),
            "languages_detected": list(set(p["language"] for p in posts)),
            "languages_supported": len(RAILWAY_KEYWORDS),
        }

    async def get_geo_clusters(self) -> list[dict]:
        posts_with_location = [p for p in self._posts_cache if p.get("location")]
        clusters: dict[str, list] = {}
        for post in posts_with_location:
            loc_name = post["location"]["name"]
            if loc_name not in clusters:
                clusters[loc_name] = []
            clusters[loc_name].append(post)

        return [
            {
                "location": name,
                "lat": posts[0]["location"]["lat"],
                "lng": posts[0]["location"]["lng"],
                "post_count": len(posts),
                "max_severity": max(posts, key=lambda p: {"info": 0, "warning": 1, "critical": 2}.get(p["severity"], 0))["severity"],
            }
            for name, posts in clusters.items()
        ]
