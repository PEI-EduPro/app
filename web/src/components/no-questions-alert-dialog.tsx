import { Link } from "@tanstack/react-router";
import { encodeId } from "@/lib/id-encoder";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export function NoQuestionsAlertDialog({
  open,
  onOpenChange,
  ucId,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  ucId: number;
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Sem questões disponíveis</AlertDialogTitle>
          <AlertDialogDescription>
            Esta unidade curricular não tem nenhum tópico com questões
            associadas. Para criar um exame, é necessário ter pelo menos um
            tópico com uma questão.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Fechar</AlertDialogCancel>
          <Link to="/banco-questoes" search={{ ucId: encodeId(ucId) }}>
            <AlertDialogAction>Ir para o Banco de Questões</AlertDialogAction>
          </Link>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
