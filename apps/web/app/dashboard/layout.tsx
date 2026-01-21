import type { ReactNode } from "react";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return <div className="bg-slate-950 text-white">{children}</div>;
}
