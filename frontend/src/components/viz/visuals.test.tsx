// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CompositeGauge } from "./CompositeGauge";
import { MiniPillarBars } from "./MiniPillarBars";
import { PillarRadar } from "./PillarRadar";
import { Sparkline } from "./Sparkline";

describe("SVG Visualization Primitives", () => {
  afterEach(cleanup);

  describe("CompositeGauge", () => {
    it("renders gauge with value and accessible label", () => {
      render(<CompositeGauge value={7.8} signal="strong_candidate" size="md" />);
      expect(screen.getByText("7.8")).toBeDefined();
      expect(screen.getByRole("img", { name: /Composite score gauge/i })).toBeDefined();
    });

    it("handles null value gracefully", () => {
      render(<CompositeGauge value={null} size="sm" />);
      expect(screen.getByText("—")).toBeDefined();
    });
  });

  describe("PillarRadar", () => {
    it("renders polygon with 4 scored axes and accessible label", () => {
      const { container } = render(
        <PillarRadar quality={8.5} value={6.2} growth={7.1} risk={5.0} size={200} />
      );
      expect(screen.getByRole("img", { name: /Pillar radar chart/i })).toBeDefined();
      const polygon = container.querySelector("polygon");
      expect(polygon).not.toBeNull();
      expect(polygon?.getAttribute("points")).toBeTruthy();
    });

    it("renders hollow dot for null pillar", () => {
      const { container } = render(
        <PillarRadar quality={8.5} value={6.2} growth={null} risk={5.0} size={200} />
      );
      const circles = container.querySelectorAll("circle");
      expect(circles.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe("Sparkline", () => {
    it("renders pure SVG sparkline path and last-point dot", () => {
      const { container } = render(
        <Sparkline data={[10, 20, 15, 30, 25]} width={60} height={20} />
      );
      expect(screen.getByRole("img", { name: /Historical trend sparkline/i })).toBeDefined();
      const path = container.querySelector("path");
      expect(path).not.toBeNull();
      const circle = container.querySelector("circle");
      expect(circle).not.toBeNull();
    });

    it("handles empty or insufficient data without crashing", () => {
      render(<Sparkline data={[]} />);
      expect(screen.getByText("—")).toBeDefined();
    });
  });

  describe("MiniPillarBars", () => {
    it("renders 4 pillar bars (Q, V, G, R)", () => {
      render(<MiniPillarBars quality={7} value={8} growth={null} risk={6} />);
      expect(screen.getByText("Q")).toBeDefined();
      expect(screen.getByText("V")).toBeDefined();
      expect(screen.getByText("G")).toBeDefined();
      expect(screen.getByText("R")).toBeDefined();
      expect(screen.getByRole("img", { name: /Pillars: Q 7\.0, V 8\.0, G —, R 6\.0/i })).toBeDefined();
    });
  });
});
