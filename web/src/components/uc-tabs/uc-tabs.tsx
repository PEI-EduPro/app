import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import BancoPerguntasTab from "./banco-perguntas-tab";
import ExamesTab from "./exames-tab";
import SalasTab from "./salas-tab";

interface UcTabsProps {
  realId: number;
  ucId: string;
  ucName: string;
}

export default function UcTabs({ realId, ucName }: UcTabsProps) {
  return (
    <Tabs defaultValue="banco-perguntas" className="mb-7.5">
      <TabsList>
        <TabsTrigger className="cursor-pointer" value="banco-perguntas">
          Banco de Perguntas
        </TabsTrigger>
        <TabsTrigger className="cursor-pointer" value="exames">
          Exames
        </TabsTrigger>
        <TabsTrigger className="cursor-pointer" value="salas">
          Salas
        </TabsTrigger>
      </TabsList>
      <TabsContent value="banco-perguntas">
        <BancoPerguntasTab realId={realId} />
      </TabsContent>
      <TabsContent value="exames">
        <ExamesTab realId={realId} />
      </TabsContent>
      <TabsContent value="salas">
        <SalasTab realId={realId} ucName={ucName} />
      </TabsContent>
    </Tabs>
  );
}
