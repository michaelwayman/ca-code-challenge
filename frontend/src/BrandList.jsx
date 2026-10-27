import React, { useEffect, useState } from "react";

const SORTS = [
  { value: "name", label: "Name (A-Z)" },
  { value: "-average_rating", label: "Highest rated" },
  { value: "average_rating", label: "Lowest rated" },
  { value: "-review_count", label: "Most reviews" },
  { value: "review_count", label: "Fewest reviews" },
];

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
      {brand.industry && <span className="badge">{brand.industry}</span>}
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
  const [industry, setIndustry] = useState("");
  const [ordering, setOrdering] = useState("name");
  const [brands, setBrands] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setStatus("loading");
    const params = new URLSearchParams({ ordering });
    if (industry) params.append("industry", industry);
    fetch(`${apiUrl}?${params}`, { signal: controller.signal })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setBrands(data.results);
        setStatus("ready");
      })
      .catch((e) => {
        if (e.name !== "AbortError") setStatus("error");
      });
    return () => controller.abort();
  }, [apiUrl, industry, ordering, attempt]);

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
        <ul className="grid brand-grid" aria-label="Brands">
          {brands.map((b) => (
            <BrandCard key={b.slug} brand={b} brandUrl={brandUrl} />
          ))}
        </ul>
      )}
    </div>
  );
}
