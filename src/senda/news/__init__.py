# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""News syndication and ClaimReview fact-checking module for Senda."""

from senda.news.feed_reader import NewsFeedReader, FeedItem
from senda.news.claim_review import ClaimReviewParser, ClaimReviewRegistry

__all__ = [
    "NewsFeedReader",
    "FeedItem",
    "ClaimReviewParser",
    "ClaimReviewRegistry",
]
