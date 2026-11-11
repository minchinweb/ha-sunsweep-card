/*
 * The equinoxes and solstices, for the card editor's day list.
 * Matches season() in sweep.py: Meeus, Astronomical Algorithms, 1000 to 3000.
 */
const TERMS = {
  march: [2451623.80984, 365242.37404, 0.05169, -0.00411, -0.00057],
  june: [2451716.56767, 365241.62603, 0.00325, 0.00888, -0.0003],
  september: [2451810.21715, 365242.01767, -0.11575, 0.00337, 0.00078],
  december: [2451900.05952, 365242.74049, -0.06223, -0.00823, 0.00032],
};

// `which` is march, june, september, or december. Returns a Date (UTC moment).
export function season(year, which) {
  const y = (year - 2000) / 1000;
  const [a, b, c, d, e] = TERMS[which];
  const jde = a + b * y + c * y * y + d * y ** 3 + e * y ** 4;
  const noon2000 = Date.UTC(2000, 0, 1, 12);
  return new Date(noon2000 + (jde - 2451545.0) * 86400000 - 69000);
}
