# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""Senda search provider adapters and multi-source aggregator."""

from senda.providers.base import SearchProvider, SearchResultItem
from senda.providers.internal import InternalStorageProvider
from senda.providers.searxng import SearXNGProvider
from senda.providers.brave import BraveSearchProvider
from senda.providers.mojeek import MojeekProvider
from senda.providers.openalex import OpenAlexProvider
from senda.providers.aggregator import ProviderAggregator, BANG_SHORTCUTS

__all__ = [
    "SearchProvider",
    "SearchResultItem",
    "InternalStorageProvider",
    "SearXNGProvider",
    "BraveSearchProvider",
    "MojeekProvider",
    "OpenAlexProvider",
    "ProviderAggregator",
    "BANG_SHORTCUTS",
]
