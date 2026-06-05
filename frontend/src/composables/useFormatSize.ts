const UNITS = ["B", "KB", "MB", "GB", "TB"];

export function useFormatSize(bytes: number): string {
  if (!bytes || bytes <= 0) return "0 B";
  const i = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    UNITS.length - 1,
  );
  const val = bytes / 1024 ** i;
  return `${val.toFixed(i === 0 ? 0 : 1)} ${UNITS[i]}`;
}
