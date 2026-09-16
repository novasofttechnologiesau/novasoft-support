import { DIAGNOSTICS_PRIVACY_NOTICE } from "@novasoft/shared";
import { Button } from "./Button";

export function PrivacyNoticeModal({
  packLabel,
  onConfirm,
  onCancel,
}: {
  packLabel: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div className="w-full max-w-md rounded-xl border border-nova-border bg-nova-card p-6">
        <h2 className="mb-2 text-base font-semibold">Before we run {packLabel}</h2>
        <p className="mb-5 text-sm leading-relaxed text-nova-muted">{DIAGNOSTICS_PRIVACY_NOTICE}</p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
          <Button variant="primary" onClick={onConfirm}>
            Run Diagnostics
          </Button>
        </div>
      </div>
    </div>
  );
}
