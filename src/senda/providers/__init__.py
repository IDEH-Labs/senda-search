# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Senda search provider adapters and multi-source aggregator."""

from senda.providers.base import (
    SearchProvider,
    SearchResultItem,
    RetractionInfo,
    VerificationItem,
    SourceScoreInfo,
    AIProvenance,
)
from senda.providers.internal import InternalStorageProvider
from senda.providers.searxng import SearXNGProvider
from senda.providers.brave import BraveSearchProvider
from senda.providers.mojeek import MojeekProvider
from senda.providers.openalex import OpenAlexProvider
from senda.providers.crossref import CrossrefProvider
from senda.providers.arxiv import ArxivProvider
from senda.providers.doaj import DoajProvider
from senda.providers.pubmed import PubMedProvider
from senda.providers.fediverse import FediverseProvider
from senda.providers.bluesky import BlueskyProvider
from senda.providers.wikipedia import WikipediaEntityCard, WikipediaEntityProvider
from senda.providers.aggregator import ProviderAggregator, BANG_SHORTCUTS

__all__ = [
    "SearchProvider",
    "SearchResultItem",
    "RetractionInfo",
    "VerificationItem",
    "SourceScoreInfo",
    "AIProvenance",
    "InternalStorageProvider",
    "SearXNGProvider",
    "BraveSearchProvider",
    "MojeekProvider",
    "OpenAlexProvider",
    "CrossrefProvider",
    "ArxivProvider",
    "DoajProvider",
    "PubMedProvider",
    "FediverseProvider",
    "BlueskyProvider",
    "WikipediaEntityCard",
    "WikipediaEntityProvider",
    "ProviderAggregator",
    "BANG_SHORTCUTS",
]
