"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useVocabularyRequest } from "@/hooks/useVocabularyRequest";
import type { VocabularyRequestPreviewResponse } from "@/types/vocabulary";

const CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"];
const JLPT_LEVELS = ["N5", "N4", "N3", "N2", "N1"];

interface VocabularyRequestFormProps {
  onPreview: (data: VocabularyRequestPreviewResponse) => void;
}

export function VocabularyRequestForm({ onPreview }: VocabularyRequestFormProps) {
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState<"en" | "jp">("en");
  const [level, setLevel] = useState("");
  const [count, setCount] = useState(10);
  const [errors, setErrors] = useState<{ topic?: string; level?: string; count?: string }>({});

  const previewMutation = useVocabularyRequest();

  const validate = () => {
    const newErrors: typeof errors = {};
    if (!topic.trim()) {
      newErrors.topic = "Topic is required";
    }
    if (!level) {
      newErrors.level = "Level is required";
    }
    if (count < 1 || count > 50) {
      newErrors.count = "Count must be between 1 and 50";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    previewMutation.mutate(
      { topic: topic.trim(), language, level, count },
      {
        onSuccess: (data) => {
          onPreview(data);
        },
        onError: () => {
          // Handle error
        },
      }
    );
  };

  const levels = language === "jp" ? JLPT_LEVELS : CEFR_LEVELS;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="topic-input" className="text-sm font-medium text-zinc-700 mb-1.5">
          Topic
        </label>
        <input
          id="topic-input"
          type="text"
          value={topic}
          onChange={(e) => {
            setTopic(e.target.value);
            if (errors.topic) setErrors((prev) => ({ ...prev, topic: undefined }));
          }}
          onBlur={validate}
          placeholder="e.g., networking, cooking, travel"
          className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10"
        />
        {errors.topic && <p className="text-red-500 text-sm mt-1">{errors.topic}</p>}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="language-select" className="text-sm font-medium text-zinc-700 mb-1.5">
          Language
        </label>
        <select
          id="language-select"
          value={language}
          onChange={(e) => {
            setLanguage(e.target.value as "en" | "jp");
            setLevel("");
          }}
          className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10"
        >
          <option value="en">English</option>
          <option value="jp">Japanese</option>
        </select>
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="level-select" className="text-sm font-medium text-zinc-700 mb-1.5">
          Level
        </label>
        <select
          id="level-select"
          value={level}
          onChange={(e) => {
            setLevel(e.target.value);
            if (errors.level) setErrors((prev) => ({ ...prev, level: undefined }));
          }}
          onBlur={validate}
          className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10"
        >
          <option value="">Select level</option>
          {levels.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
        {errors.level && <p className="text-red-500 text-sm mt-1">{errors.level}</p>}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor="count-input" className="text-sm font-medium text-zinc-700 mb-1.5">
          Number of Terms
        </label>
        <input
          id="count-input"
          type="number"
          min={1}
          max={50}
          value={count}
          onChange={(e) => {
            setCount(Number(e.target.value));
            if (errors.count) setErrors((prev) => ({ ...prev, count: undefined }));
          }}
          onBlur={validate}
          className="bg-white border border-zinc-200 rounded-[10px] px-4 py-2.5 text-sm outline-none transition focus:border-zinc-900 focus:ring-2 focus:ring-zinc-900/10"
        />
        {errors.count && <p className="text-red-500 text-sm mt-1">{errors.count}</p>}
      </div>

      <Button
        type="submit"
        disabled={previewMutation.isPending}
        className="bg-zinc-900 text-zinc-50 hover:bg-zinc-800 self-start"
      >
        {previewMutation.isPending ? "Generating..." : "Generate Preview"}
      </Button>
    </form>
  );
}