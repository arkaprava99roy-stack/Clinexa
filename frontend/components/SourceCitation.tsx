"use client";

import { FileText, ExternalLink } from "lucide-react";

interface Citation {
  report_id?: string;
  report_name: string;
  page: number;
}

interface SourceCitationProps {
  citations: Citation[];
}

export function SourceCitation({ citations }: SourceCitationProps) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {citations.map((c, i) => (
        <div
          key={i}
          title={`${c.report_name} — page ${c.page}`}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium
                     bg-brand-500/10 text-brand-400 border border-brand-500/20
                     hover:bg-brand-500/20 cursor-default transition-colors"
        >
          <FileText className="w-3 h-3" />
          <span className="max-w-[120px] truncate">{c.report_name}</span>
          <span className="text-brand-500">p.{c.page}</span>
        </div>
      ))}
    </div>
  );
}
