/*
 * Sun Sweep: the house, top down, over today's sun wedge.
 * The shapes are drawn by drawing.js, which matches drawing.py.
 */
import { LitElement, css, html, nothing } from "lit";
import { unsafeSVG } from "lit/directives/unsafe-svg.js";

import { cardSvg } from "./drawing.js";

const DOCS =
  "https://github.com/minchinweb/ha-sunsweep-card/blob/master/docs/configuration.md";

class SunSweepCard extends LitElement {
  static properties = {
    hass: {},
    config: {},
    _fixed: { state: true },
    _loading: { state: true },
  };

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
    .actionable { cursor: pointer; }
    .actionable:focus-visible {
      outline: 2px solid var(--primary-color, #03a9f4);
      outline-offset: 2px;
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
      this._fixedKey = "";
      if (this._loading) this._loading = false;
      if (this._fixed !== undefined) this._fixed = undefined;
      return;
    }
    const key = `${date}|${this.config.time || ""}`;
    if (key === this._fixedKey) return;
    this._fixedKey = key;
    this._loading = true;
    try {
      const attrs = await this.hass.callWS({
        type: "sun_sweep/snapshot",
        date,
        time: this.config.time || undefined,
      });
      if (this._fixedKey !== key) return;
      this._fixed = attrs;
      this._loading = false;
    } catch (err) {
      if (this._fixedKey !== key) return;
      this._fixed = { error: err?.message || "That date could not be drawn." };
      this._loading = false;
    }
  }

  _held() {
    const date = String(this.config?.date || "").trim();
    const key = date.toLowerCase().replaceAll(" ", "-");
    const named = {
      "march-equinox": "the March equinox",
      "june-solstice": "the June solstice",
      "september-equinox": "the September equinox",
      "december-solstice": "the December solstice",
      "vernal-equinox": "the vernal equinox",
      "spring-equinox": "the spring equinox",
      "summer-solstice": "the summer solstice",
      "autumnal-equinox": "the autumnal equinox",
      "autumn-equinox": "the autumn equinox",
      "fall-equinox": "the fall equinox",
      "winter-solstice": "the winter solstice",
      spring: "spring",
      summer: "summer",
      autumn: "autumn",
      winter: "winter",
    };
    let label = named[key];
    const language = this.hass?.locale?.language;
    const timeZone = this.hass?.config?.time_zone;
    if (!label && date.includes("T") && !Number.isNaN(new Date(date).getTime())) {
      label = new Date(date).toLocaleString(language, {
        timeZone,
        dateStyle: "medium",
        timeStyle: "short",
      });
    } else if (!label && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
      const [year, month, day] = date.split("-").map(Number);
      label = new Date(Date.UTC(year, month - 1, day)).toLocaleDateString(language, {
        timeZone: "UTC",
        dateStyle: "medium",
      });
    } else if (!label) {
      label = date;
    }
    const clock =
      this.config?.time && !date.includes("T") ? ` at ${this._face(this.config.time)}` : "";
    return `Held on ${label}${clock}.`;
  }

  _face(clock) {
    const [hour, minute] = String(clock).split(":");
    const sample = new Date(Date.UTC(2026, 0, 1, Number(hour), Number(minute) || 0));
    const cycle = this.hass?.locale?.time_format;
    const hour12 = cycle === "12" ? true : cycle === "24" ? false : undefined;
    return sample.toLocaleTimeString(this.hass?.locale?.language, {
      hour: "numeric",
      minute: "2-digit",
      hour12,
      timeZone: "UTC",
    });
  }

  _on(key) {
    return this.config[key] !== false;
  }

