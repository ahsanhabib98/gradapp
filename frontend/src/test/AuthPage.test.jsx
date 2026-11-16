import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { AuthProvider } from "../context";
import AuthPage from "../pages/AuthPage";

describe("AuthPage", () => {
  it("shows and hides the password", async () => {
    render(<AuthProvider><AuthPage /></AuthProvider>);
    const password = document.querySelector("input[name=password]");
    expect(password).toHaveAttribute("type", "password");
    await userEvent.click(screen.getByRole("button", { name: "Show password" }));
    expect(password).toHaveAttribute("type", "text");
    await userEvent.click(screen.getByRole("button", { name: "Hide password" }));
    expect(password).toHaveAttribute("type", "password");
  });
});
