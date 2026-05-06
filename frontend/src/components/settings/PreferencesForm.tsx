"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/components/ui/toast";
import { ApiClientError, useApiClient } from "@/lib/api-client";
import { userKeys } from "@/lib/query-keys";

type LearningGoal = "jlpt_prep" | "toeic_prep" | "workplace" | "general";
type EnglishLevel = "beginner" | "intermediate" | "advanced";
type JapaneseLevel = "none" | "n5" | "n4" | "n3" | "n2" | "n1";
type DailyStudyMinutes = 5 | 15 | 30 | 60;
type ITDomain = "web_dev" | "backend" | "networking" | "data" | "general_it";

export type UserPreferences = {
  learning_goal: LearningGoal;
  english_level: EnglishLevel;
  japanese_level: JapaneseLevel;
  daily_study_minutes: DailyStudyMinutes;
  it_domain: ITDomain;
  notification_email: boolean;
  notification_review_reminder: boolean;
};

export const DEFAULT_PREFERENCES: UserPreferences = {
  learning_goal: "general",
  english_level: "beginner",
  japanese_level: "none",
  daily_study_minutes: 15,
  it_domain: "general_it",
  notification_email: true,
  notification_review_reminder: true,
};

const learningGoalOptions: Array<{ value: LearningGoal; label: string }> = [
  { value: "general", label: "General" },
  { value: "workplace", label: "Workplace" },
  { value: "jlpt_prep", label: "JLPT prep" },
  { value: "toeic_prep", label: "TOEIC prep" },
];

const englishLevelOptions: Array<{ value: EnglishLevel; label: string }> = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

const japaneseLevelOptions: Array<{ value: JapaneseLevel; label: string }> = [
  { value: "none", label: "None yet" },
  { value: "n5", label: "N5" },
  { value: "n4", label: "N4" },
  { value: "n3", label: "N3" },
  { value: "n2", label: "N2" },
  { value: "n1", label: "N1" },
];

const dailyStudyOptions: Array<{ value: DailyStudyMinutes; label: string }> = [
  { value: 5, label: "5 minutes" },
  { value: 15, label: "15 minutes" },
  { value: 30, label: "30 minutes" },
  { value: 60, label: "60 minutes" },
];

const itDomainOptions: Array<{ value: ITDomain; label: string }> = [
  { value: "general_it", label: "General IT" },
  { value: "web_dev", label: "Web development" },
  { value: "backend", label: "Backend" },
  { value: "networking", label: "Networking" },
  { value: "data", label: "Data" },
];

