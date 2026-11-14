import {
  formatInterval,
  formatNumber,
  formatPValue,
  formatSigned,
  NOT_AVAILABLE,
} from "../../src/utils/format";

describe("format helpers", () => {
  it("render null and non-finite values as an explicit dash, never 0", () => {
    expect(formatNumber(null)).toBe(NOT_AVAILABLE);
    expect(formatNumber(Number.NaN)).toBe(NOT_AVAILABLE);
    expect(formatSigned(undefined)).toBe(NOT_AVAILABLE);
    expect(formatPValue(null)).toBe(NOT_AVAILABLE);
    expect(formatInterval([null, 2])).toBe(NOT_AVAILABLE);
  });

  it("sign slopes and format intervals", () => {
    expect(formatSigned(2.5)).toBe("+2.50");
    expect(formatSigned(-1)).toBe("-1.00");
    expect(formatInterval([-1, 3])).toBe("-1.00 to +3.00");
  });

  it("formats p-values with a floor", () => {
    expect(formatPValue(0.0001)).toBe("< 0.001");
    expect(formatPValue(0.0456)).toBe("0.046");
  });
});
