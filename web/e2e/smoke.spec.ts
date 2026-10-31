// The main flow in a real browser, with the API mocked: open a lecture, click a citation, ask a question.
import { expect, test } from "@playwright/test";

const slide = (number: number, text: string) => ({ number, text, needs_ocr: false, has_image: false });
const report = { passed: true, issues: [], claims_total: 1, claims_supported: 1 };
const deck = { id: "d1", course: "CS 2", title: "Sorting", slides: [slide(1, "Intro"), slide(2, "Merge sort details")] };

test("read a lecture and ask a question", async ({ page }) => {
  await page.route("http://localhost:8000/**", (route) => {
    const headers = { "access-control-allow-origin": "*", "access-control-allow-headers": "*" };
    const path = new URL(route.request().url()).pathname;
    if (route.request().method() === "OPTIONS") return route.fulfill({ status: 204, headers });
    const json = (body: unknown) => route.fulfill({ json: body, headers });
    if (path === "/config") return json({ canvas: false, demo: false });
    if (path === "/courses") return json([{ course: "CS 2", decks: 1 }]);
    if (path === "/courses/CS%202/decks") return json([{ id: "d1", title: "Sorting", slides: 2 }]);
    if (path === "/decks/d1") {
      const summary = { abstract: [{ text: "Merge sort is fast.", slides: [2] }], visuals: [] };
      return json({ deck, summary, report, attempts: 1, model: "m", prompt_version: "1" });
    }
    if (path === "/ask") return json({ insufficient_evidence: true, claims: [], report });
    return route.fulfill({ status: 404, headers });
  });

  await page.goto("/");
  await page.getByRole("link", { name: /CS 2/ }).click();
  await page.getByRole("link", { name: "Sorting" }).click();

  await expect(page.getByText("1 of 1 claim checked against the slides")).toBeVisible();
  await page.getByRole("button", { name: "Show slide 2" }).click();
  await expect(page.getByText("Merge sort details")).toBeVisible();

  await page.goto("/courses/CS%202");
  await page.getByLabel("Question").fill("photosynthesis");
  await page.getByRole("button", { name: "Ask" }).press("Enter");
  await expect(page.getByText("Not covered in the slides.")).toBeVisible();
});
