const DIVISIONS = [
  { amount: 60, unit: "秒" },
  { amount: 60, unit: "分钟" },
  { amount: 24, unit: "小时" },
  { amount: 30, unit: "天" },
  { amount: 12, unit: "个月" },
  { amount: Infinity, unit: "年" },
];

export function useRelativeTime(timestamp: string | number): string {
  const ts = typeof timestamp === "string" ? Number(timestamp) : timestamp;
  if (!ts) return "";
  let duration = (Date.now() / 1000 - ts) | 0;
  if (duration < 0) duration = 0;
  for (const div of DIVISIONS) {
    if (duration < div.amount) return `${duration}${div.unit}前`;
    duration = (duration / div.amount) | 0;
  }
  return "";
}
