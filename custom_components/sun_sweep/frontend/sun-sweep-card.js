/*
 * Sun Sweep: the house, top down, over today's sun wedge.
 * The shapes are drawn by drawing.js, which matches drawing.py.
 */
import { LitElement, css, html } from "lit";
import { unsafeSVG } from "lit/directives/unsafe-svg.js";

import { cardSvg } from "./drawing.js";

const DOCS =
  "https://github.com/minchinweb/ha-sunsweep-card/blob/master/docs/configuration.md";

class SunSweepCard extends LitElement {
  static properties = { hass: {}, config: {}, _fixed: { state: true } };

  static styles = css`
    :host { display: block; }
    svg {
      width: 100%;
      height: auto;
      display: block;
      font-family: var(--ha-font-family, sans-serif);
    }
    .message, .note {
      padding: 16px;
      text-align: center;
      color: var(--primary-text-color);
    }
    .note {
      padding-top: 0;
      color: var(--secondary-text-color);
      font-size: 0.85em;
    }
  `;

  static getConfigElement() {
    return document.createElement("sun-sweep-card-editor");
  }

  static getStubConfig() {
    return { entity: "sensor.sun_sweep" };
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return {
      columns: 6,
      rows: 6,
      min_columns: 4,
      min_rows: 4,
    };
  }

  setConfig(config) {
    if (!config) throw new Error("Invalid configuration");
    this.config = config;
  }

  willUpdate(changed) {
    if (changed.has("config") || changed.has("hass")) this._loadFixed();
  }

  async _loadFixed() {
    const date = this.config?.date;
    if (!date || !this.hass?.callWS) {
      this._fixed = undefined;
      this._fixedKey = "";
      return;
    }
    const key = `${date}|${this.config.time || ""}`;
    if (key === this._fixedKey) return;
    this._fixedKey = key;
    try {
      const attrs = await this.hass.callWS({
        type: "sun_sweep/snapshot",
        date,
        time: this.config.time || undefined,
      });
      if (this._fixedKey === key) this._fixed = attrs;
    } catch (err) {
      if (this._fixedKey === key) {
        this._fixed = { error: err?.message || "That date could not be drawn." };
      }
    }
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
    const picture = cardSvg(attrs, {
      show_sun: this._on("show_sun"),
      show_times: this._on("show_times"),
      show_moon: this._on("show_moon"),
      show_hours: this._on("show_hours"),
      show_twilight: this._on("show_twilight"),
      rotation: Number(this.config?.rotation) || 0,
      clock: (iso) => this._clock(iso),
      embedded: true,
    });
    return html`${unsafeSVG(picture)}`;
  }

  render() {
    const entity = this.config?.entity || "sensor.sun_sweep";
    const state = this.hass?.states?.[entity];
    const pinned = Boolean(this.config?.date);
    const attrs = pinned ? this._fixed : state?.attributes;
    let body;
    if (pinned && !this._fixed) {
      body = html`<div class="message">Drawing ${this.config.date}…</div>`;
    } else if (pinned && this._fixed?.error) {
      body = html`<div class="message">${this._fixed.error}</div>`;
    } else if (!pinned && !state) {
      body = html`<div class="message">Sun Sweep is not set up.</div>`;
    } else if (!attrs?.outline?.length) {
      body = html`<div class="message">House Structure has no building outline for this home yet.</div>`;
    } else {
      body = this._picture(attrs);
    }
    const note = attrs?.outline_fallback
      ? html`<div class="note">House Structure is not installed, so this is a plain square.</div>`
      : "";
    return html`<ha-card>${body}${note}</ha-card>`;
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
      { name: "show_twilight", selector: { boolean: {} } },
      {
        name: "rotation",
        selector: {
          number: { min: -180, max: 180, step: 1, mode: "box", unit_of_measurement: "°" },
        },
      },
      { name: "date", selector: { text: {} } },
      { name: "time", selector: { text: {} } },
    ];
  }

  _data() {
    return {
      entity: this.config.entity || "sensor.sun_sweep",
      show_sun: this.config.show_sun !== false,
      show_times: this.config.show_times !== false,
      show_moon: this.config.show_moon !== false,
      show_hours: this.config.show_hours !== false,
      show_twilight: this.config.show_twilight !== false,
      rotation: Number(this.config.rotation) || 0,
      date: this.config.date || "",
      time: this.config.time || "",
    };
  }

  _changed(event) {
    const value = event.detail.value;
    if (!value) return;
    if (!value.rotation) delete value.rotation;
    if (!value.date) delete value.date;
    if (!value.time) delete value.time;
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
            show_twilight: "Twilight",
            rotation: "Rotation",
            date: "Date (YYYY-MM-DD, equinox, or solstice)",
            time: "Time (HH:MM)",
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
