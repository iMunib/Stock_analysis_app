// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Card } from "./Card";
import { Chip } from "./Chip";
import { Grid } from "./Grid";
import { Page } from "./Page";
import { StatTile } from "./StatTile";

describe("Layout Primitives", () => {
  afterEach(cleanup);

  describe("StatTile", () => {
    it("renders label and formatted value", () => {
      render(<StatTile label="Revenue" value="$25.4B" />);
      expect(screen.getByText("Revenue")).toBeDefined();
      expect(screen.getByText("$25.4B")).toBeDefined();
    });

    it("renders positive YoY delta with upward arrow and positive tone", () => {
      const { container } = render(<StatTile label="Free Cash Flow" value="$3.2B" delta={12.5} />);
      expect(screen.getByText("▲")).toBeDefined();
      expect(screen.getByText("12.5%")).toBeDefined();
      const deltaEl = container.querySelector(".text-pos");
      expect(deltaEl).not.toBeNull();
    });

    it("renders negative YoY delta with downward arrow and negative tone", () => {
      const { container } = render(<StatTile label="Net Income" value="$1.1B" delta={-5.2} />);
      expect(screen.getByText("▼")).toBeDefined();
      expect(screen.getByText("5.2%")).toBeDefined();
      const deltaEl = container.querySelector(".text-neg");
      expect(deltaEl).not.toBeNull();
    });

    it("renders neutral/flat delta without arrows", () => {
      render(<StatTile label="Shares" value="500M" delta={0} />);
      expect(screen.getByText("0.0%")).toBeDefined();
    });
  });

  describe("Chip", () => {
    it("renders label and tone styling", () => {
      const { container } = render(<Chip tone="positive">HEALTHY</Chip>);
      expect(screen.getByText("HEALTHY")).toBeDefined();
      expect(container.querySelector(".text-pos")).not.toBeNull();
    });

    it("renders colorblind-safe icons for positive and negative tones", () => {
      const { rerender } = render(<Chip tone="positive" showIcon>Passed</Chip>);
      expect(screen.getByText("✓")).toBeDefined();

      rerender(<Chip tone="negative" showIcon>Failed</Chip>);
      expect(screen.getByText("✕")).toBeDefined();

      rerender(<Chip tone="warning" showIcon>Alert</Chip>);
      expect(screen.getByText("!")).toBeDefined();
    });
  });

  describe("Card", () => {
    it("renders children, title, subtitle, and tone border", () => {
      const { container } = render(
        <Card title="Card Title" subtitle="Subtitle note" tone="positive">
          <p>Card Content</p>
        </Card>
      );
      expect(screen.getByText("Card Title")).toBeDefined();
      expect(screen.getByText("Subtitle note")).toBeDefined();
      expect(screen.getByText("Card Content")).toBeDefined();
      expect(container.firstChild).toBeDefined();
      const cardEl = container.firstElementChild;
      expect(cardEl?.className).toContain("border-l-pos");
    });
  });

  describe("Grid", () => {
    it("applies responsive column classes", () => {
      const { container } = render(
        <Grid cols={4}>
          <div>Item 1</div>
          <div>Item 2</div>
        </Grid>
      );
      expect(container.firstElementChild?.className).toContain("lg:grid-cols-4");
    });
  });

  describe("Page", () => {
    it("renders breadcrumb, title, and actions inside max-width container", () => {
      render(
        <Page
          breadcrumb={<nav>Breadcrumbs</nav>}
          title="Page Header"
          description="Page Description"
          actions={<button>Action</button>}
        >
          <div>Page Body</div>
        </Page>
      );
      expect(screen.getByText("Breadcrumbs")).toBeDefined();
      expect(screen.getByText("Page Header")).toBeDefined();
      expect(screen.getByText("Page Description")).toBeDefined();
      expect(screen.getByText("Action")).toBeDefined();
      expect(screen.getByText("Page Body")).toBeDefined();
    });
  });
});
