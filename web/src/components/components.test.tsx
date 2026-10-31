import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { DeckDetail, VisualSpec } from "@/lib/api";
import { AskBox } from "./AskBox";
import { CheckNote } from "./CheckNote";
import { LectureView } from "./LectureView";
import { SyncButton } from "./SyncButton";
import { conceptMapSource, Visual } from "./Visuals";

const post = vi.hoisted(() => vi.fn());
vi.mock("@/lib/api", async (original) => ({
  ...(await original<typeof import("@/lib/api")>()),
  api: { POST: post },
}));

const slide = (number: number, text: string, extra = {}) => ({
  number,
  text,
  needs_ocr: false,
  has_image: false,
  ...extra,
});

const detail = (over: Partial<DeckDetail> = {}): DeckDetail => ({
  deck: {
    id: "d1",
    course: "CS 2",
    title: "Sorting",
    slides: [slide(1, "Intro text"), slide(2, "Merge sort text"), slide(3, "Quick sort text")],
  },
  summary: {
    abstract: [{ text: "Merge sort is fast.", slides: [2] }],
    visuals: [],
  },
  report: { passed: true, issues: [], claims_total: 1, claims_supported: 1 },
  attempts: 1,
  model: "claude",
  prompt_version: "1",
  ...over,
});

describe("LectureView", () => {
  it("clicking a citation shows that slide and highlights the claim", async () => {
    render(<LectureView detail={detail()} />);
    expect(screen.getByText("Intro text")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Show slide 2" }));
    expect(screen.getByText("Merge sort text")).toBeInTheDocument();
    expect(screen.getByText("Merge sort is fast.")).toHaveClass("active");
    expect(screen.getByRole("button", { name: "Show slide 2" })).toHaveAttribute("aria-pressed", "true");
  });

  it("uses the slide image with alt text when one exists", () => {
    const d = detail();
    d.deck.slides[0] = slide(1, "Intro text", { has_image: true });
    render(<LectureView detail={d} />);
    const image = screen.getByRole("img");
    expect(image).toHaveAttribute("src", expect.stringContaining("/decks/d1/slides/1/image"));
    expect(image).toHaveAttribute("alt", "Slide 1: Intro text");
  });

  it("previous and next stop at the ends", async () => {
    render(<LectureView detail={detail()} initialSlide={3} />);
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Previous" }));
    expect(screen.getByText("Slide 2 of 3")).toBeInTheDocument();
  });
});

describe("CheckNote", () => {
  it("states verified claims and revisions", () => {
    render(<CheckNote detail={detail({ attempts: 2 })} />);
    expect(screen.getByText(/1 of 1 claim checked against the slides, after 1 revision/)).toBeInTheDocument();
  });

  it("states removed claims", () => {
    const report = { passed: false, issues: [], claims_total: 3, claims_supported: 1 };
    render(<CheckNote detail={detail({ report })} />);
    expect(screen.getByText(/2 claims failed the check and were removed/)).toBeInTheDocument();
  });

  it("labels offline output as not AI", () => {
    render(<CheckNote detail={detail({ model: "extractive-offline" })} />);
    expect(screen.getByText(/not written by AI/)).toBeInTheDocument();
  });

  it("flags scanned slides", () => {
    const d = detail();
    d.deck.slides[1] = slide(2, "", { needs_ocr: true });
    render(<CheckNote detail={d} />);
    expect(screen.getByText(/Slide 2 is scanned/)).toBeInTheDocument();
  });
});

describe("AskBox", () => {
  it("says when the slides don't cover a question", async () => {
    post.mockResolvedValue({ data: { insufficient_evidence: true, claims: [], report: {} } });
    render(<AskBox course="CS 2" />);
    await userEvent.type(screen.getByLabelText("Question"), "photosynthesis");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText("Not covered in the slides.")).toBeInTheDocument();
    expect(post).toHaveBeenCalledWith("/ask", { body: { course: "CS 2", question: "photosynthesis" } });
  });

  it("links answers to their slides", async () => {
    const claims = [{ text: "It is fast.", sources: [{ deck_id: "d1", deck_title: "Sorting", slide: 2 }] }];
    post.mockResolvedValue({ data: { insufficient_evidence: false, claims, report: {} } });
    render(<AskBox course="CS 2" />);
    await userEvent.type(screen.getByLabelText("Question"), "speed");
    await userEvent.click(screen.getByRole("button", { name: "Ask" }));
    const link = await screen.findByRole("link", { name: "Sorting, slide 2" });
    expect(link).toHaveAttribute("href", "/decks/d1?slide=2");
  });
});

describe("Visuals", () => {
  const visual = (kind: VisualSpec["kind"], data: VisualSpec["data"]): VisualSpec => ({
    kind,
    title: "A visual",
    data,
    slides: [2],
  });

  it("renders a table and cites its slide", async () => {
    const onCite = vi.fn();
    render(<Visual visual={visual("table", { columns: ["Name"], rows: [["Merge"]] })} onCite={onCite} />);
    expect(screen.getByRole("columnheader", { name: "Name" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "Merge" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Show slide 2" }));
    expect(onCite).toHaveBeenCalledWith(2);
  });

  it("survives malformed data from the model", () => {
    render(<Visual visual={visual("table", { rows: "oops" })} onCite={() => {}} />);
    expect(screen.getByText("A visual")).toBeInTheDocument();
  });

  it("quotes concept map labels so slide text can't inject Mermaid syntax", () => {
    const source = conceptMapSource({
      nodes: ['A"] --> B[click', "C"],
      edges: [['A"] --> B[click', "C", "uses"], ["ghost", "C"]],
    });
    expect(source).toContain('n0["A ] --> B[click"]');
    expect(source).toContain('n0 -->|"uses"| n1');
    expect(source).not.toContain("ghost");
  });
});

describe("SyncButton", () => {
  it("reports new lectures and refreshes the course list", async () => {
    post.mockResolvedValue({ data: [{ deck_id: "a" }] });
    const onSynced = vi.fn();
    render(<SyncButton onSynced={onSynced} />);
    await userEvent.click(screen.getByRole("button", { name: "Sync with Canvas" }));
    expect(await screen.findByText("Added 1 new or updated lecture.")).toBeInTheDocument();
    expect(onSynced).toHaveBeenCalled();
  });

  it("shows the API's error", async () => {
    post.mockResolvedValue({ error: { detail: "Canvas rejected the token." } });
    render(<SyncButton onSynced={() => {}} />);
    await userEvent.click(screen.getByRole("button", { name: "Sync with Canvas" }));
    expect(await screen.findByText("Canvas rejected the token.")).toBeInTheDocument();
  });
});
