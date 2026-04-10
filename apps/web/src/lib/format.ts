function titleize(value: string) {
  return value
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatDateTime(value: string, timezone?: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: timezone,
  }).format(new Date(value));
}

export function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
  }).format(new Date(value));
}

export function formatRole(role: string | null | undefined) {
  if (!role) {
    return "No role";
  }

  return titleize(role.replaceAll("_", " "));
}

export function formatVoicePart(value: string | null | undefined) {
  if (!value) {
    return "Unassigned";
  }

  return titleize(value.replaceAll("_", " "));
}

export function formatEventType(value: string) {
  return titleize(value.replaceAll("_", " "));
}

export function formatAudienceLabel(audienceType: string | null) {
  if (!audienceType) {
    return "No audience";
  }

  return titleize(audienceType.replaceAll("_", " "));
}
