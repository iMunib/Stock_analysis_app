import { Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import Home from "./screens/Home";
import Dossier from "./screens/Dossier";
import Compare from "./screens/Compare";
import Sector from "./screens/Sector";
import SectorsHub from "./screens/SectorsHub";
import Jobs from "./screens/Jobs";

export default function App() {
  return (
    <ErrorBoundary>
      <AppShell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/sectors" element={<SectorsHub />} />
          <Route path="/sectors/:sheet" element={<Sector />} />
          <Route path="/c/:companyId" element={<Dossier />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </AppShell>
    </ErrorBoundary>
  );
}
