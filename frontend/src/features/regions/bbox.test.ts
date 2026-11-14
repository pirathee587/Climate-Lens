import { describe, expect, it } from "vitest";

import { bboxToLeafletBounds, isValidBBox } from "./bbox";

describe("region bounding boxes", () => {
  it("validates WGS84 bounds", () => {
    expect(isValidBBox([-10, 5, 10, 15])).toBe(true);
    expect(isValidBBox(null)).toBe(false);
    expect(isValidBBox([10, 5, -10, 15])).toBe(false);
    expect(isValidBBox([-181, 5, 10, 15])).toBe(false);
    expect(isValidBBox([-10, -91, 10, 15])).toBe(false);
    expect(isValidBBox([-10, 5, 10, 91])).toBe(false);
    expect(isValidBBox([Number.NaN, 5, 10, 15])).toBe(false);
    expect(isValidBBox([-10, 15, 10, 5])).toBe(false);
  });

  it("converts west/south/east/north to Leaflet bounds", () => {
    expect(bboxToLeafletBounds([-10, 5, 10, 15])).toEqual([
      [5, -10],
      [15, 10],
    ]);
    expect(bboxToLeafletBounds(null)).toBeNull();
  });
});
