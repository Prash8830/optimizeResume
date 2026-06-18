import time

from fastapi import APIRouter

from app.utils.llm import get_llm_logs

router = APIRouter()


@router.get("/stats")
async def get_stats():
    logs = get_llm_logs()
    now = time.time()

    def window(seconds: float) -> list[dict]:
        return [l for l in logs if now - l["timestamp"] < seconds]

    day = window(86400)
    week = window(604800)

    providers: dict[str, int] = {}
    endpoints: dict[str, int] = {}
    errors = 0
    total_dur = 0

    for l in day:
        providers[l["provider"]] = providers.get(l["provider"], 0) + 1
        endpoints[l["endpoint"]] = endpoints.get(l["endpoint"], 0) + 1
        if not l["success"]:
            errors += 1
        total_dur += l["duration_ms"]

    # Build time-series buckets (last 24h, 1 bucket per hour)
    buckets = []
    for h in range(23, -1, -1):
        t0 = now - (h + 1) * 3600
        t1 = now - h * 3600
        count = sum(1 for l in logs if t0 <= l["timestamp"] < t1)
        buckets.append({"hour": 23 - h, "count": count})

    return {
        "total_24h": len(day),
        "total_7d": len(week),
        "total_all": len(logs),
        "providers_24h": providers,
        "endpoints_24h": endpoints,
        "error_rate_24h": round(errors / max(len(day), 1), 3),
        "avg_duration_ms": round(total_dur / max(len(day), 1)),
        "timeline": buckets,
        "recent": logs[:50],
    }
