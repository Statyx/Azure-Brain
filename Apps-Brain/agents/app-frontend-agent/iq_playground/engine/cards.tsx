
import { Fragment, useEffect, useState, type ReactNode } from "react";
import type { AuthorizationStatus, EmailDraft, PersonRef, Report, ReportChart, ScenarioOption, SourceRef, CoworkEvent, CoworkTaskStatus, CoworkTask } from "../types/scenario";
import { IconCheck, IconChevronDown, IconCopy, IconDownload, IconInfo, IconMail, IconMic, IconMore, IconPlus, IconRefresh, IconSend, IconShield, IconSparkle, IconThumbDown, IconThumbUp } from "./icons";
import { sourceSystemMeta } from "./sourceMeta";
export function ReportView({ report }: { report: Report }) {
  return (
    <div>
      <p className="text-xs text-ink-muted">Reasoning complete in {report.reasoningSteps} steps</p>
      <p className="mt-2">{report.scanSummary}</p>

      <h3 className="mt-4 text-base font-semibold text-ink">To review first</h3>

      <div className="mt-2 space-y-4">
        {report.items.map((item) => (
          <div key={item.title}>
            <p className="font-semibold text-ink">{item.title}</p>
            <p className="mt-1 text-xs text-ink-muted">{item.source}</p>
            <blockquote className="mt-1 border-l-2 border-hairline pl-3 text-ink-muted italic">
              &ldquo;{item.quote}&rdquo;
            </blockquote>
            <p className="mt-1 text-ink-muted">{item.note}</p>
          </div>
        ))}
      </div>

      <h3 className="mt-4 text-base font-semibold text-ink">My take</h3>
      <p className="mt-1">{report.verdictIntro}</p>
      <ol className="mt-1 list-decimal pl-5 space-y-1">
        {report.verdictList.map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ol>
    </div>
  );
}

/* ---------- Report visual under an answer ---------- */

const REPORT_ALERT = "#c50f1f";
const REPORT_OK = "#c23fa0";

/** A Power BI-style card: KPI tiles, then one bar per row against a dashed target line. It draws
 *  what Fabric already computed — positions are scaled from the scenario values, nothing is derived. */
export function ReportChartCard({ chart }: { chart: ReportChart }) {
  const pct = (v: number) => `${Math.max(0, Math.min(100, (v / chart.axisMax) * 100))}%`;
  return (
    <figure className="mt-3 overflow-hidden rounded-lg border border-hairline bg-white" aria-label={chart.title}>
      <div className="flex items-center justify-between gap-3 border-b border-hairline px-3 py-2">
        <div className="min-w-0">
          <p className="text-xs font-semibold text-ink">{chart.title}</p>
          {chart.subtitle && <p className="text-2xs text-ink-muted">{chart.subtitle}</p>}
        </div>
        <span className="flex shrink-0 items-center gap-1.5 text-2xs text-ink-muted">
          <span className="grid h-4 w-4 place-items-center rounded-sm bg-[#f2c811] text-2xs font-bold text-black" aria-hidden>
            ▮
          </span>
          Power BI
        </span>
      </div>

      {chart.kpis && chart.kpis.length > 0 && (
        <div className="grid gap-px border-b border-hairline bg-hairline" style={{ gridTemplateColumns: `repeat(${chart.kpis.length}, minmax(0, 1fr))` }}>
          {chart.kpis.map((kpi) => (
            <div key={kpi.label} className="bg-white px-3 py-2">
              <p className="text-2xs text-ink-muted">{kpi.label}</p>
              <p className="text-sm font-semibold" style={{ color: kpi.tone === "alert" ? REPORT_ALERT : undefined }}>
                {kpi.value}
              </p>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-3 px-3 py-3">
        {chart.bars.map((bar) => {
          const breach = bar.breach === true;
          return (
            <div key={bar.label}>
              <div className="flex items-baseline justify-between gap-2 text-2xs">
                <span className="font-semibold text-ink">{bar.label}</span>
                <span className="text-ink-muted">{bar.detail}</span>
              </div>
              <div className="relative mt-1 h-4 rounded-sm bg-surface">
                {bar.previous !== undefined && (
                  <div className="absolute inset-y-0 left-0 rounded-sm bg-black/10" style={{ width: pct(bar.previous) }} title={bar.previousDisplay} />
                )}
                <div
                  className="absolute inset-y-1 left-0 rounded-sm"
                  style={{ width: pct(bar.value), background: breach ? REPORT_ALERT : REPORT_OK }}
                />
                {bar.target !== undefined && (
                  <div className="absolute -inset-y-0.5 w-0 border-l-2 border-dashed border-ink" style={{ left: pct(bar.target) }} />
                )}
              </div>
              <div className="mt-0.5 flex items-baseline gap-2 text-2xs">
                <span className="font-semibold" style={{ color: breach ? REPORT_ALERT : undefined }}>{bar.display}</span>
                {bar.previousDisplay && <span className="text-ink-muted">prior period {bar.previousDisplay}</span>}
              </div>
            </div>
          );
        })}
      </div>

      <figcaption className="flex flex-wrap items-center justify-between gap-2 border-t border-hairline bg-surface px-3 py-1.5 text-2xs text-ink-muted">
        <span className="flex items-center gap-3">
          <span className="flex items-center gap-1"><span className="inline-block h-2 w-3 rounded-sm" style={{ background: REPORT_ALERT }} />below target</span>
          <span className="flex items-center gap-1"><span className="inline-block h-2 w-3 rounded-sm bg-black/10" />prior period</span>
          {chart.targetLabel && (
            <span className="flex items-center gap-1"><span className="inline-block h-3 w-0 border-l-2 border-dashed border-ink" />{chart.targetLabel}</span>
          )}
        </span>
        <span>{chart.source}</span>
      </figcaption>
    </figure>
  );
}

/* ---------- Caldova IQ / Copilot identity ---------- */

export function getIdentity(mention?: string) {
  if (mention === "CaldovaIQ") {
    return { name: "Caldova IQ", color: "#0f7a6c" };
  }
  if (mention === "FabricAgent") {
    return { name: "Sale Forecast Agent", color: "#c23fa0", icon: "/images/fabric-logo.png" };
  }
  return { name: "Microsoft 365 Copilot", color: "#6f5bd6" };
}

export function AgentAvatar({ name, color, icon }: { name: string; color: string; icon?: string }) {
  if (icon) {
    return (
      <span className="w-6 h-6 rounded-md shrink-0 overflow-hidden bg-white" aria-hidden>
        <img src={icon} alt="" width={24} height={24} className="w-full h-full object-contain" />
      </span>
    );
  }
  return (
    <span
      className="w-6 h-6 rounded-md shrink-0 flex items-center justify-center text-2xs font-semibold text-white"
      style={{ background: color }}
      aria-hidden
    >
      {name.charAt(0)}
    </span>
  );
}

/* ---------- Cowork replay UI (Veloa Performance GTM session) ---------- */

export function ThinkingDots() {
  return (
    <span className="inline-flex items-center gap-0.5" aria-hidden>
      <span className="w-1 h-1 rounded-full bg-[#605E5C] animate-bounce [animation-delay:-0.2s]" />
      <span className="w-1 h-1 rounded-full bg-[#605E5C] animate-bounce [animation-delay:-0.1s]" />
      <span className="w-1 h-1 rounded-full bg-[#605E5C] animate-bounce" />
    </span>
  );
}

/** Collapsible "Thinking" reasoning block \u2014 collapsed by default, matches the real Cowork
 *  pattern of surfacing the agent's internal reasoning as optional, expandable detail rather
 *  than as part of the main narrative. */
export function VeloaThinkingBlock({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="max-w-xl rounded-lg border border-[#E1DFDD] bg-[#FAF9F8] px-3 py-2 animate-fade-in-up">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-2 text-left"
      >
        <span className="text-2xs font-medium text-[#605E5C] inline-flex items-center gap-1.5">
          <IconSparkle /> Thinking
        </span>
        <span
          className={`inline-block transition-transform text-[#605E5C] ${open ? "rotate-0" : "-rotate-90"}`}
          aria-hidden
        >
          <IconChevronDown />
        </span>
      </button>
      {open && <p className="mt-1.5 text-xs italic text-[#605E5C] leading-relaxed">{text}</p>}
    </div>
  );
}

/* Collapsible Workspace panel section \u2014 thin separators, no card shadow, matches Fluent
   disclosure pattern (chevron + label + count chip). */
export function WorkspaceSection({
  title,
  count,
  defaultOpen = true,
  children,
}: {
  title: string;
  count?: string;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-[#E1DFDD] py-3 last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-2 text-left"
      >
        <span className="text-xs font-semibold text-[#252423]">{title}</span>
        <span className="flex items-center gap-1.5 shrink-0 text-[#605E5C]">
          {count && (
            <span className="rounded-full bg-[#F3F2F1] px-2 py-0.5 text-2xs font-medium">{count}</span>
          )}
          <span
            className={`inline-block transition-transform ${open ? "rotate-0" : "-rotate-90"}`}
            aria-hidden
          >
            <IconChevronDown />
          </span>
        </span>
      </button>
      {open && <div className="mt-2.5 space-y-1.5">{children}</div>}
    </div>
  );
}

/** Renders a single campaign image card using the real brand asset photo. Clickable to open a
 *  large preview, mirroring the PPT deliverable card's open-preview interaction. */
export function VeloaImageCard({ file, caption, onOpen }: { file: string; caption: string; onOpen?: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="max-w-xs w-full rounded-lg border border-[#E1DFDD] overflow-hidden animate-fade-in-up text-left cursor-pointer hover:border-[#183A2A]/40 transition-colors"
    >
      <img
        src={`/images/veloa/${file}`}
        alt={caption}
        className="h-28 w-full object-cover"
      />
      <div className="px-2.5 py-2">
        <p className="text-xs font-medium text-[#252423] truncate">{file}</p>
        <p className="text-2xs text-[#605E5C]">{caption}</p>
      </div>
    </button>
  );
}

/** Large preview modal opened by clicking a campaign visual card \u2014 mirrors the PPT preview
 *  modal's header (icon, name, download, close) with a single large real photo instead of slides. */
export function VeloaImagePreviewModal({
  file,
  caption,
  onClose,
}: {
  file: string;
  caption: string;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const src = `/images/veloa/${file}`;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex flex-col" role="dialog" aria-modal="true">
      <div className="flex items-center justify-between gap-3 px-4 md:px-6 py-3 bg-white border-b border-[#E1DFDD]">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="w-8 h-8 rounded-md bg-[#183A2A] text-white flex items-center justify-center text-2xs font-semibold shrink-0">
            IMG
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-[#252423] truncate">{file}</p>
            <p className="text-2xs text-[#605E5C] truncate">{caption}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <a
            href={src}
            download={file}
            className="inline-flex items-center gap-1.5 rounded-md bg-[#183A2A] text-white px-3.5 py-1.5 text-xs font-medium hover:bg-[#183A2A]/85 transition-colors"
          >
            Download
          </a>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-[#E1DFDD] p-1.5 text-[#605E5C] hover:text-[#252423]"
            aria-label="Close preview"
          >
            <IconClose />
          </button>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex items-center justify-center px-3 md:px-10 py-4 md:py-6">
        <img
          src={src}
          alt={caption}
          className="max-w-full max-h-full w-auto h-auto rounded-lg shadow-2xl object-contain"
        />
      </div>
    </div>
  );
}

/** Renders the 14-slide QA filmstrip once the deck has been assembled, with a short QA summary
 *  line underneath (matches the spec's SlideStrip component). */
export function VeloaSlideStrip({ count, qa }: { count: number; qa: string }) {
  return (
    <div className="max-w-xl rounded-lg border border-[#E1DFDD] p-3 animate-fade-in-up">
      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="w-14 h-9 shrink-0 rounded bg-[#F3F2F1] border border-[#E1DFDD] flex items-center justify-center text-[0.5625rem] font-medium text-[#605E5C]"
          >
            {i + 1}
          </div>
        ))}
      </div>
      <p className="mt-2 text-2xs text-[#605E5C]">QA pass: {qa}</p>
    </div>
  );
}

/* ---------- Veloa Performance deck preview (PowerPoint preview + download) ----------
   Renders a lightweight, in-browser preview of the 14-slide deck Cowork generated — content
   taken directly from the real generated .pptx — plus a genuine download of that file, styled
   to sit close to the real Microsoft 365 file-preview experience (header with file icon, name,
   download and close; large slide stage; bottom thumbnail filmstrip; prev/next navigation). */

export const veloaDeckFileUrl = "/downloads/Veloa-Performance-GTM-Plan.pptx";

/** Real, pixel-perfect renders of the 14 slides from the actual generated .pptx (rendered via
 *  LibreOffice → PDF → PNG at 1921×1080), so the in-browser preview shows the genuine deck
 *  rather than a recreated approximation. */
export const veloaSlideCount = 14;
export const veloaSlideImgSrc = (index: number) =>
  `/downloads/veloa-slides-real/slide-${String(index + 1).padStart(2, "0")}.png`;

/** Renders one full slide image for the stage / thumbnails. */
export function VeloaSlideStage({ index }: { index: number }) {
  return (
    <img
      src={veloaSlideImgSrc(index)}
      alt={`Slide ${index + 1} of the Veloa Performance GTM deck`}
      className="w-full h-full object-contain bg-white"
    />
  );
}

/** Small filmstrip thumbnail \u2014 the same real slide image, scaled down, matching the real
 *  Microsoft 365 file preview's slide-panel thumbnails. */
export function VeloaSlideThumb({ index, active, onClick }: { index: number; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`relative w-24 md:w-28 aspect-video shrink-0 rounded-md overflow-hidden border-2 transition-colors ${
        active ? "border-[#183A2A]" : "border-transparent hover:border-[#E1DFDD]"
      }`}
    >
      <VeloaSlideStage index={index} />
      <span className="absolute bottom-0.5 right-1 text-[0.5rem] font-medium text-white bg-black/50 rounded px-1">
        {index + 1}
      </span>
    </button>
  );
}


/** Full preview modal opened from the deliverable card — mirrors the real Cowork / Microsoft 365
 *  file-preview experience: header (file icon, name, download, close), a large slide stage,
 *  prev/next arrows and a bottom thumbnail filmstrip. */
export function VeloaPptxPreviewModal({ onClose }: { onClose: () => void }) {
  const [slide, setSlide] = useState(0);
  const total = veloaSlideCount;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") setSlide((s) => Math.min(total - 1, s + 1));
      if (e.key === "ArrowLeft") setSlide((s) => Math.max(0, s - 1));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [total, onClose]);

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex flex-col" role="dialog" aria-modal="true">
      <div className="flex items-center justify-between gap-3 px-4 md:px-6 py-3 bg-white border-b border-[#E1DFDD]">
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="w-8 h-8 rounded-md bg-[#C43E1C] text-white flex items-center justify-center text-2xs font-semibold shrink-0">
            PPT
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium text-[#252423] truncate">Veloa-Performance-GTM-Plan.pptx</p>
            <p className="text-2xs text-[#605E5C]">
              Slide {slide + 1} of {total}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <a
            href={veloaDeckFileUrl}
            download="Veloa-Performance-GTM-Plan.pptx"
            className="inline-flex items-center gap-1.5 rounded-md bg-[#183A2A] text-white px-3.5 py-1.5 text-xs font-medium hover:bg-[#183A2A]/85 transition-colors"
          >
            Download
          </a>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-[#E1DFDD] p-1.5 text-[#605E5C] hover:text-[#252423]"
            aria-label="Close preview"
          >
            <IconClose />
          </button>
        </div>
      </div>

      <div className="flex-1 min-h-0 flex items-center justify-center px-3 md:px-10 py-4 md:py-6 relative">
        <button
          type="button"
          onClick={() => setSlide((s) => Math.max(0, s - 1))}
          disabled={slide === 0}
          className="hidden sm:flex absolute left-3 md:left-6 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-white/90 items-center justify-center text-[#252423] shadow disabled:opacity-30"
          aria-label="Previous slide"
        >
          <span aria-hidden>{"‹"}</span>
        </button>

        <div className="w-full max-w-4xl aspect-video rounded-lg overflow-hidden shadow-2xl bg-white">
          <VeloaSlideStage index={slide} />
        </div>

        <button
          type="button"
          onClick={() => setSlide((s) => Math.min(total - 1, s + 1))}
          disabled={slide === total - 1}
          className="hidden sm:flex absolute right-3 md:right-6 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-white/90 items-center justify-center text-[#252423] shadow disabled:opacity-30"
          aria-label="Next slide"
        >
          <span aria-hidden>{"›"}</span>
        </button>
      </div>

      <div className="bg-white border-t border-[#E1DFDD] px-4 md:px-6 py-2.5 overflow-x-auto">
        <div className="flex items-center gap-2 w-max">
          {Array.from({ length: veloaSlideCount }, (_, i) => (
            <VeloaSlideThumb key={i} index={i} active={i === slide} onClick={() => setSlide(i)} />
          ))}
        </div>
      </div>
    </div>
  );
}
/** Final deliverable card \u2014 the finished PowerPoint file, styled like a Fluent file chip but
 *  larger and with a "Ready" status, matching the spec's DeliverableCard. */
export function VeloaDeliverableCard({
  file,
  slides,
  status,
  onOpenPreview,
}: {
  file: string;
  slides: number;
  status: string;
  onOpenPreview?: () => void;
}) {
  return (
    <div className="max-w-sm w-full rounded-lg border border-[#E1DFDD] bg-[#FAF9F8] px-4 py-3 flex items-center gap-3 animate-fade-in-up hover:border-[#183A2A]/40 hover:bg-white transition-colors">
      <button type="button" onClick={onOpenPreview} className="flex items-center gap-3 min-w-0 flex-1 text-left cursor-pointer">
        <span className="w-9 h-9 rounded-md bg-[#C43E1C] text-white flex items-center justify-center text-2xs font-semibold shrink-0">
          PPT
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-[#252423] truncate">{file}</p>
          <p className="text-2xs text-[#107C41] font-medium">
            {slides} slides {"\u00b7"} {status}
          </p>
        </div>
      </button>
      <span className="text-2xs text-[#605E5C] shrink-0">Preview</span>
      <a
        href={veloaDeckFileUrl}
        download="Veloa-Performance-GTM-Plan.pptx"
        onClick={(e) => e.stopPropagation()}
        title="Download Veloa-Performance-GTM-Plan.pptx"
        aria-label="Download Veloa-Performance-GTM-Plan.pptx"
        className="shrink-0 rounded-md border border-[#E1DFDD] p-1.5 text-[#605E5C] hover:text-[#183A2A] hover:border-[#183A2A]/40 hover:bg-white transition-colors"
      >
        <IconDownload />
      </a>
    </div>
  );
}

export function CoworkTaskView({
  events,
  eventIdx,
  status,
  taskStatus,
  tasks,
  skillsUsed,
  onClose,
}: {
  events: CoworkEvent[];
  eventIdx: number;
  status: "running" | "complete";
  taskStatus: Record<number, CoworkTaskStatus>;
  /** Macro tasks tracked in the sticky Workspace panel — supplied by the active scenario. */
  tasks: CoworkTask[];
  /** Agent skill badges shown under the Workspace panel — supplied by the active scenario. */
  skillsUsed: string[];
  onClose: () => void;
}) {
  const visibleEvents = status === "complete" ? events : events.slice(0, eventIdx + 1);
  const [pptxPreviewOpen, setPptxPreviewOpen] = useState(false);
  const [imagePreview, setImagePreview] = useState<{ file: string; caption: string } | null>(null);

  return (
    <div className="flex-1 flex overflow-hidden">
      {pptxPreviewOpen && <VeloaPptxPreviewModal onClose={() => setPptxPreviewOpen(false)} />}
      {imagePreview && (
        <VeloaImagePreviewModal
          file={imagePreview.file}
          caption={imagePreview.caption}
          onClose={() => setImagePreview(null)}
        />
      )}
      <div className="flex-1 flex flex-col overflow-hidden bg-white min-w-0">
        <div className="flex-1 overflow-y-auto px-6 md:px-8 py-6 md:py-8">
          <div className="max-w-4xl mx-auto">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center gap-1.5 text-sm text-[#605E5C] hover:text-[#252423] mb-4"
            >
              <span aria-hidden>{"\u2190"}</span> Back to Cowork
            </button>

            <div className="flex items-start justify-between gap-3 pb-4 border-b border-[#E1DFDD]">
              <div>
                <h1 className="text-xl! md:text-2xl! font-semibold! text-[#252423] leading-tight!">
                  Veloa Performance {"\u2014"} GTM Plan
                </h1>
                <p className="text-xs text-[#605E5C] mt-1">Just now {"\u00b7"} Cowork task</p>
              </div>
              <div className="hidden sm:flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={onClose}
                  className="rounded-md border border-[#E1DFDD] px-3 py-1.5 text-xs font-medium text-[#605E5C] hover:text-[#252423]"
                >
                  Cancel
                </button>
              </div>
            </div>

            <div className="mt-5 space-y-5">
              {/* Opening one-shot prompt with the 4 brand-asset attachments, styled as a
                  right-aligned user bubble matching the spec's UserBubble component. */}
              <div className="flex justify-end">
                <div className="max-w-xl rounded-2xl bg-[#F3F2F1] px-4 py-3 animate-fade-in-up">
                  <p className="text-sm text-[#252423] leading-relaxed">
                    Give me the GTM plan for this marketing campaign. Following the approved
                    inventory reallocation to optimize product availability across priority
                    regions, define how marketing, sales and retail operations will execute the
                    campaign between July 21 and July 26, 2026 to maximize revenue and customer
                    engagement.
                  </p>
                </div>
              </div>

              {visibleEvents.map((event, i) => {
                const isCurrent = i === eventIdx && status !== "complete";
                switch (event.kind) {
                  case "thinking":
                    return <VeloaThinkingBlock key={i} text={event.text} />;
                  case "assistant":
                    return (
                      <p key={i} className="text-sm text-ink leading-relaxed animate-fade-in-up">
                        {event.text}
                      </p>
                    );
                  case "step":
                    return (
                      <div key={i} className="space-y-1.5 animate-fade-in-up">
                        <p className="text-xs text-[#605E5C] inline-flex items-center gap-1.5">
                          <IconSparkle /> {event.label}
                          {isCurrent && status === "running" && <ThinkingDots />}
                        </p>
                        {event.substeps && (!isCurrent || true) && (
                          <ul className="ml-5 space-y-1">
                            {event.substeps.map((s) => (
                              <li key={s} className="text-2xs text-[#605E5C] flex items-center gap-1.5">
                                <IconCheck /> {s}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    );
                  case "image":
                    return (
                      <VeloaImageCard
                        key={i}
                        file={event.file}
                        caption={event.caption}
                        onOpen={() => setImagePreview({ file: event.file, caption: event.caption })}
                      />
                    );
                  case "slides":
                    return <VeloaSlideStrip key={i} count={event.count} qa={event.qa} />;
                  case "deliverable":
                    return (
                      <VeloaDeliverableCard
                        key={i}
                        file={event.file}
                        slides={event.slides}
                        status={event.status}
                        onOpenPreview={() => setPptxPreviewOpen(true)}
                      />
                    );
                  default:
                    return null;
                }
              })}

              {status === "complete" && <p className="text-xs text-[#605E5C]">Task complete.</p>}
            </div>
          </div>
        </div>

        {/* Thin, full-width composer \u2014 stays visible while Cowork works, matching the real product. */}
        <div className="border-t border-[#E1DFDD] px-6 md:px-8 py-3">
          <div className="max-w-4xl mx-auto flex items-center gap-2.5 rounded-full border border-[#E1DFDD] px-4 py-2 text-[#605E5C]">
            <IconPlus />
            <span className="flex-1 text-sm truncate">
              {status === "complete" ? "Ask a follow-up question\u2026" : "We\u2019re working on it. What\u2019s next?"}
            </span>
            <IconMic />
            <span className="w-7 h-7 rounded-full bg-[#F3F2F1] flex items-center justify-center text-[#605E5C]">
              <IconSend />
            </span>
          </div>
        </div>
      </div>

      {/* Workspace \u2014 sticky Tasks panel (4 macro tasks) plus Skills used, matching the spec's
          sticky TaskPanel + Skills badges layout. */}
      <aside className="hidden lg:flex w-80 shrink-0 flex-col border-l border-[#E1DFDD] overflow-y-auto px-4 py-5">
        <h2 className="text-sm! font-semibold! text-[#252423] leading-tight! mb-1">Workspace</h2>

        <WorkspaceSection
          title="Tasks"
          count={`${Object.values(taskStatus).filter((s) => s === "done").length}/${tasks.length}`}
        >
          <ul className="space-y-2">
            {tasks.map((task) => {
              const st = taskStatus[task.id] ?? "pending";
              return (
                <li key={task.id} className="flex items-center gap-2.5">
                  <span
                    className={`w-3.5 h-3.5 rounded-full flex items-center justify-center shrink-0 ${
                      st === "done"
                        ? "bg-[#107C41] text-white"
                        : st === "in_progress"
                        ? "border-2 border-[#252423]"
                        : "bg-white text-[#605E5C] border border-[#E1DFDD]"
                    }`}
                    aria-hidden
                  >
                    {st === "done" && <span className="text-[0.5625rem]">{"\u2713"}</span>}
                  </span>
                  <div className="min-w-0">
                    <p
                      className={`text-xs ${
                        st === "in_progress" ? "font-semibold text-[#252423]" : st === "done" ? "text-[#252423]" : "text-[#605E5C]"
                      }`}
                    >
                      {task.title}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        </WorkspaceSection>

        <WorkspaceSection title="Skills and plugins">
          <div className="flex flex-wrap gap-1.5">
            {skillsUsed.map((skill) => (
              <span
                key={skill}
                className="inline-flex items-center rounded-md border border-[#E1DFDD] bg-white px-2.5 py-1 text-2xs font-medium text-[#252423]"
              >
                {skill}
              </span>
            ))}
          </div>
        </WorkspaceSection>
      </aside>
    </div>
  );
}
export function PersonCard({ person }: { person: PersonRef }) {
  return (
    <div className="mt-3 flex items-center gap-4 rounded-xl border border-hairline bg-white px-4 py-3.5">
      <div className="min-w-0 flex-1">
        <p className="truncate text-base font-medium text-ink">{person.name}</p>
        <p className="truncate text-xs text-ink-muted mt-1">
          {person.title} <span aria-hidden>{"\u00b7"}</span> {person.sub}
        </p>
        <p className="truncate text-xs text-ink-muted">{person.location}</p>
      </div>
      <span
        className="w-14 h-14 shrink-0 rounded-full flex items-center justify-center text-base font-semibold text-white"
        style={{ background: person.color }}
        aria-hidden
      >
        {person.initials}
      </span>
    </div>
  );
}

/** Read-only Corporate Inventory Policy reference, opened from the "Review approval policy" action
 *  offered alongside "Request approval from the approver" \u2014 lets the user inspect the governance rule
 *  without leaving the current step or advancing the scripted conversation. */
export function ApprovalPolicyModal({ authorization, onClose }: { authorization: AuthorizationStatus; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 px-4" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-xl border border-hairline bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-hairline px-5 py-3.5">
          <p className="text-sm font-semibold text-ink">Corporate Inventory Policy</p>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-ink-muted hover:bg-surface"
            aria-label="Close"
          >
            <IconClose />
          </button>
        </div>

        <div className="space-y-4 px-5 py-4 text-sm">
          <p className="text-ink-muted">
            Governs who may create and execute regional inventory transfers, based on the share of available
            regional stock being moved.
          </p>

          <div className="overflow-hidden rounded-lg border border-hairline">
            <div className="flex items-center justify-between border-b border-hairline bg-[#FAF9F8] px-3 py-2 text-xs font-semibold text-ink-muted">
              <span>Transfer size</span>
              <span>Required authorization</span>
            </div>
            <div className="flex items-center justify-between px-3 py-2.5">
              <span className="text-ink">0{"\u2013"}{authorization.thresholdPercent}% of regional stock</span>
              <span className="font-medium text-[#0f7a6c]">Self-approval</span>
            </div>
            <div className="flex items-center justify-between border-t border-hairline px-3 py-2.5">
              <span className="text-ink">
                {"\u003e"}
                {authorization.thresholdPercent}% of regional stock
              </span>
              <span className="font-medium text-[#b3261e]">Executive approval</span>
            </div>
          </div>

          <div className="rounded-lg bg-[#FFF4CE]/60 px-3 py-2.5 text-xs text-ink">
            This proposed transfer represents <strong>{authorization.transferPercent}%</strong> of available
            regional stock {"\u2014"} above the {authorization.thresholdPercent}% self-approval threshold, so
            executive approval from <strong>{authorization.approver}</strong> is required before SAP can create
            the final transfer order.
          </div>

          <p className="text-xs text-ink-muted">
            Source: Compliance Agent (WorkIQ) {"\u2014"} internal policy setting self-approval limits for
            regional stock transfers by percentage of available stock, and the required approver above each
            threshold.
          </p>
        </div>
      </div>
    </div>
  );
}

export function EmailDraftCard({
  draft,
  sent,
  sending,
  onSend,
  onSelectSource,
}: {
  draft: EmailDraft;
  sent: boolean;
  sending: boolean;
  onSend: () => void;
  onSelectSource: (source: SourceRef) => void;
}) {
  return (
    <div className="mt-3 rounded-2xl border border-hairline bg-white overflow-hidden">
      <div className="flex items-center justify-between gap-3 px-4 py-3 border-b border-hairline">
        <div className="flex items-center gap-2 min-w-0 text-ink-muted">
          <span className="shrink-0 w-8 h-8 rounded-lg bg-surface flex items-center justify-center">
            <IconMail />
          </span>
          <p className="truncate text-sm font-semibold text-ink">{draft.subject}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            disabled
            className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-hairline bg-white px-3 py-1.5 text-xs font-medium text-ink-muted"
          >
            <IconMail />
            Open
          </button>
          <button
            type="button"
            onClick={onSend}
            disabled={sent || sending}
            className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-medium transition-colors ${
              sent
                ? "bg-[#e6f4ea] text-[#146c2e]"
                : "bg-ink text-white hover:bg-ink/85 disabled:opacity-60"
            }`}
          >
            {sent ? <IconCheck /> : <IconSend />}
            {sent ? "Sent" : sending ? "Sending..." : "Send"}
          </button>
        </div>
      </div>

      <div className="px-4 py-3 text-sm">
        <div className="flex items-center gap-2 border-b border-hairline py-2">
          <span className="w-10 shrink-0 text-ink-muted text-xs">To:</span>
          <span className="text-ink">{draft.to}</span>
        </div>
        {draft.cc && (
          <div className="flex items-center gap-2 border-b border-hairline py-2">
            <span className="w-10 shrink-0 text-ink-muted text-xs">Cc:</span>
            <span className="text-ink">{draft.cc}</span>
          </div>
        )}
        <div className="flex items-center justify-between gap-2 border-b border-hairline py-2.5">
          <span className="font-medium text-ink">{draft.subject}</span>
          <span className="shrink-0 text-[#0f6cbd]">
            <IconShield />
          </span>
        </div>
        <div className="pt-3 space-y-3 text-ink">
          {draft.bodyParagraphs.map((p, idx) => (
            <p key={idx}>{p}</p>
          ))}
        </div>

        {draft.references && draft.references.length > 0 && (
          <div className="mt-3 border-t border-hairline pt-3">
            <SourceChips sources={draft.references} onSelect={onSelectSource} />
          </div>
        )}
      </div>

      {sent && (
        <div className="border-t border-hairline px-4 py-2.5 text-xs text-[#146c2e] bg-[#f2faf4] flex items-center gap-1.5">
          <IconCheck />
          {"Sent to "}
          {draft.to}
        </div>
      )}
    </div>
  );
}

export function MessageActionBar({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const [reaction, setReaction] = useState<"up" | "down" | null>(null);

  const handleCopy = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(text).catch(() => {});
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="mt-3 flex items-center gap-1 border-t border-hairline pt-2.5 text-ink-muted">
      <button
        type="button"
        onClick={handleCopy}
        aria-label="Copy response"
        className="rounded-md p-1.5 hover:bg-hairline/30 hover:text-ink transition-colors"
      >
        {copied ? <span className="text-xs px-0.5">{"\u2713"}</span> : <IconCopy />}
      </button>
      <button
        type="button"
        onClick={() => setReaction(reaction === "up" ? null : "up")}
        aria-label="Good response"
        className={`rounded-md p-1.5 hover:bg-hairline/30 transition-colors ${reaction === "up" ? "text-ink" : "hover:text-ink"}`}
      >
        <IconThumbUp />
      </button>
      <button
        type="button"
        onClick={() => setReaction(reaction === "down" ? null : "down")}
        aria-label="Poor response"
        className={`rounded-md p-1.5 hover:bg-hairline/30 transition-colors ${reaction === "down" ? "text-ink" : "hover:text-ink"}`}
      >
        <IconThumbDown />
      </button>
      <button
        type="button"
        aria-label="Regenerate"
        className="rounded-md p-1.5 hover:bg-hairline/30 hover:text-ink transition-colors"
      >
        <IconRefresh />
      </button>
      <button
        type="button"
        aria-label="More options"
        className="rounded-md p-1.5 hover:bg-hairline/30 hover:text-ink transition-colors"
      >
        <IconMore />
      </button>
      <span className="mx-1 h-4 w-px bg-hairline" aria-hidden />
      <button
        type="button"
        aria-label="About this response"
        className="rounded-md p-1.5 hover:bg-hairline/30 hover:text-ink transition-colors"
      >
        <IconInfo />
      </button>
    </div>
  );
}

export function SourceChips({
  sources,
  onSelect,
}: {
  sources?: SourceRef[];
  onSelect: (source: SourceRef) => void;
}) {
  if (!sources || sources.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap items-center gap-1.5">
      <span className="flex items-center gap-1 text-xs font-medium text-ink-muted">
        <IconSparkle />
        Sources
      </span>
      {sources.map((src) => (
        <button
          key={src.id}
          type="button"
          onClick={() => onSelect(src)}
          className="flex items-center gap-1.5 rounded-full border border-hairline bg-surface px-2.5 py-1 text-xs text-ink-muted hover:bg-hairline/30"
        >
          <span
            className="w-3.5 h-3.5 rounded-full flex items-center justify-center text-[0.5rem] font-bold text-white shrink-0"
            style={{ background: sourceSystemMeta[src.system].color }}
            aria-hidden
          >
            {sourceSystemMeta[src.system].abbr}
          </span>
          {src.label}
        </button>
      ))}
    </div>
  );
}

export function SourcePanel({ source, onClose }: { source: SourceRef; onClose: () => void }) {
  const meta = sourceSystemMeta[source.system];
  return (
    <aside className="fixed inset-0 z-50 md:static md:z-auto md:w-[340px] md:shrink-0 border-l border-hairline bg-white flex flex-col">
      <div className="flex items-center justify-between border-b border-hairline px-4 py-3">
        <p className="text-sm font-semibold text-ink">Sources</p>
        <button type="button" onClick={onClose} className="text-ink-muted hover:text-ink">
          <IconClose />
        </button>
      </div>
      <div className="p-4 overflow-y-auto">
        <div className="flex items-center gap-2">
          <span
            className="w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold text-white shrink-0"
            style={{ background: meta.color }}
            aria-hidden
          >
            {meta.abbr}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink">{meta.label}</p>
            <p className="truncate text-xs text-ink-muted">{source.label}</p>
          </div>
        </div>
        <p className="mt-3 text-sm text-ink">{source.detail}</p>
      </div>
    </aside>
  );
}

export function IconClose() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
      <path d="m5 5 14 14M19 5 5 19" strokeLinecap="round" />
    </svg>
  );
}

/* ---------- Composer draft rendering (shows the @mention as a chip) ---------- */

export function renderDraftWithMention(text: string) {
  const match = text.match(/^(@\S+\s?)/);
  if (!match) return text;
  const mentionPart = match[1];
  const rest = text.slice(mentionPart.length);
  return (
    <>
      <span className="mr-1 inline-block rounded-md bg-[#0f7a6c]/10 px-1.5 py-0.5 text-[#0f7a6c] font-medium">
        {mentionPart.trim()}
      </span>
      {rest}
    </>
  );
}

/**
 * Minimal markdown renderer for committed assistant messages: headings (#/##/###),
 * horizontal rules (---), bullet lists (- item, with simple nested indentation),
 * and inline **bold** spans. Intentionally not used for the live typewriter preview,
 * since partial markdown mid-stream would look broken \u2014 formatting "snaps in" on commit.
 */
export function renderInlineBold(text: string, keyPrefix: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 3) {
      return (
        <strong key={`${keyPrefix}-b-${idx}`} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <Fragment key={`${keyPrefix}-t-${idx}`}>{part}</Fragment>;
  });
}

export function renderMarkdown(text: string) {
  const lines = text.split("\n");
  const blocks: ReactNode[] = [];
  let listBuffer: string[] = [];
  let tableBuffer: string[] = [];
  let blockIdx = 0;

  const flushList = () => {
    if (!listBuffer.length) return;
    blockIdx += 1;
    blocks.push(
      <ul key={`ul-${blockIdx}`} className="my-2 ml-4 list-disc space-y-1">
        {listBuffer.map((item, i) => (
          <li key={`li-${blockIdx}-${i}`}>{renderInlineBold(item, `li-${blockIdx}-${i}`)}</li>
        ))}
      </ul>
    );
    listBuffer = [];
  };

  const flushTable = () => {
    if (!tableBuffer.length) return;
    blockIdx += 1;
    const tblIdx = blockIdx;
    const rows = tableBuffer
      .map((row) => row.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim()))
      .filter((_, i, arr) => !(i === 1 && arr[1]?.every((cell) => /^:?-+:?$/.test(cell))));
    const [headerRow, ...bodyRows] = rows;
    blocks.push(
      <div key={`tbl-${tblIdx}`} className="my-2 overflow-x-auto">
        <table className="min-w-full border-collapse text-xs">
          <thead>
            <tr>
              {headerRow.map((cell, ci) => (
                <th
                  key={`tbl-${tblIdx}-h-${ci}`}
                  className="border border-hairline bg-surface px-2 py-1 text-left font-semibold"
                >
                  {renderInlineBold(cell, `tbl-${tblIdx}-h-${ci}`)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bodyRows.map((row, ri) => (
              <tr key={`tbl-${tblIdx}-r-${ri}`}>
                {row.map((cell, ci) => (
                  <td key={`tbl-${tblIdx}-r-${ri}-c-${ci}`} className="border border-hairline px-2 py-1">
                    {renderInlineBold(cell, `tbl-${tblIdx}-r-${ri}-c-${ci}`)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableBuffer = [];
  };

  lines.forEach((rawLine) => {
    const line = rawLine.replace(/^\s{0,2}/, "");
    const tableMatch = /^\|.*\|$/.test(line.trim());

    if (tableMatch) {
      flushList();
      tableBuffer.push(line);
      return;
    }
    flushTable();

    const bulletMatch = line.match(/^(?:-|\u2022)\s+(.*)$/);

    if (bulletMatch) {
      listBuffer.push(bulletMatch[1]);
      return;
    }
    flushList();

    if (line.trim() === "---") {
      blockIdx += 1;
      blocks.push(<hr key={`hr-${blockIdx}`} className="my-3 border-hairline" />);
      return;
    }
    if (line.startsWith("### ")) {
      blockIdx += 1;
      blocks.push(
        <div key={`h3-${blockIdx}`} role="heading" aria-level={3} className="mt-3 mb-1 text-sm font-semibold">
          {renderInlineBold(line.slice(4), `h3-${blockIdx}`)}
        </div>
      );
      return;
    }
    if (line.startsWith("## ")) {
      blockIdx += 1;
      blocks.push(
        <div key={`h2-${blockIdx}`} role="heading" aria-level={2} className="mt-3 mb-1 text-base font-semibold">
          {renderInlineBold(line.slice(3), `h2-${blockIdx}`)}
        </div>
      );
      return;
    }
    if (line.startsWith("# ")) {
      blockIdx += 1;
      blocks.push(
        <div key={`h1-${blockIdx}`} role="heading" aria-level={1} className="mt-3 mb-1 text-base font-bold">
          {renderInlineBold(line.slice(2), `h1-${blockIdx}`)}
        </div>
      );
      return;
    }
    if (line.trim() === "") {
      blockIdx += 1;
      blocks.push(<div key={`sp-${blockIdx}`} className="h-2" />);
      return;
    }
    blockIdx += 1;
    blocks.push(
      <p key={`p-${blockIdx}`} className="leading-relaxed">
        {renderInlineBold(line, `p-${blockIdx}`)}
      </p>
    );
  });
  flushList();
  flushTable();

  return <div>{blocks}</div>;
}

export function ScenarioCarousel({
  scenarios,
  selectedId,
  disabled,
  onSelect,
}: {
  scenarios: ScenarioOption[];
  selectedId: string | null;
  disabled: boolean;
  onSelect: (scenario: ScenarioOption) => void;
}) {
  return (
    <div className="mt-3 -mx-1 flex gap-3 overflow-x-auto pb-2 px-1 snap-x snap-mandatory">
      {scenarios.map((scenario) => {
        const isSelected = selectedId === scenario.id;
        const isDimmed = selectedId !== null && !isSelected;
        return (
          <button
            key={scenario.id}
            type="button"
            onClick={() => onSelect(scenario)}
            disabled={disabled || selectedId !== null}
            className={`w-64 shrink-0 snap-start rounded-xl border px-4 py-3 text-left text-xs transition-colors ${
              isSelected
                ? "border-ink bg-ink text-white"
                : isDimmed
                  ? "border-hairline bg-surface text-ink-muted opacity-60"
                  : "border-hairline bg-white text-ink hover:border-ink/40"
            } disabled:cursor-default`}
          >
            <div className="mb-1 flex items-center justify-between gap-2">
              <span className={`text-sm font-semibold ${isSelected ? "text-white" : "text-ink"}`}>
                {scenario.title}
              </span>
              {scenario.badge && (
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[0.625rem] font-semibold ${
                    isSelected ? "bg-white/20 text-white" : "bg-[#0f7a6c]/10 text-[#0f7a6c]"
                  }`}
                >
                  {scenario.badge}
                </span>
              )}
            </div>
            {scenario.supportedBy && (
              <p className={`mb-2 text-[0.625rem] font-medium ${isSelected ? "text-white/80" : "text-[#c23fa0]"}`}>
                {scenario.supportedBy}
              </p>
            )}
            <div className={isSelected ? "text-white/90" : ""}>{renderMarkdown(scenario.body)}</div>
          </button>
        );
      })}
    </div>
  );
}






