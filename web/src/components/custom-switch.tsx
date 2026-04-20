import { Switch } from "@/components/ui/switch";

export const CustomSwitch = (props: {
  leftLabel: string;
  rightLabel: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}) => {
  const { leftLabel, rightLabel, checked, onCheckedChange } = props;

  return (
    <div>
      <div className="relative inline-grid h-8 grid-cols-[1fr_1fr] items-center text-sm font-medium">
        <Switch
          checked={checked}
          onCheckedChange={() => onCheckedChange(!checked)}
          className="cursor-pointer peer data-[state=unchecked]:bg-input/50 absolute inset-0 rounded-md data-[size=default]:h-[inherit] data-[size=default]:w-auto [&_span]:z-10 [&_span]:rounded-sm [&_span]:transition-transform [&_span]:duration-300 [&_span]:ease-[cubic-bezier(0.16,1,0.3,1)] [&_span]:group-data-[size=default]/switch:h-full [&_span]:group-data-[size=default]/switch:w-1/2 [&_span]:data-[state=checked]:translate-x-full [&_span]:data-[state=checked]:rtl:-translate-x-full"
          aria-label="Square switch with permanent text indicators"
        />
        <span className="pointer-events-none relative ml-0.5 flex items-center justify-center px-2 text-center transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] peer-data-[state=checked]:invisible peer-data-[state=unchecked]:translate-x-full peer-data-[state=unchecked]:rtl:-translate-x-full">
          <span className="text-[10px] font-medium uppercase">{leftLabel}</span>
        </span>
        <span className="peer-data-[state=checked]:text-background pointer-events-none relative mr-0.5 flex items-center justify-center px-2 text-center transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] peer-data-[state=checked]:-translate-x-full peer-data-[state=unchecked]:invisible peer-data-[state=checked]:rtl:translate-x-full">
          <span className="text-[10px] font-medium uppercase">
            {rightLabel}
          </span>
        </span>
      </div>
    </div>
  );
};
