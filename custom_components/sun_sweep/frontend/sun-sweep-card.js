/*
 * Sun Sweep: the house, top down, over today's sun wedge.
 * The shapes match custom_components/sun_sweep/drawing.py.
 */
import { LitElement, css, html, svg } from "lit";

const DOCS =
  "https://github.com/minchinweb/ha-sunsweep-card/blob/master/docs/configuration.md";
const SIZE = 320;
const RIM = 112;
const RING_R = 128;
const PALE = "#f6d84a";
const STRONG = "#f0b429";
const HOUR = "#c48a12";
const RING = "#111111";

const clockwise = (start, end) => (end - start + 360) % 360;
const travel = (start, end, sunClockwise) =>
  sunClockwise ? clockwise(start, end) : clockwise(end, start);

function pointAt(azimuth, radius, size = SIZE) {
  const mid = size / 2;
  const turn = (azimuth * Math.PI) / 180;
  return [mid + radius * Math.sin(turn), mid - radius * Math.cos(turn)];
}

function wedge(id, start, end, radius, fill, opacity, sunClockwise) {
  const span = travel(start, end, sunClockwise);
  const [x1, y1] = pointAt(start, radius);
  const [x2, y2] = pointAt(end, radius);
  const large = span > 180 ? 1 : 0;
  const sweep = sunClockwise ? 1 : 0;
  const mid = SIZE / 2;
  const d = `M ${mid} ${mid} L ${x1.toFixed(1)} ${y1.toFixed(1)} A ${radius} ${radius} 0 ${large} ${sweep} ${x2.toFixed(1)} ${y2.toFixed(1)} Z`;
  return svg`<path id=${id} d=${d} fill=${fill} fill-opacity=${opacity}></path>`;
}

