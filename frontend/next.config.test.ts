import { describe, expect, it } from "vitest";

import nextConfig from "./next.config";

describe("nextConfig", () => {
  it("keeps Turbopack rooted to the frontend workspace", () => {
    expect(nextConfig.turbopack?.root).toBe(process.cwd());
  });
});
