# Copyright (c) 2026 MinchinWeb
"""Today's sun wedge, the hour lines, the moon, and the house in local metres.

The sun comes from ``astral``, which Home Assistant ships (the same library
its ``sun.sun`` entity uses). That release of ``astral`` only has the moon's
phase, not where it is in the sky, so the moon's azimuth and elevation are
worked out here from the low-precision lunar theory on Paul Schlyter's
planetary-position page (https://www.stjarnhimlen.se/comp/ppcomp.html).
A degree or two is enough for a mark on the rim of the card.

Nothing in this module imports Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
import math

from astral import Observer
from astral.sun import azimuth, elevation, sun

METRES_PER_DEGREE = 111_320.0

# What the card is looking at.
BEFORE = "before_sunrise"
DAY = "day"
AFTER = "after_sunset"
POLAR_DAY = "polar_day"
POLAR_NIGHT = "polar_night"


def clockwise(start: float, end: float) -> float:
    """Degrees clockwise from ``start`` to ``end`` (0 when they match)."""
    return (end - start) % 360.0


def travel(start: float, end: float, sun_clockwise: bool) -> float:
    """Degrees the sun travels from ``start`` to ``end``.

    In the northern hemisphere the azimuth increases (clockwise on the card).
    In the southern hemisphere it decreases, through north.
    """
    if sun_clockwise:
        return clockwise(start, end)
    return clockwise(end, start)


def project_outline(
    points: list[tuple[float, float]] | list[list[float]],
) -> list[list[float]]:
    """The building ring as east/north metres, centred on its bounding box.

    Args:
        points: ``(latitude, longitude)`` corners, in ring order. A repeated
            closing corner is dropped.

    Returns:
        ``[east_m, north_m]`` for each corner. North is positive. Empty when
        there are fewer than three corners.
    """
    ring = [tuple(p) for p in points]
    if len(ring) >= 2 and _same(ring[0], ring[-1]):
        ring = ring[:-1]
    if len(ring) < 3:
        return []
    lat0, lon0 = ring[0]
    scale = METRES_PER_DEGREE * math.cos(math.radians(lat0))
    easts, norths = [], []
    for lat, lon in ring:
        easts.append((lon - lon0) * scale)
        norths.append((lat - lat0) * METRES_PER_DEGREE)
    cx = (min(easts) + max(easts)) / 2
    cy = (min(norths) + max(norths)) / 2
    return [
        [round(e - cx, 2), round(n - cy, 2)] for e, n in zip(easts, norths, strict=True)
    ]


def _same(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9


@dataclass(frozen=True)
class Sweep:
    """One moment's sun, moon and daylight sector."""

    phase: str
    sun_azimuth: float
    sun_elevation: float
    moon_azimuth: float
    moon_elevation: float
    sunrise: datetime | None
    sunset: datetime | None
    sunrise_azimuth: float | None
    sunset_azimuth: float | None
    hours: tuple[tuple[datetime, float], ...]
    pale: tuple[float, float, bool] | None
    strong: tuple[float, float, bool] | None
    # Civil dawn to civil dusk. Wider than the daylight sector.
    twilight: tuple[float, float, bool] | None
    # True when the sun's azimuth increases through the day (northern sky).
    sun_clockwise: bool

    def attributes(self) -> dict:
        """JSON-ready fields for the sensor. ``None`` is left out."""
        pale_start = pale_end = strong_start = strong_end = None
        twilight_start = twilight_end = None
        pale_full = strong_full = twilight_full = False
        if self.pale is not None:
            pale_start, pale_end, pale_full = self.pale
        if self.strong is not None:
            strong_start, strong_end, strong_full = self.strong
        if self.twilight is not None:
            twilight_start, twilight_end, twilight_full = self.twilight
        raw = {
            "sunrise": None if self.sunrise is None else self.sunrise.isoformat(),
            "sunset": None if self.sunset is None else self.sunset.isoformat(),
            "sun_azimuth": round(self.sun_azimuth, 1),
            "sun_elevation": round(self.sun_elevation, 1),
            "moon_azimuth": round(self.moon_azimuth, 1),
            "moon_elevation": round(self.moon_elevation, 1),
            "sunrise_azimuth": None
            if self.sunrise_azimuth is None
            else round(self.sunrise_azimuth, 1),
            "sunset_azimuth": None
            if self.sunset_azimuth is None
            else round(self.sunset_azimuth, 1),
            "hour_azimuths": [
                {"time": moment.strftime("%H:%M"), "azimuth": round(az, 1)}
                for moment, az in self.hours
            ],
            "phase": self.phase,
            "pale_start": None if pale_start is None else round(pale_start, 1),
            "pale_end": None if pale_end is None else round(pale_end, 1),
            "pale_full": pale_full,
            "strong_start": None if strong_start is None else round(strong_start, 1),
            "strong_end": None if strong_end is None else round(strong_end, 1),
            "strong_full": strong_full,
            "twilight_start": (
                None if twilight_start is None else round(twilight_start, 1)
            ),
            "twilight_end": None if twilight_end is None else round(twilight_end, 1),
            "twilight_full": twilight_full,
            "sun_clockwise": self.sun_clockwise,
        }
        return {key: value for key, value in raw.items() if value is not None}


