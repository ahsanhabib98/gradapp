import { describe, expect, it, vi } from "vitest";
import { api, errorMessage, onSessionExpired, query, saveSession } from "../api";

function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}

describe("errorMessage", () => {
  it("reads the backend's error.message", () => {
    expect(errorMessage({ error: { message: "Invalid username or password." } }, 400)).toBe("Invalid username or password.");
  });
  it("falls back to friendly text", () => {
    expect(errorMessage(null, 500)).toMatch(/server had a problem/);
    expect(errorMessage(null, 429)).toMatch(/Too many requests/);
  });
});

describe("query", () => {
  it("skips empty values", () => {
    expect(query({ search: "data", degree_level: "", page: undefined, open: false })).toBe("?search=data");
    expect(query({})).toBe("");
  });
});

describe("api", () => {
  it("sends JSON and the bearer token", async () => {
    saveSession({ access: "A1", refresh: "R1", user: { id: 1 } });
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(200, { ok: true }));
    await api("/thing/", { method: "POST", body: { a: 1 } });
    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.Authorization).toBe("Bearer A1");
    expect(options.body).toBe('{"a":1}');
  });

  it("throws ApiError with the readable message", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(400, { error: { message: "Passwords do not match.", details: {} } }));
    await expect(api("/auth/register/", { method: "POST", body: {} })).rejects.toThrow("Passwords do not match.");
  });

  it("refreshes an expired access token and retries once", async () => {
    saveSession({ access: "OLD", refresh: "R1", user: { id: 1 } });
    const fetchMock = vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(401, {}))
      .mockResolvedValueOnce(jsonResponse(200, { access: "NEW", refresh: "R2" }))
      .mockResolvedValueOnce(jsonResponse(200, { results: [] }));
    const data = await api("/programs/");
    expect(data).toEqual({ results: [] });
    expect(fetchMock.mock.calls[1][0]).toMatch(/\/auth\/token\/refresh\/$/);
    expect(fetchMock.mock.calls[2][1].headers.Authorization).toBe("Bearer NEW");
    expect(localStorage.getItem("gradapp_refresh")).toBe("R2");
  });

  it("clears the session when refresh fails", async () => {
    saveSession({ access: "OLD", refresh: "R1", user: { id: 1 } });
    const expired = vi.fn();
    onSessionExpired(expired);
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(401, {}))
      .mockResolvedValueOnce(jsonResponse(401, {}));
    await expect(api("/programs/")).rejects.toThrow(/session has expired/);
    expect(expired).toHaveBeenCalled();
    expect(localStorage.getItem("gradapp_access")).toBeNull();
  });

  it("clears the compare selection on sign-out so it never leaks to another account", async () => {
    const { clearSession } = await import("../api");
    localStorage.setItem("gradapp_compare", "[1,2]");
    clearSession();
    expect(localStorage.getItem("gradapp_compare")).toBeNull();
  });

  it("reports network failures clearly", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(api("/programs/")).rejects.toThrow(/Cannot reach the GradApp server/);
  });
});

describe("isSampleUrl", async () => {
  const { isSampleUrl } = await import("../components/ui");
  it("detects fictional sample domains only", () => {
    expect(isSampleUrl("https://www.gulfcoast-state.example/graduate/cs-ms")).toBe(true);
    expect(isSampleUrl("https://www.uh.edu/cs/ms")).toBe(false);
    expect(isSampleUrl("")).toBe(false);
    expect(isSampleUrl("not a url")).toBe(false);
  });
});
