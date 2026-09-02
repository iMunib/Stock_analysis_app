import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import App from "./App";
import Home from "./screens/Home";
import Dossier from "./screens/Dossier";
import Compare from "./screens/Compare";
import Sector from "./screens/Sector";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/c/:companyId" element={<Dossier />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/sectors/:sheet" element={<Sector />} />
        </Routes>
      </App>
    </BrowserRouter>
  </React.StrictMode>,
);
