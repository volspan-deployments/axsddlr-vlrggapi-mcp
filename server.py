from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
import threading
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

mcp = FastMCP("vlrggapi")

BASE_URL = "https://vlrggapi.vercel.app"


@mcp.tool()
async def get_news() -> dict:
    """Fetch the latest Valorant esports news articles from vlr.gg. Use this when the user asks about recent news, announcements, or updates in the Valorant esports scene."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/v2/news")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_matches(q: str) -> dict:
    """
    Fetch Valorant esports match information from vlr.gg. Use this to get live scores, upcoming matches, match results, or extended upcoming match details.

    Args:
        q: Type of match data to retrieve. Options: 'live_score' (currently live matches with scores), 'upcoming' (scheduled upcoming matches), 'results' (recent match results), 'upcoming_extended' (upcoming matches with additional details).
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/v2/match", params={"q": q})
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_rankings(region: str) -> dict:
    """
    Fetch current Valorant esports team rankings from vlr.gg. Use this when the user wants to know team standings or rankings for a specific region.

    Args:
        region: The region to get rankings for. Common values: 'na' (North America), 'eu' (Europe), 'ap' (Asia Pacific), 'la' (Latin America), 'br' (Brazil), 'kr' (Korea), 'cn' (China), 'gc' (Game Changers), 'collegiate', 'mena'.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/v2/rankings", params={"region": region})
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_stats(timespan: Optional[str] = "60d", region: Optional[str] = "all") -> dict:
    """
    Fetch Valorant esports player statistics from vlr.gg. Use this to get aggregated player performance stats filtered by time period and/or region.

    Args:
        timespan: Time period for stats. Options: '30d' (last 30 days), '60d' (last 60 days), '90d' (last 90 days), 'all' (all time). Defaults to '60d'.
        region: Region filter for stats. Options: 'all', 'na', 'eu', 'ap', 'la', 'br', 'kr', 'cn', 'gc', 'mena'. Defaults to 'all'.
    """
    params = {}
    if timespan:
        params["timespan"] = timespan
    if region:
        params["region"] = region

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/v2/stats", params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_events(q: str) -> dict:
    """
    Fetch Valorant esports events from vlr.gg. Use this when the user wants to know about upcoming, ongoing, or completed tournaments and events.

    Args:
        q: Type of events to retrieve. Options: 'upcoming' (future events), 'live' (currently ongoing events), 'completed' (past events).
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/v2/events", params={"q": q})
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_match_detail(id: str) -> dict:
    """
    Fetch detailed information about a specific Valorant esports match from vlr.gg. Use this when the user wants in-depth stats for a particular match, including per-map player stats (K/D/A, ACS, rating), round-by-round data, kill matrix, and economy breakdown.

    Args:
        id: The vlr.gg match ID. Found in vlr.gg match URLs, e.g. for 'https://vlr.gg/12345/team-a-vs-team-b' the ID is '12345'.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/v2/match/{id}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_player(id: int, timespan: Optional[str] = "all") -> dict:
    """
    Fetch a Valorant esports player's profile from vlr.gg. Use this to get agent statistics, current and past team history, event placements, total winnings, and match history for a specific player.

    Args:
        id: The vlr.gg player ID. Found in vlr.gg player profile URLs, e.g. for 'https://vlr.gg/player/9/tenz' the ID is 9.
        timespan: Time period for player stats. Options: '30d', '60d', '90d', 'all'. Defaults to 'all'.
    """
    params = {"id": id}
    if timespan:
        params["timespan"] = timespan

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/v2/player", params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_team(id: int) -> dict:
    """
    Fetch a Valorant esports team's profile from vlr.gg. Use this to get a team's roster with roles and captain status, VLR rating and rank, event placements, total winnings, match history, and roster transactions.

    Args:
        id: The vlr.gg team ID. Found in vlr.gg team page URLs, e.g. for 'https://vlr.gg/team/2/sentinels' the ID is 2.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/v2/team", params={"id": id})
        response.raise_for_status()
        return response.json()




_SERVER_SLUG = "axsddlr-vlrggapi"

def _track(tool_name: str, ua: str = ""):
    try:
        import urllib.request, json as _json
        data = _json.dumps({"slug": _SERVER_SLUG, "event": "tool_call", "tool": tool_name, "user_agent": ua}).encode()
        req = urllib.request.Request("https://www.volspan.dev/api/analytics/event", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=1)
    except Exception:
        pass

async def health(request):
    return JSONResponse({"status": "ok", "server": mcp.name})

async def tools(request):
    registered = await mcp.list_tools()
    tool_list = [{"name": t.name, "description": t.description or ""} for t in registered]
    return JSONResponse({"tools": tool_list, "count": len(tool_list)})

sse_app = mcp.http_app(transport="sse")

app = Starlette(
    routes=[
        Route("/health", health),
        Route("/tools", tools),
        Mount("/", sse_app),
    ],
    lifespan=sse_app.lifespan,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