  _clock(iso) {
    const cycle = this.hass?.locale?.time_format;
    const hour12 = cycle === "12" ? true : cycle === "24" ? false : undefined;
    const timeZone = this.hass?.config?.time_zone;
    return new Date(iso).toLocaleTimeString(this.hass?.locale?.language, {
      hour: "numeric",
      minute: "2-digit",
      hour12,
      timeZone,
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
    return html`<div class="disc" role="img" aria-label=${this._summary(attrs)}>${unsafeSVG(picture)}</div>`;
  }

  _summary(attrs) {
    if (attrs.phase === "polar_night") return "The sun stays below the horizon today.";
    if (attrs.phase === "polar_day") return "The sun stays above the horizon today.";
    const bits = [];
    if (attrs.phase === "before_sunrise") bits.push("Before sunrise");
    else if (attrs.phase === "after_sunset") bits.push("After sunset");
    else bits.push("Sun above the horizon");
    if (attrs.sunrise) bits.push(`sunrise ${this._clock(attrs.sunrise)}`);
    if (attrs.sunset) bits.push(`sunset ${this._clock(attrs.sunset)}`);
    return bits.join(", ");
  }

  _interactive() {
    const action = this.config?.tap_action?.action;
    return Boolean(action && action !== "none");
  }

  _tap() {
    const chosen = this.config?.tap_action;
    const action = chosen?.action;
    if (!action || action === "none") return;
    const entity = this.config?.entity || "sensor.sun_sweep";
    if (action === "more-info") {
      this.dispatchEvent(
        new CustomEvent("hass-more-info", {
          bubbles: true,
          composed: true,
          detail: { entityId: entity },
        }),
      );
      return;
    }
    if (action === "navigate" && chosen.navigation_path) {
      history.pushState(null, "", chosen.navigation_path);
      this.dispatchEvent(
        new CustomEvent("location-changed", {
          bubbles: true,
          composed: true,
          detail: { replace: false },
        }),
      );
      return;
    }
    if (action === "url" && chosen.url_path) {
      window.open(chosen.url_path);
      return;
    }
    if (action === "toggle") {
      this.hass?.callService("homeassistant", "toggle", { entity_id: entity });
      return;
    }
    if (action === "perform-action" || action === "call-service") {
      const service = chosen.perform_action || chosen.service;
      if (!service || !service.includes(".")) return;
      const [domain, name] = service.split(".");
      const data = { ...(chosen.service_data || {}), ...(chosen.data || {}) };
      this.hass?.callService(domain, name, data, chosen.target);
    }
  }

  _key(event) {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    this._tap();
  }

  render() {
    const entity = this.config?.entity || "sensor.sun_sweep";
    const state = this.hass?.states?.[entity];
    const pinned = Boolean(this.config?.date);
    const waiting = pinned && (this._loading || !this._fixed || this._fixed.error);
    const attrs = pinned ? (this._fixed?.error ? undefined : this._fixed) : state?.attributes;
    let body;
    if (pinned && this._fixed?.error && !this._loading) {
      body = html`<div class="message" aria-live="polite">${this._fixed.error}</div>`;
    } else if (pinned && (this._loading || !this._fixed)) {
      body = html`<div class="message" aria-live="polite">Drawing ${this.config.date}…</div>`;
    } else if (!pinned && !state) {
      body = html`<div class="message">Sun Sweep is not set up.</div>`;
    } else if (!pinned && (state.state === "unavailable" || state.state === "unknown")) {
      body = html`<div class="message">Sun Sweep is not ready yet.</div>`;
    } else if (!attrs?.outline?.length) {
      body = html`<div class="message">House Structure has no building outline for this home yet.</div>`;
    } else {
      body = this._picture(attrs);
    }
    const notes = [];
    if (!waiting && attrs?.outline_fallback) {
      notes.push("House Structure is not installed, so this is a plain square.");
    }
    if (!waiting && attrs?.phase === "polar_night") {
      notes.push("The sun stays below the horizon today.");
    }
    if (pinned && !this._loading && this._fixed && !this._fixed.error) {
      notes.push(this._held());
    }
    const note = notes.length
      ? html`<div class="note">${notes.map((line) => html`<div>${line}</div>`)}</div>`
      : "";
    const interactive = this._interactive();
    return html`
      <ha-card
        class=${interactive ? "actionable" : ""}
        tabindex=${interactive ? "0" : nothing}
        @click=${interactive ? this._tap : nothing}
        @keydown=${interactive ? this._key : nothing}
      >
        ${body}${note}
      </ha-card>
    `;
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
