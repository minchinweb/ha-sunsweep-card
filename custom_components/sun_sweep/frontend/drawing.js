/*
 * The card's SVG. This matches custom_components/sun_sweep/drawing.py.
 * North is up. Azimuth maps with x = cx + r * sin(azimuth), y = cy - r * cos(azimuth).
 */

const SIZE = 320;
const RING_R = 128;
const SUN_R = 8;
const MOON_R = 7;
const PALE = "#f6d84a";
const PALE_OPACITY = 0.35;
const STRONG = "#f0b429";
const STRONG_OPACITY = 0.72;
const HOUR = "#c48a12";
const TWILIGHT = "#9aafc9";
const TWILIGHT_OPACITY = 0.55;
const RING = "#111111";
const RING_HALO = "#ffffff";
const SUN_FILL = "#f5c400";
const MOON_FILL = "#c5d0dc";
const HOUSE_FILL = "#f7f4ef";
const HOUSE_STROKE = "#3d4a57";
const INK =
  'fill="var(--primary-text-color)" stroke="var(--ha-card-background, var(--card-background-color, #ffffff))" stroke-width="3" paint-order="stroke"';
const TITLE = {
  twilight: "Civil twilight",
  "twilight-dusk": "Civil twilight",
  pale: "Where the sun travels today",
  strong: "Sunlight already past",
};

const mod = (value, base) => ((value % base) + base) % base;
const clockwise = (start, end) => mod(end - start, 360);
const travel = (start, end, sunClockwise) =>
  sunClockwise ? clockwise(start, end) : clockwise(end, start);
const one = (value) => Number(value).toFixed(1);
const esc = (value) =>
  String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");

function pointAt(azimuth, radius, size = SIZE) {
  const mid = size / 2;
  const turn = (azimuth * Math.PI) / 180;
  return [mid + radius * Math.sin(turn), mid - radius * Math.cos(turn)];
}

function on(options, key) {
  return !options || options[key] !== false;
}

export function cardSvg(attrs, options = {}) {
  const size = options.size || SIZE;
  const rotation = Number(options.rotation) || 0;
  const font = options.fontFamily || "sans-serif";
  if (!attrs?.outline?.length) {
    return (
      `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" ` +
      `viewBox="0 0 ${size} ${size}" font-family="${font}" font-size="14">` +
      `<text x="${one(size / 2)}" y="${one(size / 2)}" text-anchor="middle" ${INK}>` +
      "House Structure has no building outline for this home yet.</text></svg>"
    );
  }
  let body = parts(attrs, options, size).join("");
  if (rotation) {
    const mid = one(size / 2);
    body = `<g id="rotation" transform="rotate(${one(rotation)} ${mid} ${mid})">${body}</g>`;
  }
  const box = options.embedded ? "" : ` width="${size}" height="${size}"`;
  return (
    `<svg xmlns="http://www.w3.org/2000/svg"${box} viewBox="0 0 ${size} ${size}" ` +
    `font-family="${font}" font-size="13">${body}</svg>`
  );
}

