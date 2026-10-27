import React from "react";
import { render, screen, waitFor, cleanup, fireEvent } from "@testing-library/react";
import axe from "axe-core";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import BrandList from "./BrandList.jsx";

const brands = [
  { name: "Acme", slug: "acme", industry: "Insurance", average_rating: 3.9, review_count: 12,
    short_description: "An insurer.", top_review_snippet: "Great service." },
  { name: "NoReviews", slug: "none", industry: null, average_rating: null, review_count: 0,
    short_description: "", top_review_snippet: null },
];
const industries = [{ name: "Insurance", slug: "insurance" }];

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({ count: 2, results: brands }) })));
});
afterEach(() => cleanup());

const ui = () => <BrandList apiUrl="/api/brands/" brandUrl="/brand/__slug__/" industries={industries} />;

async function violations(container) {
  const { violations } = await axe.run(container, { rules: { "color-contrast": { enabled: false } } });
  return violations.map((v) => `${v.id}: ${v.nodes.map((n) => n.html).join(" | ")}`);
}

test("loaded list has zero axe violations and list markup", async () => {
  const { container } = render(ui());
  await waitFor(() => screen.getByRole("list", { name: "Brands" }));
  expect(screen.getAllByRole("listitem")).toHaveLength(2);
  expect(screen.getByLabelText(/Industry/)).toBeTruthy();
  expect(screen.getByLabelText(/Sort by/)).toBeTruthy();
  expect(await violations(container)).toEqual([]);
});

test("error and empty states have zero axe violations", async () => {
  fetch.mockImplementationOnce(() => Promise.resolve({ ok: false, status: 500 }));
  const { container } = render(ui());
  await waitFor(() => screen.getByRole("alert"));
  expect(await violations(container)).toEqual([]);
  cleanup();
  fetch.mockImplementationOnce(() => Promise.resolve({ ok: true, json: () => Promise.resolve({ results: [] }) }));
  const second = render(ui());
  await waitFor(() => screen.getByText(/No brands match/));
  expect(await violations(second.container)).toEqual([]);
});

const requested = () => fetch.mock.calls.map((c) => new URLSearchParams(c[0].split("?")[1]));

test("state is restored from the URL and written back to it", async () => {
  window.history.replaceState(null, "", "/?industry=insurance&ordering=-review_count&page=2");
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({
    ok: true, json: () => Promise.resolve({ count: 12, results: brands }) })));
  render(ui());
  await waitFor(() => screen.getByRole("list", { name: "Brands" }));
  const q = requested()[0];
  expect(q.get("industry")).toBe("insurance");
  expect(q.get("ordering")).toBe("-review_count");
  expect(q.get("page")).toBe("2");
  expect(screen.getByLabelText(/Industry/).value).toBe("insurance");
  expect(window.location.search).toBe("?industry=insurance&ordering=-review_count&page=2");
});

test("unknown URL values fall back to the defaults", async () => {
  window.history.replaceState(null, "", "/?industry=nope&ordering=evil&page=-3");
  render(ui());
  await waitFor(() => screen.getByRole("list", { name: "Brands" }));
  const q = requested()[0];
  expect(q.get("industry")).toBeNull();
  expect(q.get("ordering")).toBe("name");
  expect(q.get("page")).toBe("1");
  expect(window.location.search).toBe("");
});

test("pagination reaches the next page and shows the total", async () => {
  window.history.replaceState(null, "", "/");
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({
    ok: true, json: () => Promise.resolve({ count: 12, results: brands }) })));
  const { container } = render(ui());
  await waitFor(() => screen.getByText(/Showing 1-2 of 12 brands/));
  expect(screen.getByRole("button", { name: "Previous" }).disabled).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Next" }));
  await waitFor(() => screen.getByText(/Showing 11-12 of 12 brands/));
  expect(requested().at(-1).get("page")).toBe("2");
  expect(window.location.search).toBe("?page=2");
  expect(await violations(container)).toEqual([]);
});

test("changing the sort returns to page 1", async () => {
  window.history.replaceState(null, "", "/?page=2");
  vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({
    ok: true, json: () => Promise.resolve({ count: 12, results: brands }) })));
  render(ui());
  await waitFor(() => screen.getByRole("list", { name: "Brands" }));
  fireEvent.change(screen.getByLabelText(/Sort by/), { target: { value: "-average_rating" } });
  await waitFor(() => expect(requested().at(-1).get("ordering")).toBe("-average_rating"));
  expect(requested().at(-1).get("page")).toBe("1");
});
