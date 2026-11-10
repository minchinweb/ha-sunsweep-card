/*
 * Print the card SVG for one JSON payload on stdin: { "attrs", "options" }.
 * The clock matches drawing.py so the two pictures can be compared.
 */
import { readFileSync } from "node:fs";

import { cardSvg } from "../custom_components/sun_sweep/frontend/drawing.js";

const payload = JSON.parse(readFileSync(0, "utf8"));

function clock(iso) {
  const match = /T(\d{2}):(\d{2})/.exec(iso);
  let hour = Number(match[1]);
  const minute = match[2];
  const suffix = hour >= 12 ? "PM" : "AM";
  hour = hour % 12 || 12;
  return `${hour}:${minute} ${suffix}`;
}

process.stdout.write(
  cardSvg(payload.attrs, { ...(payload.options || {}), clock }),
);
