import { HelpCircle } from "lucide-react";

import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";

interface HelperHoverCardProps {
  content: string;
  iconClassName?: string;
}

export default function HelperHoverCard({
  content,
  iconClassName,
}: HelperHoverCardProps) {
  return (
    <HoverCard openDelay={50} closeDelay={100}>
      <HoverCardTrigger className="text-gray-400 hover:text-gray-600 cursor-pointer transition-colors">
        <HelpCircle className={iconClassName} />
      </HoverCardTrigger>
      <HoverCardContent
        side="top"
        className="bg-gray-100 border border-gray-300 text-gray-700 shadow-md"
      >
        <p className="text-sm">{content}</p>
      </HoverCardContent>
    </HoverCard>
  );
}
