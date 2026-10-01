import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("interface Alumni", () => {
  const html = readFileSync(resolve("index.html"), "utf8");
  const app = readFileSync(resolve("public/app.js"), "utf8");

  it("expose le point de montage et les quatre rôles", () => {
    expect(html).toContain('id="app"');
    for (const role of ["admin", "direction", "alumni", "consult"]) {
      expect(html).toContain(`value="${role}"`);
    }
  });

  it("couvre les parcours MVP principaux", () => {
    for (const capability of ["dashboard", "validation", "directory", "profile", "campaigns", "audit"]) {
      expect(app).toContain(`function ${capability}`);
    }
  });
});
