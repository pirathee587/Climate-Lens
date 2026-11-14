// Registers jest-dom matchers. Testing Library auto-cleans between tests
// because `test.globals` is enabled in vite.config.ts.
import "@testing-library/jest-dom/vitest";

// jsdom has no ResizeObserver; Recharts' ResponsiveContainer needs one.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
globalThis.ResizeObserver ??= ResizeObserverStub;
