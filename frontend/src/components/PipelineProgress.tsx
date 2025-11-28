import React from "react";

export type StepState = "pending" | "running" | "done" | "error";
export type Step = { label: string; state: StepState; detail?: string };

export function PipelineProgress({ steps }: { steps: Step[] }) {
  return (
    <div className="pipeline">
      {steps.map((s, i) => (
        <div key={i} className={`pstep ${s.state}`}>
          <span className={`pdot ${s.state}`} aria-hidden />
          <span className="plabel">{s.label}</span>
        </div>
      ))}
    </div>
  );
}
