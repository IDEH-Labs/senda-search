# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 IDEH Labs <https://ideh.top>

import datetime
from senda.astronomy import calculate_moon_phase, MoonPhaseInfo


def test_moon_phase_known_epochs():
    # Epoch New Moon: 2000-01-06 18:14 UTC
    epoch = datetime.datetime(2000, 1, 6, 18, 14, 0, tzinfo=datetime.timezone.utc)
    phase = calculate_moon_phase(epoch)
    assert phase.code == "new_moon"
    assert phase.name == "Luna nueva"
    assert phase.illumination_pct == 0

    # ~ 7.38 days later: First Quarter
    first_q = epoch + datetime.timedelta(days=7.38)
    p_fq = calculate_moon_phase(first_q)
    assert p_fq.code == "first_quarter"
    assert p_fq.name == "Cuarto creciente"
    assert 45 <= p_fq.illumination_pct <= 55

    # ~ 14.76 days later: Full Moon
    full = epoch + datetime.timedelta(days=14.76)
    p_full = calculate_moon_phase(full)
    assert p_full.code == "full_moon"
    assert p_full.name == "Luna llena"
    assert 95 <= p_full.illumination_pct <= 100

    # ~ 22.14 days later: Last Quarter
    last_q = epoch + datetime.timedelta(days=22.14)
    p_lq = calculate_moon_phase(last_q)
    assert p_lq.code == "last_quarter"
    assert p_lq.name == "Cuarto menguante"
    assert 45 <= p_lq.illumination_pct <= 55


def test_moon_phase_today():
    now = datetime.datetime.now(datetime.timezone.utc)
    phase = calculate_moon_phase(now)
    assert isinstance(phase, MoonPhaseInfo)
    assert phase.code in (
        "new_moon", "waxing_crescent", "first_quarter", "waxing_gibbous",
        "full_moon", "waning_gibbous", "last_quarter", "waning_crescent"
    )
    assert 0 <= phase.illumination_pct <= 100
    assert 0.0 <= phase.age_days <= 29.6