def day_sweep(when: datetime, latitude: float, longitude: float) -> Sweep:
    """The daylight sector and the bodies at ``when``.

    Args:
        when: A timezone-aware local time. Its date is the civil day drawn.
        latitude: Degrees north.
        longitude: Degrees east.

    Returns:
        The sweep. Polar day is a full disc. Polar night has no sector and
        no hour lines. The strong portion runs from sunrise to the sun now,
        in the direction the sun travels; it is absent before sunrise and
        covers the whole sector after sunset.
    """
    observer = Observer(latitude, longitude)
    sun_az = azimuth(observer, when)
    sun_el = elevation(observer, when)
    moon_az, moon_el = moon_position(when, latitude, longitude)
    try:
        times = sun(observer, date=when.date(), tzinfo=when.tzinfo)
    except ValueError:
        return _polar(when, observer, sun_az, sun_el, moon_az, moon_el)

    rise, sett = times["sunrise"], times["sunset"]
    rise_az = azimuth(observer, rise)
    set_az = azimuth(observer, sett)
    dawn_az = azimuth(observer, times["dawn"])
    dusk_az = azimuth(observer, times["dusk"])
    sun_clockwise = _sun_clockwise(observer, rise, rise_az)
    if when < rise:
        phase = BEFORE
        strong = None
    elif when >= sett:
        phase = AFTER
        strong = (rise_az, set_az, False)
    else:
        phase = DAY
        strong = (rise_az, sun_az, False)
    return Sweep(
        phase=phase,
        sun_azimuth=sun_az,
        sun_elevation=sun_el,
        moon_azimuth=moon_az,
        moon_elevation=moon_el,
        sunrise=rise,
        sunset=sett,
        sunrise_azimuth=rise_az,
        sunset_azimuth=set_az,
        hours=_hours(
            observer, when, rise, sett, rise_az, set_az, sun_clockwise, full=False
        ),
        pale=(rise_az, set_az, False),
        strong=strong,
        twilight=(dawn_az, dusk_az, False),
        sun_clockwise=sun_clockwise,
    )


def resolve_when(now: datetime, date: str | None, clock: str | None = None) -> datetime:
    """The moment a pinned card should draw.

    Args:
        now: The live local time. Its clock is kept when ``date`` is only a day.
        date: ``YYYY-MM-DD``, or a full ISO datetime. Empty means ``now``.
        clock: ``HH:MM``, used with a bare date. Ignored when ``date`` has a time.

    Raises:
        ValueError: The date or the clock cannot be read.
    """
    if not date or not str(date).strip():
        return now
    text = str(date).strip()
    if "T" in text:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=now.tzinfo)
        return parsed
    year_s, month_s, day_s = text.split("-")
    hour, minute = now.hour, now.minute
    if clock and str(clock).strip():
        hour_s, minute_s, *_rest = str(clock).strip().split(":")
        hour, minute = int(hour_s), int(minute_s)
    return datetime(
        int(year_s), int(month_s), int(day_s), hour, minute, tzinfo=now.tzinfo
    )


