# Setting up Sun Sweep

Sun Sweep draws today's sunlight as a top-down wedge around your house. This
is the page linked from the integration's help view.

## Before you start

1. Home Assistant's home location (Settings, System, General) is the place
   the sun and moon are calculated for.
2. Add Sun Sweep. The form has nothing to fill in. It creates
   `sensor.sun_sweep`.
3. Optional: install
   [House Structure](https://github.com/minchinweb/ha-house-structure) and
   add it. Its first form measures your building on OpenStreetMap and keeps
   the outline. Sun Sweep reads that outline. It does not look up the
   building itself. The building has to be on OpenStreetMap at your home
   location. House Structure says so on its form when it cannot find one.

Without a building outline the card draws a 10 m square and says so
underneath. That is true when House Structure is not installed, and when it
is installed but has not found a building yet. Sun Sweep still sets up, and
it picks up an outline House Structure saves later.

## The card

Add a card on a dashboard:

```yaml
type: custom:sun-sweep-card
entity: sensor.sun_sweep
```

Or pick **Sun Sweep** in the card picker. The picker only lists it after
this integration is added and the browser has loaded the card, so reload
the page once if you have just finished setup. The visual editor can point the card
at the sensor and turn each of these on or off. Leaving one out is the same
as leaving it on.

| Option | Default | What you get |
| --- | --- | --- |
| `entity` | `sensor.sun_sweep` | The sensor this integration creates |
| `show_sun` | on | A two-tone yellow disc centred on the black ring at the sun's compass bearing, only while the sun is above the horizon |
| `show_times` | on | Sunrise and sunset, in your Home Assistant time format, written just outside the two edges of the wedge, with each edge as the baseline |
| `show_moon` | on | A two-tone disc centred on the black ring at the moon's bearing, only while the moon is above the horizon |
| `show_hours` | on | A line through the wedge at each local hour the sun is up. Noon runs to the centre and is drawn heavier than the three-hour lines. Every third hour runs further in. The house is drawn on top, so the lines stop at the walls and noon still reads as the heavy spoke |
| `show_twilight` | on | A blue-grey wedge on each side of the day: civil dawn to sunrise, and sunset to civil dusk. The daylight keeps its own colour |
| `rotation` | `0` | Degrees clockwise to turn the whole card. `0` keeps north at the top. Useful when a tablet is mounted sideways. Negative turns anticlockwise. The editor's slider runs from -360 to 360, and YAML takes any number |
| `date` | | Pin the card to `YYYY-MM-DD`, a full ISO datetime, `march-equinox`, `june-solstice`, `september-equinox`, or `december-solstice` (this year, at home). `spring`, `summer`, `autumn`, and `winter` follow the home hemisphere: summer is June in the north and December in the south. The sensor itself stays live. Leave this out for today. While a date is set, the card says which day it is holding |
| `time` | | `HH:MM` on that date. Without it, the card uses the current clock time on the chosen day. The editor shows this once a date is set, and hides it when that date already includes a time |
| `tap_action` | none | What a tap does. `more-info`, `navigate`, `url`, `toggle`, `perform-action`, or `none`. None leaves the picture alone |

A black ring circles the disc, and the daylight and twilight wedges run out to it.
North is the top of the circle, just inside that ring. The house sits in the middle, scaled so the
wedge stays visible around it. Noon and every third hour are drawn further in than the other hours. Noon is the heavy stroke. The house covers the part of a line that falls inside the walls.

## How to read the wedge

Either side of the yellow, a blue-grey wedge runs from civil dawn to
sunrise and from sunset to civil dusk. Turn
it off with `show_twilight: false`. The pale yellow is every direction the sun passes today, from sunrise to
sunset, in the direction the sun actually travels. North of the equator that
is clockwise through south. South of the equator it is the other way, through
north. A stronger yellow covers the part already past: from sunrise up to the
sun now. Before sunrise there is no stronger portion. After sunset the whole
wedge is the stronger yellow and the sun disc is hidden. The wedge stays, so
you can still see the day that just finished.

On a polar day the pale wedge is the full disc. On a polar night there is no
wedge and no hour lines.

To hold the picture on one moment, for a screenshot or while checking the
drawing, set `date` and optionally `time`:

```yaml
type: custom:sun-sweep-card
date: september-equinox
time: "15:00"
```

The pictures in the readme are rendered with `python scripts/render_card.py`.
That writes the June morning, the winter afternoon, the hour after sunset,
the same morning turned 40 degrees, and the 10 m square. One extra picture
is `python scripts/render_card.py --date 2026-06-21 --time 09:30 --name preview`.

The main sensor's state is `above_horizon` or `below_horizon`. Two more
sensors on the same device are `Sunrise azimuth` and `Sunset azimuth`, in
degrees clockwise from north. On a polar day or polar night those two have
no value. The card uses the attributes (the outline in metres, the wedge,
the hour bearings, and where the sun and moon are) and does not need them
copied into the card.

## When the picture is missing

The card says **Sun Sweep is not set up** when the sensor is not there.
With no building outline it draws the square. While you add or edit the
card, a note underneath says whether House Structure is missing or has not
found a building yet. On the live dashboard that note is hidden. A
restart picks up an outline House Structure has already saved. House
Structure fetches again when the home coordinates change, and Sun Sweep
reads the new ring within a minute. The card appears in the dashboard
picker after Sun Sweep is added. Reload the page if the picker was already
open.
