"""LLM Provider abstraction for the Oracle service.

Supports multiple providers (OpenAI, Groq) with a unified interface.
Mock data is returned for MVP but the structure is production-ready.
"""

from datetime import datetime, timezone
from typing import Literal

from app.config import get_settings
from app.schemas import OracleAdvice, OracleAdviceCategory

settings = get_settings()


class OracleProvider:
    """LLM provider for generating tactical advice.

    Abstracts the complexity of calling different LLM APIs.
    For MVP, returns structured mock data.
    """

    def __init__(
        self,
        provider: Literal["openai", "groq"] | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize the Oracle provider.

        Args:
            provider: LLM provider to use (defaults to settings)
            model: Model identifier (defaults to settings)
        """
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model

        # API keys would be used here in production
        self._openai_key = settings.openai_api_key
        self._groq_key = settings.groq_api_key

    # ==========================================================================
    # MOCK DATA - In production, this would call actual LLM APIs
    # ==========================================================================

    async def generate_matchup_advice(
        self,
        player_deck_name: str,
        opponent_deck_name: str,
        player_archetype: str,
        opponent_archetype: str,
        player_cards: list[str],
        opponent_cards: list[str],
    ) -> tuple[list[OracleAdvice], float, str]:
        """Generate tactical advice for a matchup.

        In production, this would:
        1. Build a detailed prompt with deck information
        2. Call the LLM API (OpenAI/Groq)
        3. Parse the response into structured advice

        For MVP, returns comprehensive mock data.

        Args:
            player_deck_name: Name of player's deck
            opponent_deck_name: Name of opponent's deck
            player_archetype: Player's archetype
            opponent_archetype: Opponent's archetype
            player_cards: List of player card IDs
            opponent_cards: List of opponent card IDs

        Returns:
            Tuple of (advice list, winrate prediction, difficulty level)
        """
        # Mock comprehensive advice based on archetype matchup
        matchup_key = f"{player_archetype}_vs_{opponent_archetype}"

        # Generate matchup-specific advice
        advice = self._get_mock_advice(matchup_key, player_cards, opponent_cards)
        winrate = self._get_mock_winrate(matchup_key)
        difficulty = self._get_mock_difficulty(winrate)

        return advice, winrate, difficulty

    # ==========================================================================
    # MOCK DATA GENERATORS
    # ==========================================================================

    def _get_mock_advice(
        self,
        matchup_key: str,
        player_cards: list[str],
        opponent_cards: list[str],
    ) -> list[OracleAdvice]:
        """Get comprehensive mock advice for a matchup.

        Returns an exhaustive list of advice that adapts to the matchup.
        """
        # Base advice that applies to most matchups
        base_advice = [
            OracleAdvice(
                id="gameplay-1",
                category=OracleAdviceCategory(
                    name="General Gameplay", priority="critical"
                ),
                title="Maintain elixir advantage",
                description="Always try to have at least 2 elixir more than your opponent when they make a push. This allows you to respond effectively while setting up your own counter-attack.",
                cards_involved=[],
                timing="Throughout the match",
            ),
            OracleAdvice(
                id="gameplay-2",
                category=OracleAdviceCategory(
                    name="General Gameplay", priority="high"
                ),
                title="Don't waste your primary win condition",
                description=f"Your main win condition should only be played when you have enough elixir to support it or when your opponent is low on elixir and can't punish effectively.",
                cards_involved=player_cards[:1],
                timing="After single elixir",
            ),
            OracleAdvice(
                id="gameplay-3",
                category=OracleAdviceCategory(
                    name="General Gameplay", priority="high"
                ),
                title="Track your opponent's card cycle",
                description="Keep mental (or physical) track of what cards your opponent has played. This helps you predict when they'll have their key counters available.",
                cards_involved=[],
                timing="Throughout the match",
            ),
        ]

        # Archetype-specific advice
        archetype_advice = self._get_archetype_specific_advice(
            matchup_key, player_cards, opponent_cards
        )

        # Card-specific advice
        card_advice = self._get_card_specific_advice(player_cards, opponent_cards)

        return base_advice + archetype_advice + card_advice

    def _get_archetype_specific_advice(
        self,
        matchup_key: str,
        player_cards: list[str],
        opponent_cards: list[str],
    ) -> list[OracleAdvice]:
        """Generate archetype-specific tactical advice."""
        advice_map = {
            "Beatdown_vs_Cycle": [
                OracleAdvice(
                    id="arch-beatdown-cycle-1",
                    category=OracleAdviceCategory(
                        name="Early Game", priority="critical"
                    ),
                    title="Wait for their first move",
                    description="Against cycle decks, you should almost always wait at the bridge or in the back. Let them play first so you can respond efficiently. If they don't play, you can pump in the back at ~1:45.",
                    cards_involved=[],
                    timing="First 30 seconds",
                ),
                OracleAdvice(
                    id="arch-beatdown-cycle-2",
                    category=OracleAdviceCategory(
                        name="Defense", priority="critical"
                    ),
                    title="Don't panic on their first hog",
                    description="When they cycle Hog, use your cheapest reliable defense. Save your medium spells for their supporting units. Your goal is to make their cycle inefficient.",
                    cards_involved=player_cards[2:4],
                    timing="On defense",
                ),
                OracleAdvice(
                    id="arch-beatdown-cycle-3",
                    category=OracleAdviceCategory(
                        name="2x Elixir", priority="critical"
                    ),
                    title="Force their spells before committing",
                    description="Before going all-in in 2x, make a small push or play a building to bait out their log/arrows. Once their spells are out of cycle, your main push is much stronger.",
                    cards_involved=[],
                    timing="2x elixir",
                ),
                OracleAdvice(
                    id="arch-beatdown-cycle-4",
                    category=OracleAdviceCategory(
                        name="2x Elixir", priority="high"
                    ),
                    title="Split your tanks in the back",
                    description="In 2x elixir, consider playing your win condition in one corner and another tank in the opposite corner. This splits their focus and makes cycling through answers much harder.",
                    cards_involved=player_cards[:2],
                    timing="2x elixir",
                ),
                OracleAdvice(
                    id="arch-beatdown-cycle-5",
                    category=OracleAdviceCategory(
                        name="Counter-Attack", priority="high"
                    ),
                    title="Bridge spam after successful defense",
                    description="Every time you defend their Hog efficiently, immediately bridge spam with medium troops if you have the elixir. This pressures them to defend instead of continuing their cycle.",
                    cards_involved=player_cards[3:5],
                    timing="After defense",
                ),
                OracleAdvice(
                    id="arch-beatdown-cycle-6",
                    category=OracleAdviceCategory(
                        name="Card Preservation", priority="medium"
                    ),
                    title="Never hold two of the same card",
                    description="Against cycle, holding duplicate cards makes your hand clunky. Try to avoid having two of the same card unless they're critical for defense.",
                    cards_involved=[],
                    timing="Throughout the match",
                ),
            ],
            "Control_vs_Beatdown": [
                OracleAdvice(
                    id="arch-control-beatdown-1",
                    category=OracleAdviceCategory(
                        name="Early Game", priority="critical"
                    ),
                    title="Apply early pressure",
                    description="Your beatdown opponent will wait until 2x to make their main push. You MUST apply pressure early in single elixir to force them to spend elixir on defense instead of building a massive push.",
                    cards_involved=[],
                    timing="Single elixir",
                ),
                OracleAdvice(
                    id="arch-control-beatdown-2",
                    category=OracleAdviceCategory(
                        name="Defense", priority="critical"
                    ),
                    title=" NEVER play your win condition first",
                    description="Always defend their initial commitment with your cheapest options. If you commit your X-Bow/Mortar before they commit Golem, you lose - they can simply ignore it and punish you.",
                    cards_involved=[],
                    timing="On defense",
                ),
                OracleAdvice(
                    id="arch-control-beatdown-3",
                    category=OracleAdviceCategory(
                        name="Defense", priority="critical"
                    ),
                    title="Center placement is key",
                    description="Place your defensive buildings in the center to redirect their tank. This gives your princess tower time to chip away and makes their supporting troops walk longer.",
                    cards_involved=player_cards[4:6],
                    timing="On defense",
                ),
                OracleAdvice(
                    id="arch-control-beatdown-4",
                    category=OracleAdviceCategory(
                        name="Spell Management", priority="high"
                    ),
                    title="Save your primary spell for their support",
                    description="Your spell should usually hit their witch/necro/night witch, NOT the golem itself. If you spell the golem, you waste damage - their support troops are the real threat.",
                    cards_involved=player_cards[5:7],
                    timing="On their main push",
                ),
                OracleAdvice(
                    id="arch-control-beatdown-5",
                    category=OracleAdviceCategory(
                        name="Counter-Attack", priority="critical"
                    ),
                    title="Lock your win condition IMMEDIATELY after defense",
                    description="The moment their golem dies, lock your X-Bow/Mortar. They're low on elixir after their push and can't rotate to defense fast enough.",
                    cards_involved=player_cards[:1],
                    timing="After successful defense",
                ),
                OracleAdvice(
                    id="arch-control-beatdown-6",
                    category=OracleAdviceCategory(
                        name="Tower Race", priority="high"
                    ),
                    title="Every tower chip counts",
                    description="Don't try to three-crown this matchup. Take whatever tower damage you can get with princess tower hits and small chip damage. Your win condition is tower advantage.",
                    cards_involved=[],
                    timing="Throughout the match",
                ),
                OracleAdvice(
                    id="arch-control-beatdown-7",
                    category=OracleAdviceCategory(
                        name="2x Elixir", priority="high"
                    ),
                    title="Defend from King's Tower activation",
                    description="In 2x, if your king tower activates, you can defend from the center more aggressively. However, be careful not to overcommit if they can go the other lane.",
                    cards_involved=[],
                    timing="2x elixir",
                ),
            ],
            "Cycle_vs_Siege": [
                OracleAdvice(
                    id="arch-cycle-siege-1",
                    category=OracleAdviceCategory(
                        name="Early Game", priority="critical"
                    ),
                    title="Aggressive cycle at bridge",
                    description="Siege decks want to set up their X-Bow/Mortar safely. You must constantly pressure the bridge so they can never comfortably place their win condition.",
                    cards_involved=player_cards[:3],
                    timing="From the start",
                ),
                OracleAdvice(
                    id="arch-cycle-siege-2",
                    category=OracleAdviceCategory(
                        name="Priority Target", priority="critical"
                    ),
                    title="NEVER let it lock",
                    description="If their X-Bow or Mortar locks onto your tower, you must counter immediately. Use your building or distraction troops to pull it away. One lock can lose you the game.",
                    cards_involved=[],
                    timing="Always",
                ),
                OracleAdvice(
                    id="arch-cycle-siege-3",
                    category=OracleAdviceCategory(
                        name="Spell Baiting", priority="high"
                    ),
                    title="Make them spell your building",
                    description="Place your defensive building where they must use their spell to stop it. Every spell they use on your building is one they can't use on your cycle troops.",
                    cards_involved=player_cards[4:6],
                    timing="On defense",
                ),
                OracleAdvice(
                    id="arch-cycle-siege-4",
                    category=OracleAdviceCategory(
                        name="Bridge Control", priority="high"
                    ),
                    title="Control the bridge with medium troops",
                    description="Your knight/valkyrie equivalent should sit at the bridge. This threatens their siege and forces them to play awkwardly.",
                    cards_involved=player_cards[2:4],
                    timing="Throughout the match",
                ),
                OracleAdvice(
                    id="arch-cycle-siege-5",
                    category=OracleAdviceCategory(
                        name="2x Elixir", priority="critical"
                    ),
                    title="Double lane in 2x",
                    description="In 2x elixir, pressure both lanes. They can only cover one side with their siege. This creates win conditions they can't defend.",
                    cards_involved=[],
                    timing="2x elixir",
                ),
            ],
            "Siege_vs_Control": [
                OracleAdvice(
                    id="arch-siege-control-1",
                    category=OracleAdviceCategory(
                        name="Setup", priority="critical"
                    ),
                    title="Protect your siege at all costs",
                    description="Your win condition needs support. Always have a spell or defensive troop ready to answer their immediate counter-push.",
                    cards_involved=player_cards[:2],
                    timing="During setup",
                ),
                OracleAdvice(
                    id="arch-siege-control-2",
                    category=OracleAdviceCategory(
                        name="Placement", priority="critical"
                    ),
                    title="Optimal siege placement",
                    description="Place your X-Bow/Mortar so it can hit their tower from safety but is protected by your king tower if possible. Practice the exact tile positions.",
                    cards_involved=[],
                    timing="During setup",
                ),
                OracleAdvice(
                    id="arch-siege-control-3",
                    category=OracleAdviceCategory(
                        name="Defense", priority="high"
                    ),
                    title="Minimize their chip damage",
                    description="Control decks will chip you down. Every princess tower hit matters. Use cheap troops to deny their small chip damage.",
                    cards_involved=player_cards[4:7],
                    timing="On defense",
                ),
                OracleAdvice(
                    id="arch-siege-control-4",
                    category=OracleAdviceCategory(
                        name="2x Elixir", priority="high"
                    ),
                    title="Multiple siege threats",
                    description="In 2x, consider placing two siege threats or cycling siege rapidly. They can't defend everything.",
                    cards_involved=[],
                    timing="2x elixir",
                ),
            ],
        }

        # Default advice if no specific matchup found
        default_advice = [
            OracleAdvice(
                id="arch-default-1",
                category=OracleAdviceCategory(
                    name="General Strategy", priority="high"
                ),
                title="Understand the win condition",
                description=f"Your {player_cards[0] if player_cards else 'main win condition'} should be the centerpiece of your strategy. Build your game plan around getting value from this card.",
                cards_involved=player_cards[:1],
                timing="Throughout the match",
            ),
            OracleAdvice(
                id="arch-default-2",
                category=OracleAdviceCategory(
                    name="Elixir Management", priority="high"
                ),
                title="Never reach full elixir",
                description="If you're at 10 elixir, you're wasting resources. Always be cycling cards, even if small placements, to maintain pressure and prepare your defense.",
                cards_involved=[],
                timing="Throughout the match",
            ),
            OracleAdvice(
                id="arch-default-3",
                category=OracleAdviceCategory(
                    name="2x Elixir", priority="medium"
                ),
                title="Adapt your playstyle",
                description="In 2x elixir, the matchup dynamics change. Be ready to adjust your strategy based on how single elixir went.",
                cards_involved=[],
                timing="2x elixir",
            ),
        ]

        return advice_map.get(matchup_key, default_advice)

    def _get_card_specific_advice(
        self,
        player_cards: list[str],
        opponent_cards: list[str],
    ) -> list[OracleAdvice]:
        """Generate card-specific tactical advice."""
        advice = []

        # Card-specific advice library
        card_advice_map = {
            "golem": [
                OracleAdvice(
                    id="card-golem-1",
                    category=OracleAdviceCategory(
                        name="Golem Usage", priority="critical"
                    ),
                    title="Always play Golem in the back",
                    description="Never play Golem at the bridge. You need time to build up elixir and cycle to your support cards. Back corner placement is optimal.",
                    cards_involved=["golem"],
                    timing="Single elixir",
                ),
                OracleAdvice(
                    id="card-golem-2",
                    category=OracleAdviceCategory(
                        name="Golem Usage", priority="critical"
                    ),
                    title="Predict the death damage",
                    description="When Golem dies, it deals massive death damage. Time your spells so they hit both the Golem and the death explosion radius for maximum value.",
                    cards_involved=["golem"],
                    timing="On offense",
                ),
            ],
            "hog-rider": [
                OracleAdvice(
                    id="card-hog-1",
                    category=OracleAdviceCategory(
                        name="Hog Rider Usage", priority="critical"
                    ),
                    title="Test for traps first",
                    description="Before committing to a full Hog cycle, play a small troop to check for TESLA, Bomb Tower, or other defensive buildings. Once confirmed, then commit.",
                    cards_involved=["hog-rider"],
                    timing="Early game",
                ),
                OracleAdvice(
                    id="card-hog-2",
                    category=OracleAdviceCategory(
                        name="Hog Rider Usage", priority="high"
                    ),
                    title="Bridge pressure first",
                    description="Always place a troop at the bridge before Hog Rider. This forces them to split attention and makes Hog harder to defend.",
                    cards_involved=["hog-rider"],
                    timing="During cycle",
                ),
            ],
            "mortar": [
                OracleAdvice(
                    id="card-mortar-1",
                    category=OracleAdviceCategory(
                        name="Mortar Usage", priority="critical"
                    ),
                    title="Perfect the placement",
                    description="Practice the exact tile that allows Mortar to hit tower while being safe. Being one tile off can lose you the match.",
                    cards_involved=["mortar"],
                    timing="Setup",
                ),
            ],
            "lightning": [
                OracleAdvice(
                    id="card-lightning-1",
                    category=OracleAdviceCategory(
                        name="Spell Usage", priority="high"
                    ),
                    title="Three-value lightning",
                    description="Always try to hit at least 2-3 targets with Lightning. Common targets: win condition + support tower, or 3 medium troops.",
                    cards_involved=["lightning"],
                    timing="On their push",
                ),
            ],
            "log": [
                OracleAdvice(
                    id="card-log-1",
                    category=OracleAdviceCategory(
                        name="Spell Usage", priority="medium"
                    ),
                    title="Don't overuse on goblins",
                    description="Sometimes it's better to let princess tower chip small swarms rather than Log immediately. Save Log for Barrel + Goblin Barrel stacks.",
                    cards_involved=["log"],
                    timing="On defense",
                ),
            ],
        }

        # Add relevant card advice
        for card in player_cards:
            if card in card_advice_map:
                advice.extend(card_advice_map[card])

        # Counter advice (how to play against opponent's cards)
        counter_advice_map = {
            "golem": [
                OracleAdvice(
                    id="counter-golem-1",
                    category=OracleAdviceCategory(
                        name="Countering Golem", priority="critical"
                    ),
                    title="Ignore the golem, target the support",
                    description="Never waste damage on the Golem itself. Your spells and troops should focus exclusively on the Witch, Night Witch, Mega Minion, and other support troops.",
                    cards_involved=[],
                    timing="On defense",
                ),
                OracleAdvice(
                    id="counter-golem-2",
                    category=OracleAdviceCategory(
                        name="Countering Golem", priority="critical"
                    ),
                    title="Single lane hard defense",
                    description="Commit everything to ONE lane when Golem is placed. If you split defenses, the Golem lane breaks through. Make them choose which lane to commit to.",
                    cards_involved=[],
                    timing="On their push",
                ),
                OracleAdvice(
                    id="counter-golem-3",
                    category=OracleAdviceCategory(
                        name="Countering Golem", priority="high"
                    ),
                    title="Bats for Night Witch",
                    description="When Night Witch spawns bats, have your cheap swarm or Bats ready. This prevents their bats from overwhelming your defense.",
                    cards_involved=[],
                    timing="When Golem reaches bridge",
                ),
            ],
            "hog-rider": [
                OracleAdvice(
                    id="counter-hog-1",
                    category=OracleAdviceCategory(
                        name="Countering Hog", priority="high"
                    ),
                    title="Cheap reliable defense",
                    description="Use your cheapest reliable Hog counter. Don't waste more elixir than necessary. Your goal is to gain elixir advantage from their cycle.",
                    cards_involved=[],
                    timing="On Hog",
                ),
            ],
            "elixir-golem": [
                OracleAdvice(
                    id="counter-elixir-golem-1",
                    category=OracleAdviceCategory(
                        name="Countering Elixir Golem", priority="critical"
                    ),
                    title="Let it bridge split or kite",
                    description="Let Elixir Golem bridge split if you can, or kite it with a cheap troop. When it dies, immediately clear the blobs - they deal massive tower damage.",
                    cards_involved=[],
                    timing="On defense",
                ),
            ],
        }

        for card in opponent_cards:
            if card in counter_advice_map:
                advice.extend(counter_advice_map[card])

        return advice

    def _get_mock_winrate(self, matchup_key: str) -> float:
        """Get mock winrate prediction for a matchup."""
        winrate_map = {
            "Beatdown_vs_Cycle": 52.5,
            "Cycle_vs_Beatdown": 47.5,
            "Control_vs_Beatdown": 45.0,
            "Beatdown_vs_Control": 55.0,
            "Cycle_vs_Siege": 58.0,
            "Siege_vs_Cycle": 42.0,
            "Siege_vs_Control": 48.0,
            "Control_vs_Siege": 52.0,
        }
        return winrate_map.get(matchup_key, 50.0)

    def _get_mock_difficulty(self, winrate: float) -> str:
        """Convert winrate to difficulty rating."""
        if winrate >= 60:
            return "favorable"
        if winrate >= 53:
            return "favorable"
        if winrate >= 47:
            return "even"
        if winrate >= 40:
            return "unfavorable"
        return "hard"

    # ==========================================================================
    # PRODUCTION METHODS (to be implemented with real LLM)
    # ==========================================================================

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API (production implementation).

        Args:
            prompt: Prompt to send to the LLM

        Returns:
            LLM response text
        """
        # Production implementation would use:
        # from openai import AsyncOpenAI
        # client = AsyncOpenAI(api_key=self._openai_key)
        # response = await client.chat.completions.create(...)
        raise NotImplementedError("OpenAI integration not implemented in MVP")

    async def _call_groq(self, prompt: str) -> str:
        """Call Groq API (production implementation).

        Args:
            prompt: Prompt to send to the LLM

        Returns:
            LLM response text
        """
        # Production implementation would use:
        # from groq import AsyncGroq
        # client = AsyncGroq(api_key=self._groq_key)
        # response = await client.chat.completions.create(...)
        raise NotImplementedError("Groq integration not implemented in MVP")

    def _build_matchup_prompt(
        self,
        player_deck_name: str,
        opponent_deck_name: str,
        player_archetype: str,
        opponent_archetype: str,
        player_cards: list[str],
        opponent_cards: list[str],
    ) -> str:
        """Build detailed prompt for LLM (for production use).

        Args:
            **deck and card information**

        Returns:
            Formatted prompt string
        """
        return f"""You are an expert Clash Royale strategist. Analyze the following matchup:

PLAYER DECK ({player_archetype}): {player_deck_name}
Cards: {', '.join(player_cards)}

OPPONENT DECK ({opponent_archetype}): {opponent_deck_name}
Cards: {', '.join(opponent_cards)}

Provide comprehensive tactical advice covering:
1. Early game strategy
2. Defense priorities
3. Counter-attack opportunities
4. 2x elixir strategy
5. Key cards to use/counter
6. Win conditions

Format the response as structured JSON with categories, priorities, and specific timing for each piece of advice.
"""