function arc(start, end, radius, sunClockwise) {
  const span = travel(start, end, sunClockwise);
  const [x1, y1] = pointAt(start, radius);
  const [x2, y2] = pointAt(end, radius);
  const large = span > 180 ? 1 : 0;
  const sweep = sunClockwise ? 1 : 0;
  const d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} A ${radius} ${radius} 0 ${large} ${sweep} ${x2.toFixed(1)} ${y2.toFixed(1)}`;
  return svg`<path id="rim" d=${d} fill="none" stroke=${HOUR} stroke-width="1.5"></path>`;
}

function hourInner(time, houseRadius) {
  const hour = Number(String(time).slice(0, 2));
  if (hour === 12) return 0;
  if (hour % 3 === 0) return houseRadius * 0.45;
  return Math.min(houseRadius + 6, RIM - 8);
}

function disc(id, x, y, radius, fill) {
  const cx = x.toFixed(1);
  const top = (y - radius).toFixed(1);
  const bottom = (y + radius).toFixed(1);
  const d = `M ${cx} ${top} A ${radius} ${radius} 0 0 1 ${cx} ${bottom} Z`;
  return svg`<g id=${id}><circle cx=${cx} cy=${y.toFixed(1)} r=${radius} fill=${fill}></circle><path d=${d} fill="#ffffff" fill-opacity="0.5"></path></g>`;
}

function labelAt(azimuth) {
  for (const radius of [RIM + 16, RIM - 20]) {
    const [x, y] = pointAt(azimuth, radius);
    if (x >= 40 && x <= SIZE - 40 && y >= 12 && y <= SIZE - 8) return [x, y];
  }
  return pointAt(azimuth, RIM - 20);
}

class SunSweepCard extends LitElement {
  static properties = { hass: {}, config: {} };

  static styles = css`
    :host { display: block; }
    svg { width: 100%; height: auto; display: block; }
    .message {
      padding: 16px;
      text-align: center;
      color: var(--primary-text-color);
    }
    text { fill: var(--primary-text-color); font-family: sans-serif; font-size: 13px; }
  `;

  static getConfigElement() {
    return document.createElement("sun-sweep-card-editor");
  }

  static getStubConfig() {
    return { entity: "sensor.sun_sweep" };
  }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    this.config = config;
  }

  _on(key) {
    return this.config[key] !== false;
  }

  _clock(iso) {
    const cycle = this.hass?.locale?.time_format;
    const hour12 = cycle === "12" ? true : cycle === "24" ? false : undefined;
    return new Date(iso).toLocaleTimeString(this.hass?.locale?.language, {
      hour: "numeric",
      minute: "2-digit",
      hour12,
    });
  }

  _picture(attrs) {
    const sunClockwise = attrs.sun_clockwise !== false;
    const parts = [];
    if (attrs.pale_full) {
      parts.push(svg`<circle id="pale" cx="160" cy="160" r=${RIM} fill=${PALE} fill-opacity="0.35"></circle>`);
      parts.push(svg`<circle id="rim" cx="160" cy="160" r=${RIM} fill="none" stroke=${HOUR} stroke-width="1.5"></circle>`);
    } else if (attrs.pale_start != null) {
      parts.push(wedge("pale", attrs.pale_start, attrs.pale_end, RIM, PALE, 0.35, sunClockwise));
      parts.push(arc(attrs.pale_start, attrs.pale_end, RIM, sunClockwise));
    }
    parts.push(svg`<circle id="ring" cx="160" cy="160" r=${RING_R} fill="none" stroke=${RING} stroke-width="3"></circle>`);
    if (attrs.strong_full) {
      parts.push(svg`<circle id="strong" cx="160" cy="160" r=${RIM} fill=${STRONG} fill-opacity="0.72"></circle>`);
    } else if (attrs.strong_start != null) {
      parts.push(wedge("strong", attrs.strong_start, attrs.strong_end, RIM, STRONG, 0.72, sunClockwise));
    }
    const outline = attrs.outline;
    const easts = outline.map((p) => p[0]);
    const norths = outline.map((p) => p[1]);
    const span = Math.max(
      Math.max(...easts) - Math.min(...easts),
      Math.max(...norths) - Math.min(...norths),
      1e-6,
    );
    const scale = (0.42 * 2 * RIM) / span;
    const house = outline.map(([east, north]) => [
      SIZE / 2 + east * scale,
      SIZE / 2 - north * scale,
    ]);
    const houseRadius = Math.max(
      ...house.map(([x, y]) => Math.hypot(x - SIZE / 2, y - SIZE / 2)),
    );
    const points = house.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
    parts.push(svg`<polygon id="house" points=${points} fill="#f7f4ef" stroke="#3d4a57" stroke-width="2"></polygon>`);
    if (this._on("show_hours") && attrs.hour_azimuths?.length) {
      const lines = attrs.hour_azimuths.map((mark) => {
        const inner = hourInner(mark.time, houseRadius);
        const [x1, y1] = pointAt(mark.azimuth, inner);
        const [x2, y2] = pointAt(mark.azimuth, RIM);
        return svg`<line x1=${x1.toFixed(1)} y1=${y1.toFixed(1)} x2=${x2.toFixed(1)} y2=${y2.toFixed(1)} stroke=${HOUR} stroke-width="1.5"></line>`;
      });
      parts.push(svg`<g id="hours">${lines}</g>`);
    }
    if (this._on("show_sun") && attrs.sun_elevation > 0) {
      const [x, y] = pointAt(attrs.sun_azimuth, RING_R);
      parts.push(disc("sun", x, y, 8, "#f5c400"));
    }
    if (this._on("show_moon") && attrs.moon_elevation > 0) {
      const [x, y] = pointAt(attrs.moon_azimuth, RING_R);
      parts.push(disc("moon", x, y, 7, "#c5d0dc"));
    }
    if (this._on("show_times")) {
      for (const [key, az, id] of [
        ["sunrise", "sunrise_azimuth", "sunrise"],
        ["sunset", "sunset_azimuth", "sunset"],
      ]) {
        if (!attrs[key] || attrs[az] == null) continue;
        const [x, y] = labelAt(attrs[az]);
        parts.push(svg`<text id=${id} x=${x.toFixed(1)} y=${y.toFixed(1)} text-anchor="middle" dominant-baseline="middle">${this._clock(attrs[key])}</text>`);
      }
    }
    const [nx, ny] = pointAt(0, RING_R - 18);
    parts.push(svg`<text id="north" x=${nx.toFixed(1)} y=${(ny + 4).toFixed(1)} text-anchor="middle">N</text>`);
    return svg`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${SIZE} ${SIZE}">${parts}</svg>`;
  }

  render() {
    const entity = this.config?.entity || "sensor.sun_sweep";
    const state = this.hass?.states?.[entity];
    let body;
    if (!state) {
      body = html`<div class="message">Sun Sweep is not set up.</div>`;
    } else if (!state.attributes?.outline?.length) {
      body = html`<div class="message">House Structure has no building outline for this home yet.</div>`;
    } else {
      body = this._picture(state.attributes);
    }
    return html`<ha-card>${body}</ha-card>`;
  }
}

class SunSweepCardEditor extends LitElement {
  static properties = { hass: {}, config: {} };

  setConfig(config) {
    this.config = config;
  }

  _schema() {
    return [
      { name: "entity", selector: { entity: { domain: "sensor" } } },
      { name: "show_sun", selector: { boolean: {} } },
      { name: "show_times", selector: { boolean: {} } },
      { name: "show_moon", selector: { boolean: {} } },
      { name: "show_hours", selector: { boolean: {} } },
    ];
  }

  _data() {
    return {
      entity: this.config.entity || "sensor.sun_sweep",
      show_sun: this.config.show_sun !== false,
      show_times: this.config.show_times !== false,
      show_moon: this.config.show_moon !== false,
      show_hours: this.config.show_hours !== false,
    };
  }

  _changed(event) {
    const value = event.detail.value;
    if (!value) return;
    this.config = value;
    this.dispatchEvent(
      new CustomEvent("config-changed", { detail: { config: value } }),
    );
  }

  render() {
    return html`
      <ha-form
        .hass=${this.hass}
        .schema=${this._schema()}
        .data=${this._data()}
        .computeLabel=${(item) =>
          ({
            entity: "Entity",
            show_sun: "Sun",
            show_times: "Sunrise and sunset",
            show_moon: "Moon",
            show_hours: "Hour lines",
          })[item.name]}
        @value-changed=${this._changed}
      ></ha-form>
    `;
  }
}

customElements.define("sun-sweep-card", SunSweepCard);
customElements.define("sun-sweep-card-editor", SunSweepCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "sun-sweep-card",
  name: "Sun Sweep",
  description: "Today's sun angles around your house, top down.",
  preview: true,
  documentationURL: DOCS,
});
