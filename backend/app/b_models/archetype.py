"""ORM Model for Clash Royale deck archetypes.

An archetype is a permanent, curated structural classification of a deck.
It describes WHAT a deck is (its win condition + play style), independently
of whether it is currently strong in the meta.

Two orthogonal concepts are intentionally separated:
  - Archetype (this model): structural identity, permanent.
  - DeckMetaStatus: competitive performance, per-season, computed.

Self-referential relationship allows variant modelling:
  "Hog 2.6" and "Hog 3.0" are both variants of "Hog Cycle".
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Archetype(Base):
    """A curated Clash Royale deck archetype.

    Play styles
    -----------
    CYCLE        Low elixir, high cycle speed (e.g. Hog 2.6, Log Bait)
    BEATDOWN     High HP push supported by spells (e.g. Golem, Giant)
    CONTROL      Reactive/defense-first, small pushes (e.g. Miner Control)
    BRIDGE_SPAM  Fast deploying troops at the bridge (e.g. Ram Rider BS)
    SIEGE        Win condition stays behind the river (e.g. X-Bow, Mortar)
    HYBRID       Mix of two strategies                (e.g. LavaLoon Freeze)
    """

    __tablename__ = "archetypes"

    # -------------------------------------------------------------------------
    # Primary key
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # Identity
    # -------------------------------------------------------------------------
    # Full display name, unique. e.g. "Hog 2.6", "Hog Cycle", "Golem Beatdown"
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)

    # Slug of the primary win-condition card, e.g. "hog-rider", "golem", "x-bow"
    win_condition: Mapped[str] = mapped_column(String(50), nullable=False)

    # Structural play style (see docstring above for valid values)
    play_style: Mapped[str] = mapped_column(String(20), nullable=False)

    # -------------------------------------------------------------------------
    # Timeless flag ("Indemodable")
    # -------------------------------------------------------------------------
    # Set manually for archetypes that have persisted across many seasons/patches.
    # Orthogonal to meta_status: a timeless deck CAN simultaneously be DOMINANT.
    is_timeless: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )

    # -------------------------------------------------------------------------
    # Variant tree (self-referential adjacency list)
    # -------------------------------------------------------------------------
    # NULL  → root archetype (e.g. "Hog Cycle")
    # Set   → variant of another archetype (e.g. "Hog 2.6" → "Hog Cycle")
    variant_of_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("archetypes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # -------------------------------------------------------------------------
    # Fingerprinting data
    # -------------------------------------------------------------------------
    # Ordered list of card slugs that MUST all be present in a deck for it to
    # match this archetype. Longer list = more specific = higher priority during
    # auto-classification.
    # Example: ["hog-rider", "ice-golem", "ice-spirit", "skeletons"] → Hog 2.6
    #          ["hog-rider"] → Hog Cycle (parent, broader match)
    core_cards: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # -------------------------------------------------------------------------
    # Optional description
    # -------------------------------------------------------------------------
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # -------------------------------------------------------------------------
    # Timestamps
    # -------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(),
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    # Child variants (e.g. for "Hog Cycle": ["Hog 2.6", "Hog 3.0", ...])
    variants: Mapped[list[Archetype]] = relationship(
        "Archetype",
        back_populates="parent_archetype",
        foreign_keys="[Archetype.variant_of_id]",
    )

    # Parent archetype (e.g. for "Hog 2.6": "Hog Cycle")
    parent_archetype: Mapped[Optional[Archetype]] = relationship(
        "Archetype",
        back_populates="variants",
        foreign_keys="[Archetype.variant_of_id]",
        remote_side="[Archetype.id]",
    )

    def __repr__(self) -> str:
        timeless_marker = " ★" if self.is_timeless else ""
        return (
            f"<Archetype(id={self.id}, name='{self.name}'"
            f", play_style='{self.play_style}'{timeless_marker})>"
        )
