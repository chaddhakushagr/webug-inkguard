"use client";

import React, { useState } from "react";
import {
  Button,
  Input,
  Textarea,
  Select,
  Badge,
  Card,
  CardHeader,
  CardContent,
  CardFooter,
  Tabs,
  Dialog,
  Toast,
  Tooltip,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableHeaderCell,
  TableCell,
  EmptyState,
  ErrorState,
  Skeleton,
  Banner,
  StatusStepper,
  DiffView,
  HighlightedText,
  PageHeader,
  AIBadge,
  ModeChip,
  AppShell,
} from "@/shared/ui";
import { Finding } from "@/shared/api/types";
import { Sparkles, ArrowRight, Save, Send, AlertTriangle, Shield } from "lucide-react";

export default function DevUiGalleryPage() {
  const [activeTab, setActiveTab] = useState("components");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>("f-1");
  const [toasts, setToasts] = useState([
    { id: "t-1", type: "success" as const, title: "Fix Applied", message: "Replacement 'Lumo Glow Concentrate' applied to version 2." },
  ]);

  const sampleFindings: Finding[] = [
    {
      id: "f-1",
      review_id: "rev-1",
      submission_version_id: "v-1",
      fingerprint: "fp-1",
      source: "rule",
      issue_type: "terminology",
      severity: "high",
      confidence: 1.0,
      span_start: 35,
      span_end: 40,
      excerpt: "serum",
      cited_entry_code: "TERM-001",
      is_policy: true,
      needs_human_judgment: false,
      explanation: "Product must be called 'Lumo Glow Concentrate', never 'serum'.",
      suggested_fix: "Lumo Glow Concentrate",
      status: "open",
      is_synthetic: true,
      created_at: new Date().toISOString(),
    },
    {
      id: "f-2",
      review_id: "rev-1",
      submission_version_id: "v-1",
      fingerprint: "fp-2",
      source: "ai",
      issue_type: "claim",
      severity: "high",
      confidence: 0.94,
      span_start: 62,
      span_end: 86,
      excerpt: "completely cure dry skin",
      cited_entry_code: "FACT-001",
      claim_verdict: "Contradicted",
      is_policy: true,
      needs_human_judgment: false,
      explanation: "Clinical Study L-12 supports 'visible skin hydration improvement', but refutes total cure claims.",
      suggested_fix: "visibly hydrate dry skin",
      status: "open",
      is_synthetic: true,
      created_at: new Date().toISOString(),
    },
  ];

  const sampleText =
    "Experience the miracle power of our serum! It is clinically proven to completely cure dry skin in just 2 days.";

  return (
    <AppShell pageTitle="UI Design System Gallery (Dev Review)">
      <div className="space-y-12">
        <PageHeader
          title="Proofreader's Desk Design System"
          description="Design review harness showing all tokens, accessible components, and finding markup styles."
          breadcrumbs={[
            { label: "Dashboard", href: "/dashboard/" },
            { label: "Design System (/dev/ui)" },
          ]}
          actions={
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsDialogOpen(true)}
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Open Test Dialog
            </Button>
          }
        />

        {/* 1. Palette & Contrast Swatches */}
        <section aria-labelledby="palette-section" className="bg-white p-6 rounded-xl border border-[#E2E5EA]">
          <h2 id="palette-section" className="text-base font-bold text-[#1F2A44] mb-1">
            Palette &amp; WCAG 2.1 AA Contrast Ratios (Target &ge; 4.5:1)
          </h2>
          <p className="text-xs text-[#5B6475] mb-4">
            All text and background pairs verified via automated relative luminance formula.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 text-xs">
            <div className="p-3 rounded-lg border border-[#CBD2DC] bg-[#1F2A44] text-white">
              <span className="font-bold block">Ink Navy</span>
              <span className="font-mono text-[10px] opacity-80">#1F2A44</span>
              <span className="block mt-2 font-mono text-[10px] text-emerald-300">14.2:1 (AAA)</span>
            </div>
            <div className="p-3 rounded-lg border border-[#CBD2DC] bg-[#0F766E] text-white">
              <span className="font-bold block">Teal Accent</span>
              <span className="font-mono text-[10px] opacity-80">#0F766E</span>
              <span className="block mt-2 font-mono text-[10px] text-emerald-300">5.5:1 (AA)</span>
            </div>
            <div className="p-3 rounded-lg border border-[#CBD2DC] bg-[#F7F7F4] text-[#1F2A44]">
              <span className="font-bold block">Paper BG</span>
              <span className="font-mono text-[10px] text-[#5B6475]">#F7F7F4</span>
              <span className="block mt-2 font-mono text-[10px] text-[#5B6475]">Canvas Base</span>
            </div>
            <div className="p-3 rounded-lg border border-[#CBD2DC] bg-[#FEF3F2] text-[#B42318]">
              <span className="font-bold block">High Severity</span>
              <span className="font-mono text-[10px] opacity-80">#B42318</span>
              <span className="block mt-2 font-mono text-[10px] text-[#B42318]">6.6:1 (AA)</span>
            </div>
            <div className="p-3 rounded-lg border border-[#CBD2DC] bg-[#FFFBEB] text-[#B45309]">
              <span className="font-bold block">Medium Severity</span>
              <span className="font-mono text-[10px] opacity-80">#B45309</span>
              <span className="block mt-2 font-mono text-[10px] text-[#B45309]">5.0:1 (AA)</span>
            </div>
            <div className="p-3 rounded-lg border border-[#CBD2DC] bg-[#EFF8FF] text-[#175CD3]">
              <span className="font-bold block">Low Severity</span>
              <span className="font-mono text-[10px] opacity-80">#175CD3</span>
              <span className="block mt-2 font-mono text-[10px] text-[#175CD3]">6.0:1 (AA)</span>
            </div>
            <div className="p-3 rounded-lg border border-[#CBD2DC] bg-[#ECFDF3] text-[#067647]">
              <span className="font-bold block">Success</span>
              <span className="font-mono text-[10px] opacity-80">#067647</span>
              <span className="block mt-2 font-mono text-[10px] text-[#067647]">5.7:1 (AA)</span>
            </div>
          </div>
        </section>

        {/* 2. Proofreader Text Markup (Rule vs AI) */}
        <section aria-labelledby="markup-section" className="bg-white p-6 rounded-xl border border-[#E2E5EA]">
          <h2 id="markup-section" className="text-base font-bold text-[#1F2A44] mb-1">
            Proofreader Text Markup (Rule vs. AI Distinction)
          </h2>
          <p className="text-xs text-[#5B6475] mb-4">
            Rule findings feature solid underline and solid card border. AI findings feature wavy dotted underline, dashed card border, and AI badge.
          </p>

          <HighlightedText
            content={sampleText}
            findings={sampleFindings}
            selectedFindingId={selectedFindingId}
            onSelectFinding={(id) => setSelectedFindingId(id)}
          />

          <div className="mt-4 flex items-center gap-4 text-xs text-[#5B6475]">
            <span className="flex items-center gap-1.5 font-medium">
              <span className="w-4 h-0.5 bg-[#B42318] inline-block" /> Solid = Rule Finding
            </span>
            <span className="flex items-center gap-1.5 font-medium">
              <span className="w-4 h-0.5 border-b-2 border-dotted border-[#B42318] inline-block" /> Wavy = AI Finding
            </span>
          </div>
        </section>

        {/* 3. Workflow Stepper */}
        <section aria-labelledby="stepper-section" className="bg-white p-6 rounded-xl border border-[#E2E5EA]">
          <h2 id="stepper-section" className="text-base font-bold text-[#1F2A44] mb-3">
            Workflow Status Stepper
          </h2>
          <div className="space-y-4">
            <div>
              <span className="text-xs font-semibold text-[#5B6475] block mb-1">Linear Progress: In Review</span>
              <StatusStepper currentStatus="In Review" />
            </div>
            <div>
              <span className="text-xs font-semibold text-[#5B6475] block mb-1">Workflow Branch: Changes Requested</span>
              <StatusStepper currentStatus="Changes Requested" />
            </div>
          </div>
        </section>

        {/* 4. Diff View Component */}
        <section aria-labelledby="diff-section" className="bg-white p-6 rounded-xl border border-[#E2E5EA]">
          <h2 id="diff-section" className="text-base font-bold text-[#1F2A44] mb-3">
            Content Revision Diff Viewer
          </h2>
          <DiffView
            diffText={`--- v1 (Draft)
+++ v2 (Accepted Fix)
- Experience the miracle power of our serum!
+ Experience the proven hydration benefits of our Lumo Glow Concentrate!
  It is clinically proven to support healthy skin.`}
          />
        </section>

        {/* 5. Buttons & Controls */}
        <section aria-labelledby="buttons-section" className="bg-white p-6 rounded-xl border border-[#E2E5EA]">
          <h2 id="buttons-section" className="text-base font-bold text-[#1F2A44] mb-3">
            Buttons &amp; Variants
          </h2>
          <div className="flex flex-wrap items-center gap-3">
            <Button variant="primary" size="sm">Primary Sm</Button>
            <Button variant="primary" size="md" leftIcon={<Save className="w-4 h-4" />}>
              Primary Md
            </Button>
            <Button variant="primary" size="lg">Primary Lg</Button>
            <Button variant="secondary" size="md">Secondary</Button>
            <Button variant="ghost" size="md">Ghost Button</Button>
            <Button variant="danger" size="md">Danger Action</Button>
            <Button variant="primary" size="md" isLoading>Loading State</Button>
            <Button variant="secondary" size="md" disabled>Disabled</Button>
          </div>
        </section>

        {/* 6. Form Controls */}
        <section aria-labelledby="forms-section" className="bg-white p-6 rounded-xl border border-[#E2E5EA]">
          <h2 id="forms-section" className="text-base font-bold text-[#1F2A44] mb-3">
            Accessible Form Controls
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input label="Submission Title" placeholder="e.g. Spring Launch Teaser" hint="Internal working title" required />
            <Input label="Channel Name" value="social" error="Channel 'press_release' requires high-tier approval" />
            <Select
              label="Classification Tier"
              options={[
                { value: "public", label: "Public (Agency Safe)" },
                { value: "internal", label: "Internal (Default)" },
                { value: "confidential", label: "Confidential (Strict)" },
              ]}
            />
          </div>
          <div className="mt-4">
            <Textarea label="Marketing Copy" rows={3} placeholder="Paste draft text here..." />
          </div>
        </section>

        {/* 7. Badges & Honesty Chips */}
        <section aria-labelledby="badges-section" className="bg-white p-6 rounded-xl border border-[#E2E5EA]">
          <h2 id="badges-section" className="text-base font-bold text-[#1F2A44] mb-3">
            Badges, Honesty Cues &amp; Mode Chips (Never Color Alone)
          </h2>
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-[#5B6475] mr-2">Severity:</span>
              <Badge badge={{ kind: "severity", value: "high" }} />
              <Badge badge={{ kind: "severity", value: "medium" }} />
              <Badge badge={{ kind: "severity", value: "low" }} />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-[#5B6475] mr-2">Verdicts:</span>
              <Badge badge={{ kind: "verdict", value: "Supported" }} />
              <Badge badge={{ kind: "verdict", value: "Contradicted" }} />
              <Badge badge={{ kind: "verdict", value: "Unverified" }} />
              <Badge badge={{ kind: "verdict", value: "Expired" }} />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-[#5B6475] mr-2">Source:</span>
              <Badge badge={{ kind: "source", value: "rule" }} />
              <Badge badge={{ kind: "source", value: "ai" }} />
              <AIBadge confidence={0.92} />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-[#5B6475] mr-2">AI Modes:</span>
              <ModeChip mode="mock" />
              <ModeChip mode="cached" />
              <ModeChip mode="live" />
              <ModeChip mode="rules_only" />
            </div>
          </div>
        </section>

        {/* 8. Banners, Toasts & Feedback States */}
        <section aria-labelledby="feedback-section" className="bg-white p-6 rounded-xl border border-[#E2E5EA] space-y-4">
          <h2 id="feedback-section" className="text-base font-bold text-[#1F2A44] mb-3">
            Banners &amp; Feedback States
          </h2>
          <Banner type="demo" title="Synthetic Boundary Safe">
            No proprietary or confidential data leaves the machine. All items relate to fictional brand &quot;Lumo&quot;.
          </Banner>
          <Banner type="error" title="Review Blocked">
            High-severity findings must be resolved or dismissed before submission can proceed.
          </Banner>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <EmptyState
              title="No Open Submissions"
              description="Your queue is clear. Create a new submission or load a demo sample to run brand governance."
              action={<Button variant="primary" size="sm">+ New Submission</Button>}
            />
            <ErrorState
              title="LLM Service Timeout"
              message="The upstream model exceeded the 15-second response limit. Fallback to rule engine succeeded."
              onRetry={() => {}}
            />
          </div>
        </section>

        {/* Interactive Dialog Demo */}
        <Dialog
          isOpen={isDialogOpen}
          onClose={() => setIsDialogOpen(false)}
          title="Dismiss Finding with Rationale"
          description="A documented rationale is strictly required to dismiss brand policy findings."
          footer={
            <>
              <Button variant="secondary" size="sm" onClick={() => setIsDialogOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={() => setIsDialogOpen(false)}>
                Confirm Dismissal
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <Select
              label="Dismissal Category"
              options={[
                { value: "factual_override", label: "Factual override with updated clinical report" },
                { value: "contextual_exception", label: "Contextual exception approved by brand director" },
                { value: "editorial_intent", label: "Creative editorial intent" },
              ]}
            />
            <Textarea label="Explanation & Evidence Note" rows={3} placeholder="Describe the reason for this exception..." />
          </div>
        </Dialog>
      </div>
    </AppShell>
  );
}
