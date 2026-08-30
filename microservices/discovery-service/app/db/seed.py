"""Idempotent seed for the creator index.

The discovery index is normally fed by `profile.updated` events via the
internal ingest (see routers/internal.py). Until enough real creators have
completed profiles, we seed a starter catalog so the Discover page returns live,
filterable results out of the box. Seeding is idempotent — it upserts by
`user_id` and is safe to run on every startup.

Seed rows use a reserved high user_id range (9000+) so they never collide with
real creator accounts minted by users-service.
"""
from ..schemas.discovery import CreatorIndexUpsert
from ..services import discovery as service
from .session import SessionLocal

# display_name, handle, niches, platforms, location, followers, engagement,
# rating, rate_per_post, verified
_SEED = [
    (9001, "Maya Okonkwo", "mayaokonkwo", ["Skincare", "clean skincare"],
     ["Instagram"], "Lagos, NG", 184000, 6.4, 4.9, 3200, True),
    (9002, "Dara Leigh", "daraleigh", ["Clean beauty", "clean skincare"],
     ["TikTok"], "Austin, US", 92000, 5.1, 4.7, 1900, True),
    (9003, "Renu Nair", "renu.derm", ["Derm science"],
     ["YouTube"], "Mumbai, IN", 311000, 4.2, 4.8, 4500, True),
    (9004, "Tomi Cole", "tomicole", ["Minimal skincare", "clean skincare"],
     ["Instagram"], "London, UK", 58000, 7.0, 4.5, 1400, False),
    (9005, "Amara Kealoha", "amara.k", ["SPF & sun care"],
     ["TikTok"], "Honolulu, US", 128000, 5.8, 4.6, 2600, True),
    (9006, "Jia Park", "jiapark", ["K-beauty"],
     ["Instagram"], "Seoul, KR", 246000, 4.9, 4.8, 3800, True),
    (9007, "Femi Ade", "femiade", ["Men's grooming"],
     ["YouTube"], "Accra, GH", 74000, 6.1, 4.4, 1650, False),
    (9008, "Sofia Vidal", "sofiavidal", ["Barrier repair", "clean skincare"],
     ["Instagram"], "Madrid, ES", 163000, 5.4, 4.7, 2950, True),
    (9009, "Hana Löwe", "hanalowe", ["Fragrance-free"],
     ["TikTok"], "Berlin, DE", 89000, 6.7, 4.9, 1800, True),
]


async def seed_creator_index() -> None:
    async with SessionLocal() as session:
        for (
            user_id, name, handle, niches, platforms, location,
            followers, engagement, rating, rate, verified,
        ) in _SEED:
            await service.upsert_creator_index(
                session,
                CreatorIndexUpsert(
                    user_id=user_id,
                    display_name=name,
                    handle=handle,
                    niches=niches,
                    platforms=platforms,
                    location=location,
                    follower_count=followers,
                    engagement_rate=engagement,
                    avg_rating=rating,
                    rate_per_post=rate,
                    verified=verified,
                ),
            )