def snapshot(
    when: datetime,
    latitude: float,
    longitude: float,
    points: list | None,
) -> dict:
    """Sensor attributes for ``when``, including the centred outline.

    A missing or failed outline becomes ``outline: []`` and does not raise.
    """
    attrs = day_sweep(when, latitude, longitude).attributes()
    attrs["outline"] = project_outline(points or [])
    return attrs


def _polar(when, observer, sun_az, sun_el, moon_az, moon_el) -> Sweep:
    """A day with no sunrise: a full disc, or nothing, by the noon elevation."""
    noon = when.replace(hour=12, minute=0, second=0, microsecond=0)
    if elevation(observer, noon) > 0:
        midnight = when.replace(hour=0, minute=0, second=0, microsecond=0)
        midnight_az = azimuth(observer, midnight)
        return Sweep(
            phase=POLAR_DAY,
            sun_azimuth=sun_az,
            sun_elevation=sun_el,
            moon_azimuth=moon_az,
            moon_elevation=moon_el,
            sunrise=None,
            sunset=None,
            sunrise_azimuth=None,
            sunset_azimuth=None,
            hours=_hours(observer, when, None, None, 0.0, 0.0, True, full=True),
            pale=(0.0, 360.0, True),
            strong=(midnight_az, sun_az, False),
            twilight=None,
            sun_clockwise=_sun_clockwise(observer, midnight, midnight_az),
        )
    return Sweep(
        phase=POLAR_NIGHT,
        sun_azimuth=sun_az,
        sun_elevation=sun_el,
        moon_azimuth=moon_az,
        moon_elevation=moon_el,
        sunrise=None,
        sunset=None,
        sunrise_azimuth=None,
        sunset_azimuth=None,
        hours=(),
        pale=None,
        strong=None,
        twilight=None,
        sun_clockwise=True,
    )


def _sun_clockwise(observer, start: datetime, start_azimuth: float) -> bool:
    """True when the azimuth increases as time does, as it does north of the equator."""
    later = azimuth(observer, start + timedelta(minutes=20))
    return clockwise(start_azimuth, later) <= clockwise(later, start_azimuth)


def _hours(
    observer, when, rise, sett, rise_az, set_az, sun_clockwise, *, full: bool
) -> tuple[tuple[datetime, float], ...]:
    """Local clock hours today at which the sun is above the horizon."""
    found = []
    for hour in range(24):
        try:
            moment = datetime.combine(when.date(), time(hour), tzinfo=when.tzinfo)
        except ValueError:
            continue  # a clock hour that doesn't exist on a DST change
        if not full and (moment < rise or moment > sett):
            continue
        if elevation(observer, moment) <= 0:
            continue
        place = azimuth(observer, moment)
        if not full and not _on_arc(rise_az, set_az, place, sun_clockwise):
            continue
        found.append((moment, place))
    return tuple(found)


def _on_arc(
    start: float, end: float, point: float, sun_clockwise: bool, tol: float = 0.5
) -> bool:
    return (
        travel(start, point, sun_clockwise) <= travel(start, end, sun_clockwise) + tol
    )


