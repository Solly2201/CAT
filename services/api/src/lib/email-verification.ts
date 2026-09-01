import crypto from "node:crypto";
import type { DevVerification } from "@cap/contracts";
import { env } from "../config/env.js";

// Issues the email-verification challenge; delivery is lib/mailer.ts. A
// random token is issued at registration, only its SHA-256 hash is
// persisted (models/user.ts), and it expires after 24 hours.
//
// Outside production the raw token is returned in the API response so the
// flow is completable locally, with or without SMTP configured. That is a
// development affordance, not a hole: devVerification() returns undefined
// when NODE_ENV is production, so a deployed instance never leaks a token.

export const VERIFICATION_TOKEN_TTL_MS = 24 * 60 * 60 * 1000;

export const hashVerificationToken = (token: string) =>
  crypto.createHash("sha256").update(token).digest("hex");

export type IssuedVerification = {
  token: string;
  tokenHash: string;
  expiresAt: Date;
};

export const issueVerificationToken = (): IssuedVerification => {
  const token = crypto.randomBytes(32).toString("hex");
  return {
    token,
    tokenHash: hashVerificationToken(token),
    expiresAt: new Date(Date.now() + VERIFICATION_TOKEN_TTL_MS)
  };
};

// Attached to non-production responses only; undefined in production,
// where a real transport must deliver the token instead.
export const devVerification = (issued: IssuedVerification): DevVerification | undefined =>
  env.NODE_ENV === "production"
    ? undefined
    : { token: issued.token, expiresAt: issued.expiresAt.toISOString(), deliveredVia: "api-response" };
