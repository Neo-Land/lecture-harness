"use client";

import { useEffect, useId, useState } from "react";
import type { VisualSpec } from "@/lib/api";

type Row = unknown[];
const rows = (value: unknown): Row[] => (Array.isArray(value) ? value.filter(Array.isArray) : []);
const strings = (value: unknown): string[] => (Array.isArray(value) ? value.map(String) : []);

/** Mermaid source for a concept map. Labels are quoted so slide text can't change the diagram's syntax. */
export function conceptMapSource(data: VisualSpec["data"]): string {
  const label = (text: unknown) => `"${String(text).replace(/[#"]/g, " ").replace(/[\r\n]+/g, " ")}"`;
  const nodes = strings(data.nodes);
  const id = (name: unknown) => `n${nodes.indexOf(String(name))}`;
  const edges = rows(data.edges).filter(([a, b]) => nodes.includes(String(a)) && nodes.includes(String(b)));
  return [
    "graph LR",
    ...nodes.map((n, i) => `  n${i}[${label(n)}]`),
    ...edges.map(([a, b, text]) => `  ${id(a)} -->${text ? `|${label(text)}|` : ""} ${id(b)}`),
  ].join("\n");
}

function ConceptMap({ data, title }: { data: VisualSpec["data"]; title: string }) {
  const id = useId().replace(/\W/g, "");
  const [svg, setSvg] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    import("mermaid")
      .then(async ({ default: mermaid }) => {
        // strict mode has Mermaid sanitize the SVG, since labels come from a model
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral" });
        const result = await mermaid.render(`map${id}`, conceptMapSource(data));
        if (live) setSvg(result.svg);
      })
      .catch(() => live && setSvg(null));
    return () => {
      live = false;
    };
  }, [data, id]);

  return (
    <>
      {svg && <div role="img" aria-label={`Concept map: ${title}`} dangerouslySetInnerHTML={{ __html: svg }} />}
      <details open={!svg}>
        <summary>Read as text</summary>
        <ul>
          {rows(data.edges).map(([a, b, text]) => (
            <li key={`${a}-${b}-${text}`}>
              {String(a)} {text ? `${String(text)} ` : "connects to "}
              {String(b)}
            </li>
          ))}
        </ul>
      </details>
    </>
  );
}

function Body({ visual }: { visual: VisualSpec }) {
  const { data } = visual;
  switch (visual.kind) {
    case "table":
      return (
        <table>
          <thead>
            <tr>
              {strings(data.columns).map((c) => (
                <th key={c} scope="col">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows(data.rows).map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td key={j}>{String(cell)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    case "timeline":
      return (
        <ol>
          {rows(data.events).map(([label, detail]) => (
            <li key={String(label)}>
              <strong>{String(label)}</strong>
              {detail ? `: ${String(detail)}` : ""}
            </li>
          ))}
        </ol>
      );
    case "key_terms":
      return (
        <dl>
          {rows(data.terms).flatMap(([term, definition]) => [
            <dt key={`t-${term}`}>{String(term)}</dt>,
            <dd key={`d-${term}`}>{String(definition)}</dd>,
          ])}
        </dl>
      );
    case "concept_map":
      return <ConceptMap data={data} title={visual.title} />;
  }
}

/** A verified visual with its citations. The model sends data; this decides how it looks. */
export function Visual({ visual, onCite }: { visual: VisualSpec; onCite: (slide: number) => void }) {
  return (
    <figure className="visual" style={{ marginInline: 0 }}>
      <figcaption>{visual.title}</figcaption>
      <Body visual={visual} />
      <span className="visual-sources">
        {visual.slides.map((n) => (
          <button key={n} type="button" className="cite" onClick={() => onCite(n)} aria-label={`Show slide ${n}`}>
            slide {n}
          </button>
        ))}
      </span>
    </figure>
  );
}
