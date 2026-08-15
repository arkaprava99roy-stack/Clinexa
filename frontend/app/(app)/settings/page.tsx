"use client";

import { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { createClient } from "@/lib/supabase";
import { Save, Trash2, AlertCircle } from "lucide-react";
import type { Metadata } from "next";

export default function SettingsPage() {
  const { user, signOut } = useAuth();
  const supabase = createClient();

  const [fullName, setFullName] = useState(user?.user_metadata?.full_name ?? "");
  const [language, setLanguage] = useState("en");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    const { error } = await supabase.auth.updateUser({ data: { full_name: fullName } });
    setSaving(false);
    setMessage(error
      ? { type: "error", text: error.message }
      : { type: "success", text: "Profile updated successfully." }
    );
  }

  async function handleDeleteAccount() {
    setDeleting(true);
    // Phase 1: sign out only. Actual deletion via admin API in Phase 9.
    await signOut();
  }

  return (
    <div className="px-8 py-8 max-w-2xl mx-auto animate-fade-in">
      <div className="mb-8">
        <h1 className="section-title">Settings</h1>
        <p className="section-subtitle">Manage your profile and account preferences.</p>
      </div>

      {/* Profile */}
      <div className="glass-card p-6 mb-6">
        <h2 className="font-semibold text-slate-200 mb-5">Profile</h2>
        <form onSubmit={handleSave} className="space-y-5">
          <div>
            <label htmlFor="settings-name" className="label">Full Name</label>
            <input
              id="settings-name"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="input-field"
            />
          </div>
          <div>
            <label htmlFor="settings-email" className="label">Email</label>
            <input
              id="settings-email"
              type="email"
              value={user?.email ?? ""}
              disabled
              className="input-field opacity-50 cursor-not-allowed"
            />
          </div>
          <div>
            <label htmlFor="settings-language" className="label">Preferred Language</label>
            <select
              id="settings-language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="input-field"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
              <option value="hi">Hindi</option>
            </select>
          </div>

          {message && (
            <div className={`flex items-center gap-2 text-sm px-4 py-3 rounded-xl ${
              message.type === "success"
                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                : "bg-red-500/10 text-red-400 border border-red-500/20"
            }`}>
              {message.type === "error" && <AlertCircle className="w-4 h-4" />}
              {message.text}
            </div>
          )}

          <button id="settings-save" type="submit" disabled={saving} className="btn-primary">
            <Save className="w-4 h-4" />
            {saving ? "Saving…" : "Save Changes"}
          </button>
        </form>
      </div>

      {/* Danger Zone */}
      <div className="glass-card p-6 border-red-500/20">
        <h2 className="font-semibold text-red-400 mb-2">Danger Zone</h2>
        <p className="text-slate-400 text-sm mb-5">
          Deleting your account permanently removes all reports, analyses, and chat history.
          This action cannot be undone.
        </p>
        {!confirmDelete ? (
          <button
            id="settings-delete-start"
            onClick={() => setConfirmDelete(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                       text-red-400 border border-red-500/20 bg-red-500/5 hover:bg-red-500/15 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete My Account
          </button>
        ) : (
          <div className="flex items-center gap-3">
            <button
              id="settings-delete-confirm"
              onClick={handleDeleteAccount}
              disabled={deleting}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium
                         text-white bg-red-600 hover:bg-red-500 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              {deleting ? "Deleting…" : "Yes, Delete Everything"}
            </button>
            <button
              id="settings-delete-cancel"
              onClick={() => setConfirmDelete(false)}
              className="btn-secondary text-sm px-4 py-2.5"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
