import type { NextFunction, Request, Response } from "express";
import type { UserRole } from "@cap/contracts";
import { verifyAccessToken } from "../lib/jwt.js";
import { User } from "../models/user.js";

declare global {
  namespace Express {
    interface Request {
      auth?: { userId: string; role: UserRole; tokenVersion: number };
    }
  }
}

const bearer = (request: Request): string | undefined =>
  request.header("authorization")?.replace(/^Bearer\s+/i, "");

export const requireAuth = (request: Request, response: Response, next: NextFunction) => {
  const token = bearer(request);
  if (!token) return response.status(401).json({ message: "Authentication is required." });

  try {
    const payload = verifyAccessToken(token);
    request.auth = { userId: payload.sub, role: payload.role, tokenVersion: payload.ver ?? 0 };
    return next();
  } catch {
    return response.status(401).json({ message: "Your session is invalid or has expired." });
  }
};

// Role as claimed by the token. Cheap and stateless, so it stays the
// guard for routes where a stale claim is harmless -- roles only ever
// gain reach here, so a stale CITIZEN claim grants nothing extra.
export const requireRole = (...roles: UserRole[]) =>
  (request: Request, response: Response, next: NextFunction) => {
    if (!request.auth) return response.status(401).json({ message: "Authentication is required." });
    if (!roles.includes(request.auth.role)) {
      return response.status(403).json({ message: "You do not have access to this resource." });
    }
    return next();
  };

/**
 * Re-reads the caller's role and token version from the database.
 *
 * A signed JWT carries the role, so without this the API would honour a
 * role for the token's remaining lifetime even after the account was
 * demoted -- the window in which a removed authority can still moderate.
 * Privileged routes therefore pay one indexed read to confirm the claim
 * against stored state, and `request.auth.role` is replaced with the
 * stored value so everything downstream authorises on fact, not claim.
 *
 * `tokenVersion` is the revocation lever: incrementing a user's
 * `tokenVersion` invalidates every token already issued to them without
 * waiting for expiry. Ordinary citizen requests keep the stateless path.
 */
const freshRole = (roles?: UserRole[]) =>
  async (request: Request, response: Response, next: NextFunction) => {
    if (!request.auth) return response.status(401).json({ message: "Authentication is required." });

    try {
      const user = await User.findById(request.auth.userId).select("role tokenVersion");
      if (!user || (user.tokenVersion ?? 0) !== request.auth.tokenVersion) {
        return response.status(401).json({ message: "Your session is invalid or has expired." });
      }

      request.auth.role = user.role;
      if (roles && !roles.includes(user.role)) {
        return response.status(403).json({ message: "You do not have access to this resource." });
      }
      return next();
    } catch (error) {
      return next(error);
    }
  };

export const withFreshRole = freshRole();

export const requireFreshRole = (...roles: UserRole[]) => freshRole(roles);

/**
 * Populates `request.auth` when a valid token is present and continues
 * either way, for endpoints that are public but render differently when
 * signed in (the petition list and detail).
 *
 * An invalid token is treated as anonymous, so a stale session degrades a
 * public page rather than breaking it. This grants no access on its own:
 * every privileged branch behind it re-checks the identity it finds.
 */
export const optionalAuth = (request: Request, _response: Response, next: NextFunction) => {
  const token = bearer(request);
  if (!token) return next();

  try {
    const payload = verifyAccessToken(token);
    request.auth = { userId: payload.sub, role: payload.role, tokenVersion: payload.ver ?? 0 };
  } catch {
    // Deliberately silent: an unusable token means anonymous here.
  }
  return next();
};
