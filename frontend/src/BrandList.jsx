import React, { useEffect, useState } from "react";

const SORTS = [
  { value: "name", label: "Name (A-Z)" },
  { value: "-average_rating", label: "Highest rated" },
  { value: "average_rating", label: "Lowest rated" },
  { value: "-review_count", label: "Most reviews" },
  { value: "review_count", label: "Fewest reviews" },
];

const PAGE_SIZE = 10;

// Initial state comes from the page URL so a reloaded or shared link restores it.
// Unknown values fall back to the defaults instead of reaching the API.
function readUrlState(industries) {
  const q = new URLSearchParams(window.location.search);
  const industry = q.get("industry") || "";
  const ordering = q.get("ordering") || "";
  const page = Number.parseInt(q.get("page") || "", 10);
  return {
    industry: industries.some((i) => i.slug === industry) ? industry : "",
    ordering: SORTS.some((s) => s.value === ordering) ? ordering : "name",
    page: Number.isInteger(page) && page > 0 ? page : 1,
  };
}

function writeUrlState({ industry, ordering, page }) {
  const q = new URLSearchParams(window.location.search);
  const set = (key, value, isDefault) => (isDefault ? q.delete(key) : q.set(key, value));
  set("industry", industry, !industry);
  set("ordering", ordering, ordering === "name");
  set("page", String(page), page === 1);
  const query = q.toString();
  const url = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
  window.history.replaceState(null, "", url);
}

function Stars({ rating }) {
  const full = Math.round(rating || 0);
  const label = rating == null ? "No rating" : `${rating} out of 5 stars`;
  return (
    <span className="stars" role="img" aria-label={label}>
      {[0, 1, 2, 3, 4].map((i) => (
        <span key={i} className={i < full ? "star-full" : "star-empty"} aria-hidden="true">★</span>
      ))}
      {rating != null && <span className="rating-value">{rating}</span>}
    </span>
  );
}

function BrandCard({ brand, brandUrl }) {
  return (
    <li className="card">
      {brand.industry && <div><span className="badge">{brand.industry}</span></div>}
      <h3><a href={brandUrl.replace("__slug__", brand.slug)}>{brand.name}</a></h3>
      <div>
        <Stars rating={brand.average_rating} />
        <span className="meta"> ({brand.review_count} reviews)</span>
      </div>
      <p className="excerpt">{brand.short_description}</p>
      {brand.top_review_snippet && <blockquote className="meta">"{brand.top_review_snippet}"</blockquote>}
    </li>
  );
}

export default function BrandList({ apiUrl, brandUrl, industries = [] }) {
  const [initial] = useState(() => readUrlState(industries));
  const [industry, setIndustryState] = useState(initial.industry);
  const [ordering, setOrderingState] = useState(initial.ordering);
  const [page, setPage] = useState(initial.page);
  const [brands, setBrands] = useState([]);
  const [count, setCount] = useState(0);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [attempt, setAttempt] = useState(0);

  // Changing a filter or the sort starts again from the first page.
  const setIndustry = (value) => { setIndustryState(value); setPage(1); };
  const setOrdering = (value) => { setOrderingState(value); setPage(1); };

  useEffect(() => writeUrlState({ industry, ordering, page }), [industry, ordering, page]);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    const params = new URLSearchParams({ ordering, page: String(page), page_size: String(PAGE_SIZE) });
    if (industry) params.append("industry", industry);
    fetch(`${apiUrl}?${params}`, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        // A shared link can point past the last page: go back to page 1.
        if (data.results.length === 0 && data.count > 0 && page > 1) {
          setPage(1);
          return;
        }
        setBrands(data.results);
        setCount(data.count);
        setStatus("ready");
      })
      .catch((e) => {
        if (e.name !== "AbortError") setStatus("error");
      });
    return () => controller.abort();
  }, [apiUrl, industry, ordering, page, attempt]);

  return (
    <div className="brand-list">
      <div className="brand-list-controls" role="group" aria-label="Filter and sort brands">
        <label>
          Industry{" "}
          <select value={industry} onChange={(e) => setIndustry(e.target.value)}>
            <option value="">All industries</option>
            {industries.map((i) => (
              <option key={i.slug} value={i.slug}>{i.name}</option>
            ))}
          </select>
        </label>
        <label>
          Sort by{" "}
          <select value={ordering} onChange={(e) => setOrdering(e.target.value)}>
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </label>
      </div>
      {status === "loading" && (
        <p className="brand-list-message" role="status">Loading brands…</p>
      )}
      {status === "error" && (
        <div className="brand-list-message brand-list-error" role="alert">
          <p>Sorry, brands could not be loaded.</p>
          <button type="button" onClick={() => setAttempt((n) => n + 1)}>Try again</button>
        </div>
      )}
      {status === "ready" && brands.length === 0 && (
        <p className="brand-list-message" role="status">No brands match this filter.</p>
      )}
      {status === "ready" && brands.length > 0 && (
        <>
          <p className="brand-list-summary" role="status">
            Showing {(page - 1) * PAGE_SIZE + 1}-{(page - 1) * PAGE_SIZE + brands.length} of {count} {count === 1 ? "brand" : "brands"}
          </p>
          <ul className="grid brand-grid" aria-label="Brands">
            {brands.map((b) => (
              <BrandCard key={b.slug} brand={b} brandUrl={brandUrl} />
            ))}
          </ul>
          {count > PAGE_SIZE && (
            <nav className="pagination" aria-label="Brand pages">
              <button type="button" className="page-numbers" disabled={page <= 1}
                      onClick={() => setPage(page - 1)}>Previous</button>
              <button type="button" className="page-numbers" disabled={page * PAGE_SIZE >= count}
                      onClick={() => setPage(page + 1)}>Next</button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
