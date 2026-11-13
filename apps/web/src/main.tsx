import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { TechnicalApp } from "./TechnicalApp";
import { createCesiumGlobe } from "./globe/createCesiumGlobe";
import "./styles/technical.css";

const root = document.getElementById("root");
if (!root) {
  throw new Error("Falta el nodo #root.");
}

createRoot(root).render(
  <StrictMode>
    <TechnicalApp createGlobe={createCesiumGlobe} />
  </StrictMode>,
);
