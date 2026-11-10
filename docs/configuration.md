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

Without House Structure the card draws a 10 m square and says so underneath.
If House Structure is installed but has not found a building yet, Sun Sweep
stops on its form and the card says the outline is missing. Set House
Structure up at this home, then add Sun Sweep again.

## The card

Add a card on a dashboard:

```yaml
type: custom:sun-sweep-card
entity: sensor.sun_sweep
```

Or pick **Sun Sweep** in the card picker. The visual editor can point the card
at the sensor and turn each of these on or off. Leaving one out is the same
as leaving it on.

| Option | Default | What you get |
| --- | --- | --- |
| `entity` | `sensor.sun_sweep` | The sensor this integration creates |
| `show_sun` | on | A two-tone yellow disc centred on the black ring at the sun's compass bearing, only while the sun is above the horizon |
| `show_times` | on | Sunrise and sunset, in your Home Assistant time format, written along the two edges of the wedge |
| `show_moon` | on | A two-tone disc centred on the black ring at the moon's bearing, only while the moon is above the horizon |
| `show_hours` | on | A line through the wedge at each local hour the sun is up. Noon runs to the centre. Every third hour runs further in. The house is drawn on top, so the lines do not show inside the walls |
| `show_twilight` | on | A blue-grey wedge from civil dawn to civil dusk, drawn under the daylight. What shows is the twilight on either side of the day |
| `rotation` | `0` | Degrees clockwise to turn the whole card. `0` keeps north at the top. Useful when a tablet is mounted sideways |
| `date` | | Pin the card to `YYYY-MM-DD`, a full ISO datetime, `march-equinox`, or `september-equinox` (this year, at home). The sensor itself stays live. Leave this out for today |
| `time` | | `HH:MM` on that date. Without it, the card uses the current clock time on the chosen day |

A black ring circles the disc, and the daylight and twilight wedges run out to it.
North is the top of the circle, just inside that ring. The house sits in the middle, scaled so the
wedge stays visible around it. Noon and every third hour are drawn further in than the other hours, and the house covers the part of a line that falls inside the walls.

## How to read the wedge

Under the yellow, a blue-grey wedge runs from civil dawn to civil dusk. Turn
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

The sensor's state is `above_horizon` or `below_horizon`. The card uses the
attributes (the outline in metres, the wedge, the hour bearings, and where
the sun and moon are) and does not need them copied into the card.

## When the picture is missing

The card says **House Structure has no building outline for this home yet**
when House Structure is installed but the outline has not been found, and
**Sun Sweep is not set up** when the sensor is not there. With no House
Structure integration at all, the card draws the square instead. A restart picks up an outline House Structure has already
saved. House Structure fetches again when the home coordinates change, and
Sun Sweep reads the new ring within a minute.
