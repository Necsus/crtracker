"""Player business logic layer."""

import re
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.player_dal import PlayerDAL
from app.b_models.player import Player
from app.clients.cr_client import CRApiError, fetch_player

# Regex for a valid CR tag fragment (letters + digits, 3+ chars, no #)
_TAG_RE = re.compile(r"^[0-9A-Z]{2,}$")


class PlayerService:
    def __init__(self, session: AsyncSession, cr_token: str):
        self.dal = PlayerDAL(session)
        self.cr_token = cr_token

    async def list_top(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[Player], int]:
        players = await self.dal.list_top(limit, offset)
        total = await self.dal.count()
        return players, total

    async def search(self, query: str) -> tuple[list[Player], str]:
        """Search players in DB first; fall back to CR API for tag-like queries.

        Returns:
            (players, source) where source is 'db' or 'api'.
        """
        q = query.strip()
        if not q:
            return [], "db"

        is_tag = q.startswith("#") or _TAG_RE.match(q.upper().lstrip("#"))

        if is_tag:
            # Exact tag match first
            exact = await self.dal.get_by_tag(q)
            if exact:
                return [exact], "db"

            # Partial tag match in DB
            db_results = await self.dal.search_by_tag_fragment(q, limit=10)
            if db_results:
                return db_results, "db"

            # CR API fallback — exact tag lookup
            try:
                raw = await fetch_player(q, self.cr_token)
                data = _parse_cr_player(raw)
                player = await self.dal.upsert(data)
                return [player], "api"
            except CRApiError as exc:
                if exc.status_code == 404:
                    return [], "db"
                raise
        else:
            db_results = await self.dal.search_by_name(q, limit=10)
            return db_results, "db"

    async def get_or_fetch(self, tag: str) -> Player:
        """Return the player from DB, fetching from CR API and saving if absent."""
        player = await self.dal.get_by_tag(tag)
        if player:
            return player
        raw = await fetch_player(tag, self.cr_token)
        data = _parse_cr_player(raw)
        return await self.dal.upsert(data)


def _parse_cr_player(raw: dict) -> dict:
    """Map a raw CR API response dict to Player model fields."""
    clan = raw.get("clan") or {}
    arena = raw.get("arena") or {}
    pol = raw.get("pathOfLegend") or {}

    return {
        "tag": raw.get("tag", "").lstrip("#"),
        "name": raw.get("name", ""),
        "exp_level": raw.get("expLevel", 0),
        "exp_points": raw.get("expPoints"),
        "total_exp_points": raw.get("totalExpPoints"),
        "star_points": raw.get("starPoints"),
        "trophies": raw.get("trophies", 0),
        "best_trophies": raw.get("bestTrophies", 0),
        "legacy_trophy_road_high_score": raw.get("legacyTrophyRoadHighScore"),
        "wins": raw.get("wins", 0),
        "losses": raw.get("losses", 0),
        "battle_count": raw.get("battleCount", 0),
        "three_crown_wins": raw.get("threeCrownWins", 0),
        "challenge_cards_won": raw.get("challengeCardsWon"),
        "challenge_max_wins": raw.get("challengeMaxWins"),
        "tournament_cards_won": raw.get("tournamentCardsWon"),
        "tournament_battle_count": raw.get("tournamentBattleCount"),
        "war_day_wins": raw.get("warDayWins"),
        "clan_cards_collected": raw.get("clanCardsCollected"),
        "donations": raw.get("donations"),
        "donations_received": raw.get("donationsReceived"),
        "total_donations": raw.get("totalDonations"),
        "clan_tag": (clan.get("tag") or "").lstrip("#") or None,
        "clan_name": clan.get("name"),
        "clan_badge_id": clan.get("badgeId"),
        "role": raw.get("role"),
        "arena_id": arena.get("id"),
        "arena_name": arena.get("name"),
        "pol_league_number": pol.get("leagueNumber"),
        "pol_trophies": pol.get("trophies"),
        "pol_rank": pol.get("rank"),
        "current_deck": raw.get("currentDeck"),
        "current_favourite_card": raw.get("currentFavouriteCard"),
        "league_statistics": raw.get("leagueStatistics"),
        "badges": raw.get("badges"),
        "achievements": raw.get("achievements"),
        "raw_data": raw,
        "last_synced_at": datetime.now(timezone.utc),
    }
