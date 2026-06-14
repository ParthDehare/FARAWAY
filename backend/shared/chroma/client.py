"""ChromaDB client for RailNerv Sentinel vector memory.

Connects to a ChromaDB instance and provides helpers for adding and
querying documents across the four core collections.
"""

import logging
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from .collections import COLLECTIONS

logger = logging.getLogger(__name__)

CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.environ.get("CHROMA_PORT", "8001"))


class ChromaClient:
    """Thin async-friendly wrapper around ChromaDB's HTTP client."""

    def __init__(self):
        self._client: Optional[chromadb.HttpClient] = None
        self._collections: Dict[str, Any] = {}

    def _ensure_client(self):
        if self._client is None:
            try:
                self._client = chromadb.HttpClient(
                    host=CHROMA_HOST,
                    port=CHROMA_PORT,
                    settings=Settings(
                        anonymized_telemetry=False,
                    ),
                )
                logger.info("Connected to ChromaDB at %s:%s", CHROMA_HOST, CHROMA_PORT)
            except Exception as exc:
                logger.error("Failed to connect to ChromaDB: %s", exc)
                raise

    def _get_collection(self, name: str):
        if name not in self._collections:
            self._ensure_client()
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"description": COLLECTIONS.get(name, "")},
            )
        return self._collections[name]

    async def initialize(self):
        """Create or verify all collections exist."""
        self._ensure_client()
        for col_name, description in COLLECTIONS.items():
            self._collections[col_name] = self._client.get_or_create_collection(
                name=col_name,
                metadata={"description": description},
            )
        logger.info("Initialized %d ChromaDB collections", len(COLLECTIONS))

    async def add_incident(
        self,
        collection: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """Add a document to the specified collection.

        ChromaDB generates embeddings automatically via its default
        embedding function.
        """
        col = self._get_collection(collection)
        doc_id = doc_id or str(uuid.uuid4())
        col.add(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata or {}],
        )
        return doc_id

    async def query_similar(
        self,
        collection: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[dict]:
        """Semantic search over a collection. Returns list of match dicts."""
        col = self._get_collection(collection)
        kwargs: dict = {
            "query_texts": [query_text],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where

        try:
            results = col.query(**kwargs)
        except Exception as exc:
            logger.error("ChromaDB query failed on %s: %s", collection, exc)
            return []

        matches = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc_id in enumerate(ids):
            matches.append({
                "id": doc_id,
                "document": docs[i] if i < len(docs) else "",
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            })
        return matches

    async def seed_demo_data(self):
        """Pre-seed 50 synthetic Indian Railway incidents across all collections."""
        await self.initialize()

        random.seed(42)
        base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

        # --- incidents collection -------------------------------------------
        incident_records = [
            ("Boulder landslide blocking tracks on Konkan Railway near Ratnagiri", "critical", "SEG-KNK-047", "clear", 4.5),
            ("Micro-crack detected on Delhi-Mumbai Rajdhani corridor near Kota", "warning", "SEG-DM-112", "clear", 8.0),
            ("Flat wheel vibration on Rajdhani Express 12951 near Mathura", "warning", "SEG-DM-078", "clear", 2.0),
            ("Monsoon flooding submerging tracks near Guwahati on NF Railway", "critical", "SEG-NF-023", "heavy_rain", 24.0),
            ("Obstruction detected — fallen tree on Chennai-Bangalore section", "critical", "SEG-CB-031", "storm", 3.0),
            ("Micro-crack on Howrah-Delhi main line near Mughalsarai junction", "warning", "SEG-HD-089", "clear", 6.0),
            ("Rail buckling due to extreme heat on Jodhpur-Jaisalmer section", "critical", "SEG-JJ-015", "extreme_heat", 12.0),
            ("Flat wheel alert on Deccan Queen 12123 near Lonavala ghats", "info", "SEG-MP-041", "fog", 1.5),
            ("Elephant crossing detected on track near Coimbatore", "warning", "SEG-CB-055", "clear", 0.5),
            ("Waterlogging on Mumbai suburban tracks during monsoon", "critical", "SEG-MUM-003", "heavy_rain", 18.0),
            ("Loose fishplate detected near Vijayawada junction", "warning", "SEG-VJ-022", "clear", 3.0),
            ("Cattle on track detected near Agra Cantt section", "info", "SEG-DM-095", "clear", 0.3),
            ("Flash flood warning on Kalka-Shimla narrow gauge", "critical", "SEG-KS-008", "heavy_rain", 48.0),
            ("Micro-crack pattern on Eastern Dedicated Freight Corridor", "warning", "SEG-EDFC-067", "clear", 10.0),
            ("Signal cable theft detected near Kanpur section", "critical", "SEG-HD-102", "clear", 6.0),
            ("Fog-related near miss on Lucknow-Varanasi section", "warning", "SEG-LV-019", "dense_fog", 2.0),
            ("Subsidence detected on Pamban Bridge approach", "critical", "SEG-PAM-002", "cyclone", 72.0),
            ("Minor crack on Secunderabad-Kazipet section", "info", "SEG-SK-033", "clear", 4.0),
            ("Derailment risk — uneven ballast near Itarsi junction", "warning", "SEG-IT-011", "clear", 8.0),
            ("Flooding on Samastipur-Darbhanga section during Bihar floods", "critical", "SEG-SD-007", "heavy_rain", 96.0),
        ]

        for i, (desc, severity, seg, weather, hours) in enumerate(incident_records):
            await self.add_incident(
                "incidents",
                desc,
                metadata={
                    "severity": severity,
                    "segment_id": seg,
                    "weather_condition": weather,
                    "date": (base_date + timedelta(days=i * 7)).strftime("%Y-%m-%d"),
                    "resolution_hours": hours,
                },
                doc_id=f"inc-{i+1:03d}",
            )

        # --- acoustic_signatures collection ---------------------------------
        acoustic_records = [
            ("Flat wheel rhythmic impact pattern at 0.8Hz on broad gauge", "FLAT_WHEEL", "SEG-DM-078", 0.93),
            ("High-frequency micro-crack resonance at 12kHz on welded joint", "MICRO_CRACK", "SEG-DM-112", 0.87),
            ("Low-frequency rumble consistent with boulder obstruction", "OBSTRUCTION", "SEG-KNK-047", 0.95),
            ("Normal rail-wheel contact signature — baseline reference", "NORMAL", "SEG-DM-050", 0.99),
            ("Intermittent clicking from loose fishplate vibration", "MICRO_CRACK", "SEG-VJ-022", 0.74),
            ("Double-impact pattern — flat spot on both wheels of bogie", "FLAT_WHEEL", "SEG-MP-041", 0.91),
            ("Broadband noise burst — possible foreign object on rail", "OBSTRUCTION", "SEG-CB-031", 0.82),
            ("Thermal expansion creaking — not anomalous for 47C ambient", "NORMAL", "SEG-JJ-015", 0.88),
            ("Grinding anomaly from worn crossing nose at junction", "MICRO_CRACK", "SEG-HD-089", 0.79),
            ("Impact transient consistent with rail fracture propagation", "MICRO_CRACK", "SEG-EDFC-067", 0.91),
        ]

        for i, (desc, cls, seg, conf) in enumerate(acoustic_records):
            await self.add_incident(
                "acoustic_signatures",
                desc,
                metadata={
                    "anomaly_class": cls,
                    "segment_id": seg,
                    "confidence": conf,
                    "date": (base_date + timedelta(days=i * 12)).strftime("%Y-%m-%d"),
                },
                doc_id=f"aco-{i+1:03d}",
            )

        # --- weather_patterns collection ------------------------------------
        weather_records = [
            ("Heavy monsoon rainfall 180mm/24h caused track submersion on NF Railway", "critical", "SEG-NF-023", "heavy_rain", 24.0),
            ("Cyclone Biparjoy wind damage to OHE near Bhuj section", "critical", "SEG-BHJ-005", "cyclone", 48.0),
            ("Dense fog reduced visibility to 20m on Delhi-Ambala section", "warning", "SEG-DA-014", "dense_fog", 6.0),
            ("Extreme heat 49C caused rail buckling on Rajasthan section", "critical", "SEG-JJ-015", "extreme_heat", 12.0),
            ("Lightning strike damaged signaling equipment near Bhopal", "warning", "SEG-BPL-028", "thunderstorm", 4.0),
            ("Cloud burst triggered landslide on Kalka-Shimla section", "critical", "SEG-KS-008", "heavy_rain", 72.0),
            ("Waterlogging from 120mm rainfall on Mumbai CST approaches", "critical", "SEG-MUM-003", "heavy_rain", 18.0),
            ("Dust storm reduced visibility on Jodhpur-Barmer section", "warning", "SEG-JB-009", "dust_storm", 3.0),
            ("Freezing temperature caused point machine failure in Kashmir", "warning", "SEG-KSH-001", "snow", 8.0),
            ("Moderate rain with soil erosion risk on Konkan coastal track", "warning", "SEG-KNK-047", "moderate_rain", 6.0),
        ]

        for i, (desc, severity, seg, weather, hours) in enumerate(weather_records):
            await self.add_incident(
                "weather_patterns",
                desc,
                metadata={
                    "severity": severity,
                    "segment_id": seg,
                    "weather_condition": weather,
                    "date": (base_date + timedelta(days=i * 15)).strftime("%Y-%m-%d"),
                    "resolution_hours": hours,
                },
                doc_id=f"wx-{i+1:03d}",
            )

        # --- maintenance_outcomes collection --------------------------------
        maintenance_records = [
            ("Weld repair on micro-crack — Delhi-Mumbai corridor restored in 8h", "SEG-DM-112", "weld_repair", 8.0),
            ("Wheel turning for Rajdhani coach — flat spot eliminated", "SEG-DM-078", "wheel_turning", 2.0),
            ("Boulder removal and slope stabilisation on Konkan Railway", "SEG-KNK-047", "debris_clearing", 4.5),
            ("Track relaying after flood damage on NF Railway section", "SEG-NF-023", "track_relaying", 96.0),
            ("Tree removal and OHE repair on Chennai-Bangalore section", "SEG-CB-031", "debris_clearing", 3.0),
            ("Rail replacement on heat-buckled Jodhpur section", "SEG-JJ-015", "rail_replacement", 12.0),
            ("Fishplate tightening and ultrasonic testing at Vijayawada", "SEG-VJ-022", "fastener_repair", 3.0),
            ("Ballast tamping and alignment correction at Itarsi", "SEG-IT-011", "ballast_tamping", 8.0),
            ("Emergency bridge inspection and reinforcement at Pamban", "SEG-PAM-002", "bridge_repair", 72.0),
            ("Signal cable replacement and anti-theft measures at Kanpur", "SEG-HD-102", "cable_repair", 6.0),
        ]

        for i, (desc, seg, repair_type, hours) in enumerate(maintenance_records):
            await self.add_incident(
                "maintenance_outcomes",
                desc,
                metadata={
                    "segment_id": seg,
                    "repair_type": repair_type,
                    "resolution_hours": hours,
                    "date": (base_date + timedelta(days=i * 10)).strftime("%Y-%m-%d"),
                    "success": True,
                },
                doc_id=f"mnt-{i+1:03d}",
            )

        total = len(incident_records) + len(acoustic_records) + len(weather_records) + len(maintenance_records)
        logger.info("Seeded %d demo documents across all ChromaDB collections", total)
        return total


# Module-level singleton
chroma_client = ChromaClient()
