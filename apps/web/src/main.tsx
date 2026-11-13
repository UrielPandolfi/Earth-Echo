import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ObservatoryApp } from "./shell/ObservatoryApp";
import { createCesiumGlobe } from "./globe/createCesiumGlobe";
import "./styles/tokens.css";
import "./styles/observatory.css";

const root = document.getElementById("root");
if (!root) {
  throw new Error("Falta el nodo #root.");
}

createRoot(root).render(
  <StrictMode>
    <ObservatoryApp createGlobe={createCesiumGlobe} />
  </StrictMode>,
);
