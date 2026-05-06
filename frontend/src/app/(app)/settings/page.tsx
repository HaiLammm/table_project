"use client";

import { UserProfile } from "@clerk/nextjs";

import { PreferencesForm } from "@/components/settings";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <section className="flex flex-col gap-6">
      <div className="space-y-2">
        <h1 className="text-display text-text-primary">Settings</h1>
        <p className="text-body text-text-secondary">
          Manage your Clerk account details and the learning preferences that shape your daily study plan.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>
            Update your name, email, avatar, password, and connected account details in Clerk.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UserProfile
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "w-full rounded-xl border border-border shadow-none",
              },
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Learning preferences</CardTitle>
          <CardDescription>
            Keep your goals, language levels, study budget, and reminders aligned with how you want to learn.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PreferencesForm />
        </CardContent>
      </Card>
    </section>
  );
}
