import React from "react";
import { render, screen, waitFor, cleanup } from "@testing-library/react";
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