def moon_position(
    when: datetime, latitude: float, longitude: float
) -> tuple[float, float]:
    """The moon's compass azimuth and elevation, in degrees.

    Azimuth is clockwise from north. Elevation is negative below the horizon.
    Geocentric, so it can be about a degree off a rooftop observer.

    Args:
        when: The moment (timezone-aware).
        latitude: Degrees north.
        longitude: Degrees east.
    """
    jd = _julian_day(when)
    d = jd - 2451543.5

    def wrap(deg: float) -> float:
        return deg % 360.0

    n = wrap(125.1228 - 0.0529538083 * d)
    incl = 5.1454
    w = wrap(318.0634 + 0.1643573223 * d)
    a = 60.2666
    ecc = 0.054900
    m = wrap(115.3654 + 13.0649929509 * d)
    eccentric = math.radians(m)
    for _ in range(8):
        eccentric = eccentric - (
            eccentric - ecc * math.sin(eccentric) - math.radians(m)
        ) / (1 - ecc * math.cos(eccentric))
    xv = a * (math.cos(eccentric) - ecc)
    yv = a * math.sqrt(1 - ecc * ecc) * math.sin(eccentric)
    v = math.degrees(math.atan2(yv, xv))
    r = math.hypot(xv, yv)
    vw = math.radians(v + w)
    node = math.radians(n)
    tilt = math.radians(incl)
    xh = r * (
        math.cos(node) * math.cos(vw) - math.sin(node) * math.sin(vw) * math.cos(tilt)
    )
    yh = r * (
        math.sin(node) * math.cos(vw) + math.cos(node) * math.sin(vw) * math.cos(tilt)
    )
    zh = r * math.sin(vw) * math.sin(tilt)
    lonecl = math.degrees(math.atan2(yh, xh)) % 360.0
    latecl = math.degrees(math.atan2(zh, math.hypot(xh, yh)))

    sun_m = wrap(356.0470 + 0.9856002585 * d)
    sun_l = wrap(sun_m + 282.9404 + 4.70935e-5 * d)
    moon_l = wrap(n + w + m)
    elong = wrap(moon_l - sun_l)
    node_dist = wrap(moon_l - n)
    lonecl, latecl = _perturb(lonecl, latecl, m, sun_m, elong, node_dist)

    obl = math.radians(23.4393 - 3.563e-7 * d)
    lam = math.radians(lonecl)
    beta = math.radians(latecl)
    xeq = math.cos(beta) * math.cos(lam)
    yeq = math.cos(beta) * math.sin(lam) * math.cos(obl) - math.sin(beta) * math.sin(
        obl
    )
    zeq = math.cos(beta) * math.sin(lam) * math.sin(obl) + math.sin(beta) * math.cos(
        obl
    )
    ra = math.atan2(yeq, xeq)
    dec = math.atan2(zeq, math.hypot(xeq, yeq))
    gmst = wrap(280.46061837 + 360.98564736629 * (jd - 2451545.0))
    lst = math.radians(wrap(gmst + longitude))
    return _horizontal(dec, lst - ra, math.radians(latitude))


def _perturb(lon, lat, m, sun_m, elong, node_dist):
    """The larger periodic terms, in degrees, on the ecliptic place."""

    def s(*parts: float) -> float:
        return math.sin(math.radians(sum(parts)))

    lon += (
        -1.274 * s(m, -2 * elong)
        + 0.658 * s(2 * elong)
        - 0.186 * s(sun_m)
        - 0.059 * s(2 * m, -2 * elong)
        - 0.057 * s(m, -2 * elong, sun_m)
        + 0.053 * s(m, 2 * elong)
        + 0.046 * s(2 * elong, -sun_m)
        + 0.041 * s(m, -sun_m)
        - 0.035 * s(elong)
        - 0.031 * s(m, sun_m)
        - 0.015 * s(2 * node_dist, -2 * elong)
        + 0.011 * s(m, -4 * elong)
    )
    lat += (
        -0.173 * s(node_dist, -2 * elong)
        - 0.055 * s(m, -node_dist, -2 * elong)
        - 0.046 * s(m, node_dist, -2 * elong)
        + 0.033 * s(node_dist, 2 * elong)
        + 0.017 * s(2 * m, node_dist)
    )
    return lon % 360.0, lat


def _horizontal(dec: float, hour_angle: float, latitude: float) -> tuple[float, float]:
    """Azimuth clockwise from north, and elevation, from equatorial angles.

    All arguments are radians. This is the NOAA solar-position conversion.
    """
    sin_alt = math.sin(dec) * math.sin(latitude) + math.cos(dec) * math.cos(
        latitude
    ) * math.cos(hour_angle)
    sin_alt = max(-1.0, min(1.0, sin_alt))
    alt = math.degrees(math.asin(sin_alt))
    az = math.degrees(
        math.atan2(
            math.sin(hour_angle),
            math.cos(hour_angle) * math.sin(latitude)
            - math.tan(dec) * math.cos(latitude),
        )
    )
    return (az + 180.0) % 360.0, alt


def _julian_day(when: datetime) -> float:
    """Julian day, including the fraction of the UT day."""
    when = when.astimezone(UTC)
    year, month = when.year, when.month
    if month <= 2:
        year -= 1
        month += 12
    century = year // 100
    gregorian = 2 - century + century // 4
    day = (
        when.day
        + when.hour / 24
        + when.minute / 1440
        + (when.second + when.microsecond / 1e6) / 86400
    )
    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + gregorian
        - 1524.5
    )
