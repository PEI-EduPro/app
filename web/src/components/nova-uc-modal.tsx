import { NovaUCForm } from "@/components/nova-uc-form";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface UcModalProps {
  onClose: () => void;
  ucId?: number;
  ucName?: string;
}

export function NovaUcModal({ onClose, ucId, ucName }: UcModalProps) {
  const isEdit = !!ucId;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="bg-background rounded-xl shadow-2xl w-full max-w-3xl m-4 max-h-[90vh] overflow-y-auto p-8 flex flex-col gap-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <span className="font-rubik text-2xl font-bold">
            {isEdit ? ucName : "Nova Unidade Curricular"}
          </span>
          <Button variant="ghost" size="icon" className="cursor-pointer" onClick={onClose}>
            <X />
          </Button>
        </div>
        <NovaUCForm ucId={ucId} onSuccess={onClose} onCancel={onClose} />
      </div>
    </div>
  );
}
