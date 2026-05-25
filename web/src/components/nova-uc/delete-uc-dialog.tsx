import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Trash2 } from "lucide-react";

interface DeleteUcDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeleteUcDialog({
  open,
  onOpenChange,
  onConfirm,
  onCancel,
}: DeleteUcDialogProps) {
  return (
    <div onClick={(e) => e.stopPropagation()}>
      <AlertDialog open={open} onOpenChange={onOpenChange}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
              <Trash2 />
            </AlertDialogMedia>
            <AlertDialogTitle>Eliminar Unidade Curricular</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação irá eliminar permanentemente esta unidade curricular.
              Deseja continuar?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="w-full! flex flex-row justify-between!">
            <AlertDialogCancel
              variant="outline"
              size="lg"
              className="cursor-pointer"
              onClick={onCancel}
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              size="lg"
              variant="destructive"
              className="cursor-pointer"
              onClick={onConfirm}
            >
              Eliminar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
