import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";

export function StepItem({
  step,
  index,
  isLast,
  noExpand,
}: {
  step: {
    label: string;
    description?: ReactNode;
    action?: ReactNode;
  };
  index: number;
  isLast: boolean;
  noExpand?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next) {
      setTimeout(
        () =>
          ref.current?.scrollIntoView({ behavior: "smooth", block: "start" }),
        0,
      );
    }
  }

  return (
    <div ref={ref} className="flex gap-6">
      <div className="flex flex-col items-center shrink-0">
        <button
          onClick={toggle}
          className={cn(
            "w-11 h-11 rounded-full flex items-center justify-center text-base font-bold transition-all duration-300 ease-in-out cursor-pointer shrink-0",
            open ? "bg-primary text-white" : "bg-primary/30 text-primary",
          )}
        >
          {index + 1}
        </button>
        {!isLast && <div className="w-1 flex-1 min-h-4 bg-primary/30" />}
      </div>

      <div className="flex-1 pb-6">
        <button
          onClick={() => !noExpand && toggle()}
          className={cn(
            "flex items-center flex-row justify-between w-full text-left group h-11",
            !noExpand && "cursor-pointer",
          )}
        >
          <span
            className={cn(
              "font-semibold text-[#2E2B50] transition-colors text-lg",
              !noExpand && "group-hover:text-[#3263A8]",
            )}
          >
            {step.label}
          </span>
          <div className="flex items-center gap-4">
            {step.action && (
              <div onClick={(e) => e.stopPropagation()}>{step.action}</div>
            )}
            {!noExpand &&
              (open ? (
                <ChevronUp className="h-6 w-6 text-foreground shrink-0" />
              ) : (
                <ChevronDown className="h-6 w-6 text-foreground shrink-0" />
              ))}
          </div>
        </button>
        {open && <div className="mt-2">{step.description}</div>}
      </div>
    </div>
  );
}
