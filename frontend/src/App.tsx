import { Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import { ErrorBoundary } from "./components/ErrorBoundary";
import Home from "./screens/Home";
import Screen from "./screens/Screen";
import Dossier from "./screens/Dossier";
import Compare from "./screens/Compare";
import Sector from "./screens/Sector";
import SectorsHub from "./screens/SectorsHub";
import Jobs from "./screens/Jobs";
import Learn from "./screens/Learn";
import Screener from "./screens/Screener";
import CoverageHealth from "./screens/CoverageHealth";
import Watchlist from "./screens/Watchlist";
import Portfolio from "./screens/Portfolio";
import AlertsCenter from "./screens/AlertsCenter";
import Curriculum from "./screens/Curriculum";
import SectorRotation from "./screens/SectorRotation";
import Governance from "./screens/Governance";
import Ops from "./screens/Ops";

export default function App() {
  return (
    <ErrorBoundary>
      <AppShell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/screen" element={<Screen />} />
          <Route path="/screener" element={<Screener />} />
          <Route path="/watchlist" element={<Watchlist />} />
          <Route path="/digest" element={<Watchlist />} />
          <Route path="/morning-brief" element={<Watchlist />} />
          <Route path="/sectors" element={<SectorsHub />} />
          <Route path="/sectors/:sheet" element={<Sector />} />
          <Route path="/c/:companyId" element={<Dossier />} />
          <Route path="/dossier/:companyId" element={<Dossier />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/alerts" element={<AlertsCenter />} />
          <Route path="/coverage" element={<CoverageHealth />} />
          <Route path="/data-health" element={<CoverageHealth />} />
          <Route path="/learn" element={<Learn />} />
          <Route path="/learn/curriculum" element={<Curriculum />} />
          <Route path="/sectors/rotation" element={<SectorRotation />} />
          <Route path="/governance/model-risk" element={<Governance />} />
          <Route path="/governance" element={<Governance />} />
          <Route path="/ops" element={<Ops />} />
          <Route path="/ops/diagnostics" element={<Ops />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </AppShell>
    </ErrorBoundary>
  );
}
