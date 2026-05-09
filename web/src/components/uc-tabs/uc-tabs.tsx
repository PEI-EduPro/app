import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import BancoPerguntasTab from "./banco-perguntas-tab";
import ExamesTab from "./exames-tab";
import SalasTab from "./salas-tab";

interface UcTabsProps {
  realId: number;
  ucId: string;
  ucName: string;
  isRegente: boolean;
}

export default function UcTabs({ realId, ucName, isRegente }: UcTabsProps) {
  return (
    <Tabs
      defaultValue={isRegente ? "banco-perguntas" : "exames"}
      className="mb-7.5"
    >
      <div className="sticky top-0 z-10 bg-background pb-1 -mx-4 px-4 md:-mx-6 md:px-6">
        <TabsList>
          {isRegente && (
            <TabsTrigger className="cursor-pointer" value="banco-perguntas">
              Banco de Perguntas
            </TabsTrigger>
          )}
          <TabsTrigger className="cursor-pointer" value="exames">
            Exames
          </TabsTrigger>
          <TabsTrigger className="cursor-pointer" value="salas">
            Salas
          </TabsTrigger>
        </TabsList>
      </div>
      {isRegente && (
        <TabsContent value="banco-perguntas" className="mt-0">
          <BancoPerguntasTab realId={realId} />
        </TabsContent>
      )}
      <TabsContent value="exames" className="mt-0">
        <ExamesTab realId={realId} />
      </TabsContent>
      <TabsContent value="salas" className="mt-0">
        <SalasTab realId={realId} ucName={ucName} />
      </TabsContent>
    </Tabs>
  );
}