function parts(attrs, options, size) {
  const out = [];
  const ring = (RING_R * size) / SIZE;
  const sunClockwise = attrs.sun_clockwise !== false;
  if (on(options, "show_twilight")) out.push(...twilight(attrs, ring, size, sunClockwise));
  if (attrs.pale_full) {
    out.push(filled("pale", ring, PALE, PALE_OPACITY, size));
    const mid = one(size / 2);
    out.push(
      `<circle id="rim" cx="${mid}" cy="${mid}" r="${one(ring)}" fill="none" stroke="${HOUR}" stroke-width="1.5"/>`,
    );
  } else if (attrs.pale_start != null) {
    out.push(
      wedge(
        "pale",
        attrs.pale_start,
        attrs.pale_end,
        ring,
        PALE,
        PALE_OPACITY,
        size,
        sunClockwise,
      ),
    );
    out.push(arc("rim", attrs.pale_start, attrs.pale_end, ring, size, sunClockwise));
  }
  if (attrs.strong_full) {
    out.push(filled("strong", ring, STRONG, STRONG_OPACITY, size));
  } else if (attrs.strong_start != null) {
    out.push(
      wedge(
        "strong",
        attrs.strong_start,
        attrs.strong_end,
        ring,
        STRONG,
        STRONG_OPACITY,
        size,
        sunClockwise,
      ),
    );
  }
  const [house, houseRadius] = houseShape(attrs.outline, size, ring);
  if (on(options, "show_hours") && attrs.hour_azimuths?.length) {
    const lines = attrs.hour_azimuths.map((mark) => {
      const inner = hourInner(mark.time, houseRadius, ring, size);
      const hour = Number(String(mark.time).slice(0, 2));
      const width = hour === 12 ? "4" : "1.5";
      const [x1, y1] = pointAt(mark.azimuth, inner, size);
      const [x2, y2] = pointAt(mark.azimuth, ring, size);
      return (
        `<line x1="${one(x1)}" y1="${one(y1)}" x2="${one(x2)}" y2="${one(y2)}" ` +
        `stroke="${HOUR}" stroke-width="${width}"/>`
      );
    });
    out.push(`<g id="hours">${lines.join("")}</g>`);
  }
  const mid = one(size / 2);
  out.push(
    `<circle id="ring-halo" cx="${mid}" cy="${mid}" r="${one(ring)}" fill="none" stroke="${RING_HALO}" stroke-width="6"/>`,
  );
  out.push(
    `<circle id="ring" cx="${mid}" cy="${mid}" r="${one(ring)}" fill="none" stroke="${RING}" stroke-width="3"/>`,
  );
  out.push(house);
  if (on(options, "show_sun") && attrs.sun_elevation > 0) {
    const [x, y] = pointAt(attrs.sun_azimuth, ring, size);
    out.push(disc("sun", x, y, (SUN_R * size) / SIZE, SUN_FILL));
  }
  if (on(options, "show_moon") && attrs.moon_elevation > 0) {
    const [x, y] = pointAt(attrs.moon_azimuth, ring, size);
    out.push(disc("moon", x, y, (MOON_R * size) / SIZE, MOON_FILL));
  }
  if (on(options, "show_times")) out.push(...times(attrs, options, size, ring, houseRadius));
  const [nx, ny] = pointAt(0, ring - (18 * size) / SIZE, size);
  out.push(
    `<text id="north" x="${one(nx)}" y="${one(ny + 4)}" text-anchor="middle" ${INK}>N</text>`,
  );
  return out;
}

// The twilight on the two ends of the day, and none over the daylight: the
// sensor's twilight runs dawn to dusk, so drawing all of it would darken the
// pale wedge.
function twilight(attrs, ring, size, sunClockwise) {
  if (attrs.twilight_full && attrs.pale_start == null) {
    return [filled("twilight", ring, TWILIGHT, TWILIGHT_OPACITY, size)];
  }
  const start = attrs.twilight_start;
  const end = attrs.twilight_end;
  if (start == null || end == null) return [];
  const draw = (name, a, b) =>
    wedge(name, a, b, ring, TWILIGHT, TWILIGHT_OPACITY, size, sunClockwise);
  if (attrs.pale_start == null) return [draw("twilight", start, end)];
  return [
    ["twilight", start, attrs.pale_start],
    ["twilight-dusk", attrs.pale_end, end],
  ]
    .filter(([, a, b]) => travel(a, b, sunClockwise) > 0.05)
    .map(([name, a, b]) => draw(name, a, b));
}

function hourInner(clock, houseRadius, rim, size) {
  const hour = Number(String(clock).slice(0, 2));
  if (hour === 12) return 0;
  if (hour % 3 === 0) return houseRadius * 0.45;
  return Math.min(houseRadius + (6 * size) / SIZE, rim - (8 * size) / SIZE);
}

function disc(name, x, y, radius, fill) {
  const top = y - radius;
  const bottom = y + radius;
  return (
    `<g id="${name}">` +
    `<circle cx="${one(x)}" cy="${one(y)}" r="${one(radius)}" fill="${fill}"/>` +
    `<path d="M ${one(x)} ${one(top)} A ${one(radius)} ${one(radius)} 0 0 1 ` +
    `${one(x)} ${one(bottom)} Z" fill="#ffffff" fill-opacity="0.5"/>` +
    "</g>"
  );
}

