import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { CustomTable } from "@/components/custom-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { createFileRoute, Link } from "@tanstack/react-router";
import {
  BookOpen,
  ClipboardList,
  FileQuestionMark,
  Pencil,
} from "lucide-react";
import { useState } from "react";

export const Route = createFileRoute("/_layout/detalhes-uc")({
  component: RouteComponent,
});

function RouteComponent() {
  const data: Record<string, string>[] = [
    {
      id: "m5gr84i9",
      nome: "Ken",
      email: "ken99@example.com",
    },
    {
      id: "3u1reuv4",
      nome: "Abe",
      email: "Abe45@example.com",
    },
    {
      id: "derv1ws0",
      nome: "Monserrat",
      email: "Monserrat44@example.com",
    },
    {
      id: "5kma53ae",
      nome: "Silas",
      email: "Silas22@example.com",
    },
    {
      id: "bhqecj4p",
      nome: "Carmella",
      email: "carmella@example.com",
    },
    {
      id: "a8k2x9mn",
      nome: "Patricia",
      email: "patricia12@example.com",
    },
    {
      id: "q7w3e5rt",
      nome: "Marcus",
      email: "marcus88@example.com",
    },
    {
      id: "z9x8c7vb",
      nome: "Diana",
      email: "diana.rose@example.com",
    },
    {
      id: "p4l5m6nk",
      nome: "Roberto",
      email: "roberto.silva@example.com",
    },
    {
      id: "h3j4k5lm",
      nome: "Sofia",
      email: "sofia.lima@example.com",
    },
    {
      id: "t6y7u8io",
      nome: "Gabriel",
      email: "gabriel.santos@example.com",
    },
    {
      id: "r2e3w4qa",
      nome: "Isabella",
      email: "isabella92@example.com",
    },
    {
      id: "n8m9b0vc",
      nome: "Lucas",
      email: "lucas.oliveira@example.com",
    },
    {
      id: "f5g6h7jk",
      nome: "Mariana",
      email: "mariana.costa@example.com",
    },
    {
      id: "d1s2a3zx",
      nome: "Felipe",
      email: "felipe.alves@example.com",
    },
    {
      id: "v4b5n6mc",
      nome: "Juliana",
      email: "juliana.pereira@example.com",
    },
    {
      id: "w7e8r9ty",
      nome: "Rafael",
      email: "rafael.cardoso@example.com",
    },
    {
      id: "i0o9p8lk",
      nome: "Beatriz",
      email: "beatriz.martins@example.com",
    },
    {
      id: "u6j7h8gf",
      nome: "Thiago",
      email: "thiago.ribeiro@example.com",
    },
    {
      id: "y5t4r3ew",
      nome: "Amanda",
      email: "amanda.ferreira@example.com",
    },
    {
      id: "q1w2e3rt",
      nome: "Bruno",
      email: "bruno.rocha@example.com",
    },
    {
      id: "a9s8d7fg",
      nome: "Larissa",
      email: "larissa.souza@example.com",
    },
    {
      id: "z6x5c4vb",
      nome: "Rodrigo",
      email: "rodrigo.gomes@example.com",
    },
    {
      id: "m3n4b5vc",
      nome: "Camila",
      email: "camila.dias@example.com",
    },
    {
      id: "k8l9p0oi",
      nome: "Daniel",
      email: "daniel.barbosa@example.com",
    },
    {
      id: "j7h6g5fd",
      nome: "Fernanda",
      email: "fernanda.araujo@example.com",
    },
    {
      id: "x2c3v4bn",
      nome: "Gustavo",
      email: "gustavo.monteiro@example.com",
    },
    {
      id: "s1a2q3we",
      nome: "Aline",
      email: "aline.mendes@example.com",
    },
  ];

  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [profsSelection, setProfsSelection] = useState(data);
  const [alunosSelection, setAlunosSelection] = useState(data);

  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page="Projeto em Engenharia Informatica"
        crumbs={[
          {
            name: "Unidades Curriculares",
            link: "/unidades-curriculares",
          },
        ]}
      />
      <div className="flex flex-row gap-[20px] items-center justify-center text-5xl mb-35">
        <span className="font-rubik">Projeto em Engenharia Informatica</span>
        <Pencil
          className={`cursor-pointer size-[50px] ${isEditing ? "fill-black stroke-1 stroke-white" : ""}`}
          onClick={() => {
            if (isEditing) {
              setAlunosSelection(data);
              setProfsSelection(data);
            }
            setIsEditing(!isEditing);
          }}
        />
      </div>
      <div className="flex flex-col gap-[60px] items-center">
        <div className="flex flex-col gap-[60px] w-[1050px]">
          <div className="flex flex-row gap-[60px] w-full">
            <div className="w-full flex flex-1 flex-col gap-[30px]">
              <div>
                <span className="text-[26px] font-medium">Regente</span>
                <Input
                  className={cn("shadow-none")}
                  value={"Manuel Pedro"}
                  readOnly
                />
              </div>
              <div>
                <span className="text-[26px] font-medium">Professores</span>
                <CustomTable
                  data={data}
                  isSelectable={isEditing}
                  rowSelection={profsSelection}
                  onChange={(e) => {
                    setProfsSelection(e);
                  }}
                />
              </div>
            </div>
            <div className="w-full flex-1 h-inherit">
              <span className="text-[26px] font-medium">Alunos</span>
              <CustomTable
                data={data}
                rowNumber={15}
                isSelectable={isEditing}
                rowSelection={alunosSelection}
                onChange={(e) => {
                  setAlunosSelection(e);
                }}
              />
            </div>
          </div>
          <div className="flex justify-between">
            {isEditing ? (
              <>
                <Button
                  className="cursor:pointer h-auto w-auto font-medium text-2xl py-[10px]"
                  size="lg"
                  variant="destructive"
                  onClick={() => {
                    setAlunosSelection(data);
                    setProfsSelection(data);
                    setIsEditing(false);
                  }}
                >
                  Cancelar
                </Button>
                <Button
                  size="lg"
                  className="cursor:pointer h-auto w-auto font-medium text-2xl py-[10px]"
                  onClick={() => {
                    setIsEditing(false);
                  }}
                >
                  Guardar
                </Button>
              </>
            ) : (
              <>
                <Link to="/detalhes-uc">
                  <Button className="cursor-pointer flex flex-row gap-[20px] h-auto w-auto px-[16px] py-[18px] bg-[#41B5C0] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                    <span className="w-fit font-medium text-[26px]">
                      Manuais
                    </span>
                    <BookOpen className="size-[50px]" />
                  </Button>
                </Link>
                <Link to="/detalhes-uc">
                  <Button className="cursor-pointer flex flex-row gap-[20px] h-auto w-auto px-[16px] py-[18px] bg-[#3263A8] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                    <span className="w-fit font-medium text-[26px]">
                      Banco de Perguntas
                    </span>
                    <FileQuestionMark className="size-[50px]" />
                  </Button>
                </Link>
                <Link to="/detalhes-uc">
                  <Button className="cursor-pointer flex flex-row gap-[20px] h-auto w-auto px-[16px] py-[18px] bg-[#2E2B50] border border-[#ffffff] shadow-[0px_4px_4px_0px_rgba(0,0,0,0.25)] active:shadow-none">
                    <span className="w-fit font-medium text-[26px]">
                      Gerar Testes
                    </span>
                    <ClipboardList className="size-[50px]" />
                  </Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
