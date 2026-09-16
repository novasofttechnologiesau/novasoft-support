import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";

const VARIANT_STYLES: Record<Variant, string> = {
  primary: "bg-nova-accent hover:bg-nova-accentDark text-white",
  secondary: "bg-nova-surface hover:bg-nova-border text-nova-text border border-nova-border",
  danger: "bg-red-600 hover:bg-red-700 text-white",
  ghost: "hover:bg-nova-surface text-nova-muted hover:text-nova-text",
};

export function Button({
  variant = "primary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${VARIANT_STYLES[variant]} ${className}`}
      {...props}
    />
  );
}