function filled(name, radius, fill, opacity, size) {
  const mid = one(size / 2);
  return (
    `<circle id="${name}" cx="${mid}" cy="${mid}" r="${one(radius)}" ` +
    `fill="${fill}" fill-opacity="${opacity}"><title>${TITLE[name]}</title></circle>`
  );
}

function wedge(name, start, end, radius, fill, opacity, size, sunClockwise) {
  const span = travel(start, end, sunClockwise);
  const [x1, y1] = pointAt(start, radius, size);
  const [x2, y2] = pointAt(end, radius, size);
  const large = span > 180 ? 1 : 0;
  const sweep = sunClockwise ? 1 : 0;
  const mid = one(size / 2);
  return (
    `<path id="${name}" d="M ${mid} ${mid} L ${one(x1)} ${one(y1)} ` +
    `A ${one(radius)} ${one(radius)} 0 ${large} ${sweep} ${one(x2)} ${one(y2)} Z" ` +
    `fill="${fill}" fill-opacity="${opacity}"><title>${TITLE[name]}</title></path>`
  );
}

function arc(name, start, end, radius, size, sunClockwise) {
  const span = travel(start, end, sunClockwise);
  const [x1, y1] = pointAt(start, radius, size);
  const [x2, y2] = pointAt(end, radius, size);
  const large = span > 180 ? 1 : 0;
  const sweep = sunClockwise ? 1 : 0;
  return (
    `<path id="${name}" d="M ${one(x1)} ${one(y1)} ` +
    `A ${one(radius)} ${one(radius)} 0 ${large} ${sweep} ${one(x2)} ${one(y2)}" ` +
    `fill="none" stroke="${HOUR}" stroke-width="1.5"/>`
  );
}

function houseShape(outline, size, rim) {
  const easts = outline.map((point) => point[0]);
  const norths = outline.map((point) => point[1]);
  const span = Math.max(
    Math.max(...easts) - Math.min(...easts),
    Math.max(...norths) - Math.min(...norths),
    1e-6,
  );
  const scale = (0.42 * 2 * rim) / span;
  const mid = size / 2;
  const pts = outline.map(([east, north]) => [mid + east * scale, mid - north * scale]);
  const radius = Math.max(...pts.map(([x, y]) => Math.hypot(x - mid, y - mid)));
  const polygon = pts.map(([x, y]) => `${one(x)},${one(y)}`).join(" ");
  return [
    `<polygon id="house" points="${polygon}" fill="${HOUSE_FILL}" stroke="${HOUSE_STROKE}" stroke-width="2"/>`,
    radius,
  ];
}

function times(attrs, options, size, rim, houseRadius) {
  const labels = [];
  const sunClockwise = attrs.sun_clockwise !== false;
  const clock = options.clock || ((iso) => iso);
  for (const [key, azKey, ident] of [
    ["sunrise", "sunrise_azimuth", "sunrise"],
    ["sunset", "sunset_azimuth", "sunset"],
  ]) {
    if (!attrs[key] || attrs[azKey] == null) continue;
    const azimuth = attrs[azKey];
    const [x, y, angle] = along(azimuth, size, rim, houseRadius);
    const baseline = labelBaseline(azimuth, ident === "sunrise", sunClockwise);
    labels.push(
      `<text id="${ident}" x="${one(x)}" y="${one(y)}" text-anchor="middle" ` +
        `dominant-baseline="${baseline}" ${INK} ` +
        `transform="rotate(${one(angle)} ${one(x)} ${one(y)})">${esc(clock(attrs[key]))}</text>`,
    );
  }
  return labels;
}

function labelBaseline(azimuth, sunrise, sunClockwise) {
  const flipped = 90 < mod(azimuth - 90, 360) && mod(azimuth - 90, 360) < 270;
  const outsideIsClockwise = sunrise ? !sunClockwise : sunClockwise;
  return flipped === outsideIsClockwise ? "alphabetic" : "text-before-edge";
}

function along(azimuth, size, rim, houseRadius) {
  const outward = rim - (36 * size) / SIZE;
  const radius = Math.min(outward, Math.max(houseRadius + (16 * size) / SIZE, rim * 0.62));
  let angle = azimuth - 90;
  if (90 < mod(angle, 360) && mod(angle, 360) < 270) angle += 180;
  const [x, y] = pointAt(azimuth, radius, size);
  return [x, y, angle];
}
