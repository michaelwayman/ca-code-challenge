import React from "react";
import { createRoot } from "react-dom/client";
import BrandList from "./BrandList.jsx";

const el = document.getElementById("brand-list");
if (el) {
  const industries = JSON.parse(document.getElementById("brand-list-industries")?.textContent || "[]");
  createRoot(el).render(<BrandList apiUrl={el.dataset.apiUrl} brandUrl={el.dataset.brandUrl} industries={industries} />);
}
