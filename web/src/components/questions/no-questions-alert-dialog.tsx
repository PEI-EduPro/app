import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { CircleAlert } from "lucide-react";

export function NoQuestionsAlertDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <div onClick={(e) => e.stopPropagation()}>
      <AlertDialog open={open} onOpenChange={onOpenChange}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogMedia className="bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
              <CircleAlert />
            </AlertDialogMedia>
            <AlertDialogTitle>Sem questões disponíveis</AlertDialogTitle>
            <AlertDialogDescription>
              Esta unidade curricular não tem nenhum tópico com questões
              associadas. Para criar um exame, é necessário ter pelo menos um
              tópico com uma questão.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel size="lg" className="cursor-pointer w-full">
              Fechar
            </AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
