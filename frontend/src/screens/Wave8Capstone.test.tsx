// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach, beforeAll } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Curriculum from "./Curriculum";
import SectorRotation from "./SectorRotation";
import Governance from "./Governance";
import Ops from "./Ops";
import * as clientModule from "../api/client";

beforeAll(() => {
  const g: any = globalThis as any;
  if (typeof g.localStorage === "undefined" || g.localStorage == null) {
    const store: Record<string,string> = {};
    g.localStorage = { getItem:(k:string)=>store[k]??null, setItem:(k:string,v:string)=>{store[k]=String(v)}, removeItem:(k:string)=>{delete store[k]}, clear:()=>{for(const k in store) delete store[k]}, length:0, key:()=>null } as any;
  }
});

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("Wave 8 Capstone Frontend", () => {
  it("renders Curriculum with 6 modules and flashcards (US-0504/US-0541)", async () => {
    vi.spyOn(clientModule.api, "requestCurriculumModules").mockResolvedValue({ count:6, items:[
      {id:"m01-balance-sheet", title:"1. What Is a Balance Sheet?", description:"Assets", lessons:[{id:"l01", title:"Assets", body:"Cash"}], key_terms:["Assets"], quiz:[{q:"Q", a:"A", options:["A"]}]},
      {id:"m02-income-cashflow", title:"2. Income & Cash Flow", description:"Rev", lessons:[{id:"l01", title:"Rev", body:"body"}], key_terms:[], quiz:[]},
      {id:"m03-valuation", title:"3. Valuation", description:"desc", lessons:[{id:"l01", title:"L", body:"b"}], key_terms:[], quiz:[]},
      {id:"m04-pillars", title:"4. Pillars", description:"desc", lessons:[{id:"l01", title:"L", body:"b"}], key_terms:[], quiz:[]},
      {id:"m05-forensics-intro", title:"5. Forensics", description:"desc", lessons:[{id:"l01", title:"L", body:"b"}], key_terms:[], quiz:[]},
      {id:"m06-advanced-manipulation", title:"6. Advanced", description:"desc", lessons:[{id:"l01", title:"L", body:"b"}], key_terms:[], quiz:[]},
    ], disclaimer:"Personal research software, not investment advice."} as any);
    vi.spyOn(clientModule.api, "requestCaseStudies").mockResolvedValue({count:1, items:[{id:"enron-2001", title:"Enron (2001)", summary:"Enron", metrics_mapped:["Beneish"], lesson:"lesson"}]} as any);
    vi.spyOn(clientModule.api, "requestFlashcards").mockResolvedValue({count:2, items:[{front:"Q1", back:"A1"}, {front:"Q2", back:"A2"}]} as any);
    render(<BrowserRouter><Curriculum /></BrowserRouter>);
    expect(await screen.findByText(/Investment Curriculum/, {}, {timeout:3000})).toBeTruthy();
    expect(screen.getAllByText(/What Is a Balance Sheet/)[0]).toBeTruthy();
    expect(screen.getByText(/Flashcards/)).toBeTruthy();
    expect(screen.getAllByText(/Enron/)[0]).toBeTruthy();
  });

  it("renders SectorRotation with cycle tag and histogram SVG (US-0864/US-0886)", async () => {
    vi.spyOn(clientModule.api, "requestSectorRotation").mockResolvedValue({currency:"ALL", sectors:[{sector:"Energy", count:10, median_composite:5.5, quarterly_delta:0.12, direction:"Expansion"}, {sector:"Utilities", count:8, median_composite:4.2, quarterly_delta:-0.08, direction:"Compression"}], disclaimer:"Personal research software, not investment advice."} as any);
    vi.spyOn(clientModule.api, "requestSectorHistogram").mockResolvedValue({sheet:"Information Technology", currency:"ALL", metric:"composite", count:10, median:5.5, bins:[1,2,3,2,1], bin_edges:["0-2","2-4","4-6","6-8","8-10"], disclaimer:""} as any);
    vi.spyOn(clientModule.api, "requestCycleTag").mockResolvedValue({sheet:"Information Technology", cycle_tag:"Early / Growth", explanation:"Tech", disclaimer:""} as any);
    vi.spyOn(clientModule.api, "requestBarrier").mockResolvedValue({sheet:"Information Technology", currency:"USD", median_margin_stdev:0.03, barrier_assessment:"High barrier proxy (stable margins)", method:"stdev", disclaimer:""} as any);
    render(<BrowserRouter><SectorRotation /></BrowserRouter>);
    expect(await screen.findByText(/Rotation & Market Structure/, {}, {timeout:3000})).toBeTruthy();
    expect(screen.getByText(/Cycle Tag/)).toBeTruthy();
    expect(screen.getByText(/Barrier Proxy/)).toBeTruthy();
    const svgs = document.querySelectorAll("svg[role='img']");
    expect(svgs.length).toBeGreaterThan(0);
  });

  it("renders Governance with risk register and diff matrix (US-0820/US-0818)", async () => {
    vi.spyOn(clientModule.api, "requestModelRisk").mockResolvedValue({count:1, items:[{model:"Composite 0.30Q/0.25V", assumption:"a", false_positive:"b", blind_spot:"c", mitigation:"d"}], disclaimer:""} as any);
    vi.spyOn(clientModule.api, "requestCanonMap").mockResolvedValue({count:1, items:[{book:"Benjamin Graham - The Intelligent Investor", app_feature:"Graham", check:"check"}]} as any);
    vi.spyOn(clientModule.api, "requestDiffMatrix").mockResolvedValue({columns:["Feature","This App","Seeking Alpha","Simply Wall St","TIKR","GuruFocus"], rows:[["Forensic suite","✅","❌","❌","limited","warning"]], disclaimer:""} as any);
    render(<BrowserRouter><Governance /></BrowserRouter>);
    expect(await screen.findByText(/Governance - Model Risk Register/, {}, {timeout:3000})).toBeTruthy();
    expect(screen.getAllByText(/Model Risk Register/)[0]).toBeTruthy();
    expect(screen.getByText(/Canon Literature/)).toBeTruthy();
    expect(screen.getByText(/Competitive Diff/)).toBeTruthy();
    expect(screen.getAllByText(/Seeking Alpha/)[0]).toBeTruthy();
  });

  it("renders Ops with diagnostics and seed checksum (US-0957/US-0967)", async () => {
    vi.spyOn(clientModule.api, "requestDiagnostics").mockResolvedValue({cpu_percent:12.5, db_size_bytes:1234567, db_path:"data/app.db", worker:"JobWorker", integrity:{ok:true, result:"ok"}, disclaimer:""} as any);
    vi.spyOn(clientModule.api, "requestBackups").mockResolvedValue({count:1, items:[{file:"app_backup_20260905_120000.db", size_bytes:1234, modified_at:"2026-09-05"}]} as any);
    vi.spyOn(clientModule.api, "requestIntegrity").mockResolvedValue({ok:true, result:"ok", db:"data/app.db"} as any);
    vi.spyOn(clientModule.api, "requestSeedChecksum").mockResolvedValue({ok:true, file:"Sector_Financials_Final_Owner.xlsx", sha256:"a".repeat(64), sha256_short:"a".repeat(16), note:"note"} as any);
    render(<BrowserRouter><Ops /></BrowserRouter>);
    expect(await screen.findByText(/Local Backup, Diagnostics/, {}, {timeout:3000})).toBeTruthy();
    expect(screen.getByText(/System Diagnostics/)).toBeTruthy();
    expect(screen.getByText(/Seed Immutability/)).toBeTruthy();
    expect(screen.getByText(/One-Click Backup/)).toBeTruthy();
  });
});