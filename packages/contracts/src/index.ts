import { z } from "zod";

export * from "./civic.js";
export * from "./petitions.js";

export const userRoles = ["CITIZEN", "AUTHORITY", "ADMIN"] as const;
export type UserRole = (typeof userRoles)[number];

export const disclaimerVersion = "2026-08-16";

export const disclaimerText =
  "This module is only for public awareness and information. For any real-world implication, please contact a legal adviser.";

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128)
});

export const registerSchema = z.object({
  fullName: z.string().trim().min(2).max(100),
  email: z.string().email(),
  password: z.string().min(12).max(128),
  profilePhotoUrl: z.string().url().optional(),
  acceptedDisclaimer: z.literal(true)
});

export const verifyEmailSchema = z.object({
  token: z.string().trim().min(16).max(128)
});

export const resendVerificationSchema = z.object({
  email: z.string().email()
});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
export type VerifyEmailInput = z.infer<typeof verifyEmailSchema>;
export type ResendVerificationInput = z.infer<typeof resendVerificationSchema>;

export type PublicUser = {
  id: string;
  fullName: string;
  email: string;
  profilePhotoUrl?: string;
  role: UserRole;
  emailVerified: boolean;
};

export type LoginResponse = {
  token: string;
  /** Long-lived token accepted only by POST /auth/refresh. */
  refreshToken: string;
  user: PublicUser;
};

export const refreshSchema = z.object({
  refreshToken: z.string().min(1)
});
export type RefreshInput = z.infer<typeof refreshSchema>;

export type RefreshResponse = {
  token: string;
  refreshToken: string;
  user: PublicUser;
};

/**
 * Development-only verification handoff. Outside production the API
 * returns the token in the response, whether or not SMTP is configured,
 * so the flow is completable locally; in production this field is never
 * populated and delivery is by email only.
 */
export type DevVerification = {
  token: string;
  expiresAt: string;
  deliveredVia: "api-response";
};

export type RegisterResponse = {
  user: PublicUser;
  message: string;
  verification?: DevVerification;
};

export type VerifyEmailResponse = {
  user: PublicUser;
  message: string;
};

/** Mirrors the AI service's `LegalExcerpt` (services/ai/app/main.py). */
export type LegalExcerpt = {
  chunk_id: string;
  text: string;
  source: string;
  act_no: string;
  unit: string;
  official_url: string;
  verified_as_on: string;
  coverage_note: string;
};

export type LegalPolicyDecision =
  | "answered"
  | "abstained"
  | "redirect_emergency"
  | "redirect_adviser"
  | "refused";

/**
 * Safety severity assigned before retrieval by the AI service's
 * deterministic query-safety policy (services/ai/app/safety/risk.py).
 *
 * - `normal` — ordinary legal education; retrieval and the confidence gate decide the rest.
 * - `serious` — a real legal matter affecting the asker; the caution leads, cited law may follow.
 * - `emergency` — an immediate safety situation; official contact only, no legal analysis.
 * - `harmful_request` — a request for obstruction or fabrication; refused.
 */
export const legalSeverities = ["normal", "serious", "emergency", "harmful_request"] as const;
export type LegalSeverity = (typeof legalSeverities)[number];

/** Mirrors the AI service's `LegalAnswerResponse` (services/ai/app/main.py). */
export type LegalAnswerResponse = {
  excerpts: LegalExcerpt[];
  message: string | null;
  abstained: boolean;
  policy_decision: LegalPolicyDecision;
  reason: string | null;
  sources: string[];
  disclaimer_version: string;
  disclaimer_text: string;
  severity: LegalSeverity;
  /** The response points at an authority, helpline or legal-aid service. */
  authority_guidance: boolean;
  /** True when the previous question was deterministically folded into
   *  retrieval (multi-turn context). Optional: absent from responses
   *  recorded before the context layer existed. */
  context_applied?: boolean;
  /** The exact combined text retrieval used when context was applied —
   *  shown to the user so nothing is interpreted invisibly. */
  resolved_question?: string | null;
};

/** The previous exchange, sent back with a follow-up question. */
export type LegalQueryContext = {
  previous_question: string;
};
