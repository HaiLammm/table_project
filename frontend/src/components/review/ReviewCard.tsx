"use client";

import type { SessionCard } from "@/types/srs";
import type { VocabularyDefinition } from "@/types/vocabulary";

type ReviewCardProps = {
  card: SessionCard;
  currentIndex: number;
  totalCards: number;
  isRevealed: boolean;
  showJpDefinition: boolean;
};

function getJapaneseDefinition(definitions: VocabularyDefinition[]): VocabularyDefinition | undefined {
  return definitions.find((d) => d.language === "ja" || d.language === "jp");
}

function getEnglishDefinition(definitions: VocabularyDefinition[]): VocabularyDefinition | undefined {
  return definitions.find((d) => d.language === "en");
}

function buildMetadataLine(card: SessionCard): string {
  const parts: string[] = [];
  if (card.term?.part_of_speech) parts.push(card.term.part_of_speech);
  if (card.term?.cefr_level) parts.push(card.term.cefr_level);
  if (card.term?.jlpt_level) parts.push(`N${card.term.jlpt_level}`);
  return parts.join(" · ");
}

export function ReviewCard({
  card,
  currentIndex,
  totalCards,
  isRevealed,
  showJpDefinition,
}: ReviewCardProps) {
  const termText = card.term?.term ?? "Loading...";
  const metadataLine = buildMetadataLine(card);
  const jpDef = card.term ? getJapaneseDefinition(card.term.definitions) : undefined;
  const enDef = card.term ? getEnglishDefinition(card.term.definitions) : undefined;
  const jpReading = jpDef?.definition;
  const definitionText = enDef?.definition;
  const ipa = enDef?.ipa;
  const examples = enDef?.examples ?? [];
  const sessionLabel = `${currentIndex + 1}/${totalCards}`;

  return (
    <article
      role="article"
      aria-label={`Vocabulary card: ${termText}`}
      tabIndex={0}
      className="relative w-full max-w-2xl bg-zinc-100 border border-zinc-200 rounded-[14px] p-6 sm:p-8 lg:p-10 text-center transition-all duration-150 outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2"
    >
      <div className="absolute top-4 right-5">
        <span className="text-xs font-medium text-text-muted">{sessionLabel}</span>
      </div>

      <div className="mt-3">
        <p className="text-[1.5rem] sm:text-[1.625rem] lg:text-[1.75rem] font-semibold text-text-primary leading-snug">
          {termText}
        </p>

        {jpReading && (
          <p className="mt-1 text-base sm:text-lg text-text-secondary">{jpReading}</p>
        )}

        {metadataLine && (
          <p className="mt-2 text-xs text-text-muted">{metadataLine}</p>
        )}
      </div>

      {isRevealed && (
        <div className="mt-6 border-t border-zinc-300 pt-6 text-left">
          {enDef && (
            <>
              {definitionText && (
                <p className="text-base text-text-secondary leading-relaxed">
                  {definitionText}
                </p>
              )}

              {ipa && (
                <p className="mt-2 font-mono text-sm text-text-muted">/{ipa}/</p>
              )}

              {card.term?.cefr_level && (
                <span className="mt-2 inline-block rounded-full border border-zinc-300 px-2 py-0.5 text-xs font-medium text-text-muted">
                  {card.term.cefr_level}
                </span>
              )}

              {examples.length > 0 && (
                <div className="mt-4 space-y-2">
                  {examples.map((example, idx) => (
                    <p
                      key={idx}
                      className="bg-zinc-50 border-l-2 border-zinc-300 pl-3 py-2 text-sm text-text-secondary"
                    >
                      {example}
                    </p>
                  ))}
                </div>
              )}

              {jpDef && showJpDefinition && (
                <div className="mt-4 rounded-lg bg-zinc-50 border border-zinc-200 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-text-muted mb-1">
                    Japanese definition
                  </p>
                  <p className="text-sm text-text-secondary leading-relaxed text-jp">
                    {jpDef.definition}
                  </p>
                </div>
              )}
            </>
          )}

          {!enDef && (
            <p className="text-sm text-text-muted italic">
              No definition available for this term.
            </p>
          )}

          <div
            role="group"
            aria-label="Rate your recall"
            className="mt-6 min-h-[2.75rem] rounded-lg border border-dashed border-zinc-300 bg-zinc-50/50 flex items-center justify-center"
          >
            <span className="text-xs text-text-muted">Rating buttons will appear here</span>
          </div>
        </div>
      )}

      {!isRevealed && (
        <div className="mt-6 border-t border-zinc-300 pt-5">
          <kbd className="inline-flex items-center gap-1 rounded bg-zinc-800 border border-zinc-700 px-1.5 py-0.5 text-xs text-zinc-200">
            Press{" "}
            <span className="rounded bg-zinc-700 px-1 py-px text-[10px] font-semibold text-zinc-100">
              Space
            </span>{" "}
            to reveal answer
          </kbd>
        </div>
      )}
    </article>
  );
}
