# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

"""
Legacy alias module for backward compatibility.
The synthesis engine has been migrated to `senda.synthesis.extractive`.
"""

from senda.synthesis.extractive import (
    GroundedCitation,
    GroundedSynthesisResult,
    GroundedSynthesizer,
    _clean_and_truncate_snippet,
)

__all__ = [
    "GroundedCitation",
    "GroundedSynthesisResult",
    "GroundedSynthesizer",
    "_clean_and_truncate_snippet",
]
