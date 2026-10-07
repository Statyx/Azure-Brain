
/* ---------- Demo profile (configurable from the Settings panel) ----------
   The scripted experience is a demo: the person running it and the person being asked to approve
   both change from one session to the next. Instead of hardcoding names, the scripted content uses
   {{tokens}} that are resolved at render time from the profile stored in localStorage. */

export type DemoProfile = {
  /** The person running the demo \u2014 shown in the sidebar and signed at the bottom of the emails. */
  user: { firstName: string; lastName: string; photo: string };
  /** The person contacted for sign-off \u2014 named in the governance and email steps. */
  approver: { firstName: string; lastName: string; title: string };
};

export const DEFAULT_DEMO_PROFILE: DemoProfile = {
  user: { firstName: "Alex", lastName: "Morgan", photo: "" },
  approver: {
    firstName: "Morgan",
    lastName: "Reyes",
    title: "National Commercial Director",
  },
};

export const DEMO_PROFILE_STORAGE_KEY = "caldova-demo-profile";

export const joinName = (firstName: string, lastName: string) => `${firstName} ${lastName}`.trim();

export const nameInitials = (firstName: string, lastName: string) =>
  `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase() || "?";

/** Builds a plausible corporate address (accents stripped) so the email card stays consistent
 *  with whatever names the demo operator configured. */
export const corporateEmail = (firstName: string, lastName: string) => {
  const slug = (value: string) =>
    value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z]/g, "")
      .toLowerCase();
  return `${slug(firstName)}.${slug(lastName)}@caldova.com`;
};

export function loadDemoProfile(): DemoProfile {
  if (typeof window === "undefined") return DEFAULT_DEMO_PROFILE;
  try {
    const raw = window.localStorage.getItem(DEMO_PROFILE_STORAGE_KEY);
    if (!raw) return DEFAULT_DEMO_PROFILE;
    const parsed = JSON.parse(raw) as Partial<DemoProfile>;
    return {
      user: { ...DEFAULT_DEMO_PROFILE.user, ...(parsed.user ?? {}) },
      approver: { ...DEFAULT_DEMO_PROFILE.approver, ...(parsed.approver ?? {}) },
    };
  } catch {
    return DEFAULT_DEMO_PROFILE;
  }
}

/* Tiny external store for the demo profile so it can be read from localStorage without a
   setState-in-effect hydration dance: React uses the default profile for the server snapshot and
   swaps in the stored one right after hydration. */
let profileSnapshot: DemoProfile = DEFAULT_DEMO_PROFILE;
let profileSnapshotLoaded = false;
export const profileListeners = new Set<() => void>();

export function subscribeProfile(listener: () => void) {
  profileListeners.add(listener);
  return () => {
    profileListeners.delete(listener);
  };
}

export function getProfileSnapshot(): DemoProfile {
  if (!profileSnapshotLoaded) {
    profileSnapshot = loadDemoProfile();
    profileSnapshotLoaded = true;
  }
  return profileSnapshot;
}

export function getProfileServerSnapshot(): DemoProfile {
  return DEFAULT_DEMO_PROFILE;
}

/** Persists the profile and notifies subscribers. Returns false when browser storage rejected it
 *  (e.g. quota exceeded by a large uploaded photo) \u2014 the in-memory profile still applies. */
export function storeProfile(next: DemoProfile): boolean {
  profileSnapshot = next;
  profileSnapshotLoaded = true;
  let persisted = true;
  try {
    window.localStorage.setItem(DEMO_PROFILE_STORAGE_KEY, JSON.stringify(next));
  } catch {
    persisted = false;
  }
  profileListeners.forEach((listener) => listener());
  return persisted;
}

/** Token values injected into the scripted content for the current profile. */
export function profileTokens(profile: DemoProfile): Record<string, string> {
  const { user, approver } = profile;
  return {
    userName: joinName(user.firstName, user.lastName),
    userFirstName: user.firstName,
    userInitials: nameInitials(user.firstName, user.lastName),
    approverName: joinName(approver.firstName, approver.lastName),
    approverFirstName: approver.firstName,
    approverTitle: approver.title,
    approverInitials: nameInitials(approver.firstName, approver.lastName),
    approverEmail: corporateEmail(approver.firstName, approver.lastName),
  };
}

export function applyTokens(text: string, tokens: Record<string, string>) {
  return text.replace(/\{\{(\w+)\}\}/g, (match, key: string) => tokens[key] ?? match);
}

/** Recursively resolves {{tokens}} in every string of a scripted data structure (scenes, choices,
 *  email drafts, person cards...) so the whole experience follows the configured profile. */
export function resolveTokens<T>(value: T, tokens: Record<string, string>): T {
  if (typeof value === "string") return applyTokens(value, tokens) as unknown as T;
  if (Array.isArray(value)) return value.map((item) => resolveTokens(item, tokens)) as unknown as T;
  if (value && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value as Record<string, unknown>)) {
      out[key] = resolveTokens(item, tokens);
    }
    return out as unknown as T;
  }
  return value;
}

/* ---------- Minimal inline icon set (no external deps) ---------- */



