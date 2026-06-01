import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useRef, useState, type ReactNode } from "react";
import HelperHoverCard from "@/components/helper-hover-card";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function StepItem({
  step,
  index,
  isLast,
  noExpand,
  disabled,
  progress,
}: {
  step: {
    label: string;
    description?: ReactNode;
    action?: ReactNode;
    hint?: ReactNode;
  };
  index: number;
  isLast: boolean;
  noExpand?: boolean;
  disabled?: boolean;
  progress?: 0 | 1 | 2;
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
    <div ref={ref} className={cn("flex gap-6", disabled && "opacity-50")}>
      <div className="flex flex-col items-center shrink-0">
        <button
          onClick={!disabled ? toggle : undefined}
          className={cn(
            "w-11 h-11 rounded-full flex items-center justify-center text-base font-bold transition-all duration-300 ease-in-out shrink-0",
            !disabled && "cursor-pointer",
            disabled && "cursor-not-allowed",
            progress === 2
              ? "bg-primary text-white"
              : progress === 1
                ? "bg-primary/60 text-white"
                : "bg-primary/20 text-primary/40",
          )}
        >
          {index + 1}
        </button>
        {!isLast && (
          <div
            className={cn(
              "w-1 flex-1 min-h-4 transition-colors duration-300",
              progress === 2 ? "bg-primary" : "bg-primary/20",
            )}
          />
        )}
      </div>

      <div className="flex-1 pb-6">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={() => !noExpand && !disabled && toggle()}
              className={cn(
                "flex items-center flex-row justify-between w-full text-left group h-11",
                !noExpand && !disabled && "cursor-pointer",
                disabled && "cursor-not-allowed",
              )}
            >
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    "font-semibold text-foreground transition-colors text-lg",
                    !noExpand && !disabled && "group-hover:text-primary",
                  )}
                >
                  {step.label}
                </span>
                {step.hint && (
                  <div
                    className="cursor-pointer"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <HelperHoverCard
                      content={step.hint}
                      side="right"
                      iconClassName="h-5 w-5 text-muted-foreground"
                    />
                  </div>
                )}
              </div>
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
          </TooltipTrigger>
          {disabled && (
            <TooltipContent>
              Este passo ficará disponível quando os anteriores estiverem
              concluídos.
            </TooltipContent>
          )}
        </Tooltip>
        {open && <div className="mt-2">{step.description}</div>}
      </div>
    </div>
  );
}