function getErrorMessage(error: unknown) {
  if (error instanceof ApiClientError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to update settings";
}

export function PreferencesForm() {
  const apiClient = useApiClient();
  const queryClient = useQueryClient();
  const { success, error: showError } = useToast();
  const [formValues, setFormValues] = useState<UserPreferences | null>(null);

  const preferencesQuery = useQuery({
    queryKey: userKeys.preferences(),
    queryFn: () => apiClient<UserPreferences>("/users/me/preferences"),
  });

  const currentValues = formValues ?? preferencesQuery.data ?? DEFAULT_PREFERENCES;

  const updatePreferencesMutation = useMutation({
    mutationFn: (nextValues: UserPreferences) =>
      apiClient<UserPreferences>("/users/me/preferences", {
        method: "PUT",
        body: JSON.stringify(nextValues),
      }),
    onSuccess: (updatedPreferences) => {
      setFormValues(updatedPreferences);
      success("Settings updated");
      void queryClient.invalidateQueries({ queryKey: userKeys.preferences() });
    },
    onError: (mutationError) => {
      showError(getErrorMessage(mutationError));
    },
  });

  if (preferencesQuery.isError) {
    return (
      <div className="rounded-xl border border-[color:color-mix(in_srgb,var(--error)_35%,var(--border))] bg-[color:color-mix(in_srgb,var(--error)_6%,var(--surface))] p-4 text-sm text-text-primary">
        <p className="font-medium">We could not load your preferences.</p>
        <p className="mt-1 text-text-secondary">{getErrorMessage(preferencesQuery.error)}</p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="mt-3"
          onClick={() => void preferencesQuery.refetch()}
        >
          Try again
        </Button>
      </div>
    );
  }

  const isBusy = preferencesQuery.isPending || updatePreferencesMutation.isPending;

  return (
    <form
      className="space-y-6"
      onSubmit={(event) => {
        event.preventDefault();
        updatePreferencesMutation.mutate(currentValues);
      }}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="learning_goal">Learning goal</Label>
          <Select
            id="learning_goal"
            name="learning_goal"
            value={currentValues.learning_goal}
            disabled={isBusy}
            onChange={(event) => {
              setFormValues((currentValues) => ({
                ...(currentValues ?? preferencesQuery.data ?? DEFAULT_PREFERENCES),
                learning_goal: event.target.value as LearningGoal,
              }));
            }}
          >
            {learningGoalOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="english_level">English level</Label>
          <Select
            id="english_level"
            name="english_level"
            value={currentValues.english_level}
            disabled={isBusy}
            onChange={(event) => {
              setFormValues((currentValues) => ({
                ...(currentValues ?? preferencesQuery.data ?? DEFAULT_PREFERENCES),
                english_level: event.target.value as EnglishLevel,
              }));
            }}
          >
            {englishLevelOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="japanese_level">Japanese level</Label>
          <Select
            id="japanese_level"
            name="japanese_level"
            value={currentValues.japanese_level}
            disabled={isBusy}
            onChange={(event) => {
              setFormValues((currentValues) => ({
                ...(currentValues ?? preferencesQuery.data ?? DEFAULT_PREFERENCES),
                japanese_level: event.target.value as JapaneseLevel,
              }));
            }}
          >
            {japaneseLevelOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="daily_study_minutes">Daily study budget</Label>
          <Select
            id="daily_study_minutes"
            name="daily_study_minutes"
            value={String(currentValues.daily_study_minutes)}
            disabled={isBusy}
            onChange={(event) => {
              setFormValues((currentValues) => ({
                ...(currentValues ?? preferencesQuery.data ?? DEFAULT_PREFERENCES),
                daily_study_minutes: Number(event.target.value) as DailyStudyMinutes,
              }));
            }}
          >
            {dailyStudyOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="it_domain">IT domain</Label>
          <Select
            id="it_domain"
            name="it_domain"
            value={currentValues.it_domain}
            disabled={isBusy}
            onChange={(event) => {
              setFormValues((currentValues) => ({
                ...(currentValues ?? preferencesQuery.data ?? DEFAULT_PREFERENCES),
                it_domain: event.target.value as ITDomain,
              }));
            }}
          >
            {itDomainOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="space-y-4 rounded-xl border border-border bg-secondary/40 p-4">
        <div className="space-y-1">
          <h3 className="text-sm font-medium text-text-primary">Notifications</h3>
          <p className="text-sm text-text-secondary">Choose which reminders Table Project can send you.</p>
        </div>

        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <Label htmlFor="notification_email">Email updates</Label>
            <p className="text-sm text-text-secondary">Get account and learning updates by email.</p>
          </div>
          <Switch
            id="notification_email"
            aria-label="Toggle email updates"
            checked={currentValues.notification_email}
            disabled={isBusy}
            onCheckedChange={(checked) => {
              setFormValues((currentValues) => ({
                ...(currentValues ?? preferencesQuery.data ?? DEFAULT_PREFERENCES),
                notification_email: checked,
              }));
            }}
          />
        </div>

        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <Label htmlFor="notification_review_reminder">Review reminders</Label>
            <p className="text-sm text-text-secondary">Receive a nudge when your daily review queue is waiting.</p>
          </div>
          <Switch
            id="notification_review_reminder"
            aria-label="Toggle review reminders"
            checked={currentValues.notification_review_reminder}
            disabled={isBusy}
            onCheckedChange={(checked) => {
              setFormValues((currentValues) => ({
                ...(currentValues ?? preferencesQuery.data ?? DEFAULT_PREFERENCES),
                notification_review_reminder: checked,
              }));
            }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between gap-4 border-t border-border pt-4">
        <p className="text-sm text-text-secondary">Preference changes apply the next time your study queue is generated.</p>
        <Button type="submit" disabled={isBusy}>
          {updatePreferencesMutation.isPending ? "Saving..." : "Save preferences"}
        </Button>
      </div>
    </form>
  );
}
