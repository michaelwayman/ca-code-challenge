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
    <article className="card">
      {brand.industry && <span className="badge">{brand.industry}</span>}
      <h3><a href={brandUrl.replace("__slug__", brand.slug)}>{brand.name}</a></h3>
      <div>
        <Stars rating={brand.average_rating} />
        <span className="meta"> ({brand.review_count} reviews)</span>
      </div>
      <p className="excerpt">{brand.short_description}</p>
      {brand.top_review_snippet && <blockquote className="meta">"{brand.top_review_snippet}"</blockquote>}
    </article>
  );
}

export default function BrandList({ apiUrl, brandUrl, industries = [] }) {
  const [industry, setIndustry] = useState("");
  const [ordering, setOrdering] = useState("name");
  const [brands, setBrands] = useState([]);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ ordering });
    if (industry) params.append("industry", industry);
    fetch(`${apiUrl}?${params}`, { signal: controller.signal })
      .then((r) => r.json())
      .then((data) => setBrands(data.results))
      .catch((e) => {
        if (e.name !== "AbortError") throw e;
      });
    return () => controller.abort();
  }, [apiUrl, industry, ordering]);

  return (
    <div className="brand-list">
      <div className="brand-list-controls">
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
      <div className="grid">
        {brands.map((b) => (
          <BrandCard key={b.slug} brand={b} brandUrl={brandUrl} />
        ))}
      </div>
    </div>
  );
}
