import { HelpCircle } from "lucide-react";

import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import type { ReactNode } from "react";

interface HelperHoverCardProps {
  content: ReactNode;
  iconClassName?: string;
  side: "top" | "right" | "bottom" | "left";
  trigger?: ReactNode;
}

export default function HelperHoverCard({
  content,
  iconClassName,
  side,
  trigger,
}: HelperHoverCardProps) {
  return (
    <HoverCard openDelay={50} closeDelay={100}>
      <HoverCardTrigger className={trigger ? "flex self-stretch" : undefined}>
        {trigger || <HelpCircle className={iconClassName} />}
      </HoverCardTrigger>
      <HoverCardContent
        side={side}
        className="bg-gray-100 w-100 border border-gray-300 text-gray-700 shadow-md"
      >
        <p className="text-sm">{content}</p>
      </HoverCardContent>
    </HoverCard>
  );
}
