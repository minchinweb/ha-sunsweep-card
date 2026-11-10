# Setting up Sun Sweep

Sun Sweep draws today's sunlight as a top-down wedge around your house. This
is the page linked from the integration's help view.

## Before you start

1. Install [House Structure](https://github.com/minchinweb/ha-house-structure)
   and add it. Its first form measures your building on OpenStreetMap and
   keeps the outline. Sun Sweep reads that outline. It does not look up the
   building itself.
2. Home Assistant's home location (Settings, System, General) is the place
   both integrations use. The building has to be on OpenStreetMap at that
   point. House Structure says so on its form when it cannot find one.
3. Add Sun Sweep. The form has nothing to fill in. It confirms that House
   Structure is set up and that an outline was found, then creates
   `sensor.sun_sweep`.

If House Structure is missing, or it has no building yet, Sun Sweep stops and
says which of those it is. Set House Structure up, then add Sun Sweep again.

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
| `show_times` | on | Sunrise and sunset, in your Home Assistant time format, just outside the two edges of the wedge |
| `show_moon` | on | A two-tone disc centred on the black ring at the moon's bearing, only while the moon is above the horizon |
| `show_hours` | on | A line through the wedge at each local hour the sun is up. Noon runs to the centre. 3, 6 and 9 o'clock, and the same every three hours, run further in than the others |

A black ring circles the daylight disc, the way a compass draws its edge.
North is the top of the circle, just inside that ring. The house sits in the middle, scaled so the
wedge stays visible around it. Noon is drawn across the building to the centre. Every third hour reaches further in than the hours between, so the afternoon can be counted off without reading a clock.

## How to read the wedge

The pale yellow is every direction the sun passes today, from sunrise to
sunset, in the direction the sun actually travels. North of the equator that
is clockwise through south. South of the equator it is the other way, through
north. A stronger yellow covers the part already past: from sunrise up to the
sun now. Before sunrise there is no stronger portion. After sunset the whole
wedge is the stronger yellow and the sun disc is hidden. The wedge stays, so
you can still see the day that just finished.

On a polar day the pale wedge is the full disc. On a polar night there is no
wedge and no hour lines.

The sensor's state is `above_horizon` or `below_horizon`. The card uses the
attributes (the outline in metres, the wedge, the hour bearings, and where
the sun and moon are) and does not need them copied into the card.

## When the picture is missing

The card says **House Structure has no building outline for this home yet**
when the outline has not been found, and **Sun Sweep is not set up** when the
sensor is not there. A restart picks up an outline House Structure has already
saved. House Structure fetches again when the home coordinates change, and
Sun Sweep reads the new ring within a minute.
