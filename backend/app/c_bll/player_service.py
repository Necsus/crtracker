"""Player business logic layer."""

import re
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.a_dal.battle_dal import BattleDAL
from app.a_dal.player_dal import PlayerDAL
from app.b_models.battle import Battle
from app.b_models.player import Player
from app.clients.cr_client import CRApiError, fetch_battles, fetch_player

# Regex for a valid CR tag fragment (letters + digits, 3+ chars, no #)
_TAG_RE = re.compile(r"^[0-9A-Z]{2,}$")

# Auto-refresh player from CR API if data is older than this
_PLAYER_REFRESH_SECONDS = 3 * 60  # 3 minutes


class PlayerService:
    def __init__(self, session: AsyncSession, cr_token: str):
        self.dal = PlayerDAL(session)
        self.battle_dal = BattleDAL(session)
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
        """Return the player from DB, fetching from CR API if absent or stale (> 3 min).
        Also syncs the battle log whenever a CR API refresh happens.
        """
        player = await self.dal.get_by_tag(tag)
        if player is None:
            raw = await fetch_player(tag, self.cr_token)
            data = _parse_cr_player(raw)
            player = await self.dal.upsert(data)
            await self._sync_battles(tag)
            return player

        age = (datetime.now(timezone.utc) - player.last_synced_at).total_seconds()
        if age > _PLAYER_REFRESH_SECONDS:
            try:
                raw = await fetch_player(tag, self.cr_token)
                data = _parse_cr_player(raw)
                player = await self.dal.upsert(data)
                await self._sync_battles(tag)
            except CRApiError:
                pass  # fallback to existing DB data if CR API fails

        return player

    async def _sync_battles(self, tag: str) -> None:
        """Fetch battlelog from CR API and upsert new battles into DB."""
        try:
            raw_battles = await fetch_battles(tag, self.cr_token)
        except CRApiError:
            return
        normalized_tag = tag.strip().upper().lstrip("#")
        battles = [_parse_cr_battle(normalized_tag, b) for b in raw_battles]
        await self.battle_dal.upsert_many(battles)

    async def list_battles(self, tag: str, limit: int = 25) -> list[Battle]:
        normalized_tag = tag.strip().upper().lstrip("#")
        return await self.battle_dal.list_by_player_tag(normalized_tag, limit=limit)


def _parse_cr_battle(player_tag: str, raw: dict) -> dict:
    """Map a raw CR API battle dict to Battle model fields."""
    team = raw.get("team") or [{}]
    opponent = raw.get("opponent") or [{}]
    me = team[0] if team else {}
    opp = opponent[0] if opponent else {}

    battle_time_raw: str = raw.get("battleTime", "")
    # Parse CR format: "20260101T001122.000Z" → datetime
    try:
        battle_time = datetime.strptime(battle_time_raw, "%Y%m%dT%H%M%S.%fZ").replace(tzinfo=timezone.utc)
    except ValueError:
        battle_time = datetime.now(timezone.utc)

    my_crowns = me.get("crowns", 0) or 0
    opp_crowns = opp.get("crowns", 0) or 0
    if my_crowns > opp_crowns:
        result = "win"
    elif my_crowns < opp_crowns:
        result = "loss"
    else:
        result = "draw"

    opp_tag = (opp.get("tag") or "").lstrip("#")

    return {
        "player_tag": player_tag,
        "battle_key": f"{player_tag}_{battle_time_raw}",
        "battle_time": battle_time,
        "battle_type": raw.get("type"),
        "game_mode_name": (raw.get("gameMode") or {}).get("name"),
        "arena_name": (raw.get("arena") or {}).get("name"),
        "result": result,
        "trophy_change": me.get("trophyChange"),
        "player_crowns": my_crowns,
        "opponent_tag": opp_tag or None,
        "opponent_name": opp.get("name"),
        "opponent_crowns": opp_crowns,
        "opponent_trophies": opp.get("startingTrophies"),
        "player_cards": me.get("cards"),
        "opponent_cards": opp.get("cards"),
        "raw_data": raw,
    }


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
