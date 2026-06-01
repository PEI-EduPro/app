import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import XmlUploadButton from "@/components/questions/xml-upload-button";
import {
  useQuestions,
  useCreateTopic,
  useUpdateTopic,
  useDeleteTopic,
  useCreateQuestion,
  useUpdateQuestion,
  useDeleteQuestion,
} from "@/hooks/use-questions";
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
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useState, useEffect } from "react";
import {
  Plus,
  ChevronDown,
  ChevronRight,
  SquarePen,
  Search,
  Trash2,
  Trash2Icon,
  FolderOpen,
  HelpCircle,
  CheckSquare,
  Info,
  FileCode,
} from "lucide-react";
import HelperHoverCard from "../helper-hover-card";
import QuestionModal from "../questions/question-modal";
import TopicModal from "../questions/topic-modal";

interface Question {
  id: number;
  text: string;
  options: Record<number, string>;
  answer: number;
}

interface Topic {
  id: number;
  name: string;
  questions: Record<number, Question>;
  isOpen: boolean;
}

interface QuestionItemProps {
  question: Question;
  questionNumber: number;
  topicId: number;
  onEdit: () => void;
  onDelete: () => void;
}

function QuestionItem({
  question,
  questionNumber,
  onEdit,
  onDelete,
}: QuestionItemProps) {
  return (
    <div className="group flex items-start gap-4 p-4 bg-card border border-border rounded-lg">
      <div className="flex-1">
        <div className="flex items-start gap-3">
          <div className="mt-1">
            <div className="w-6 h-6 flex items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-medium">
              {questionNumber}
            </div>
          </div>
          <div className="flex-1">
            <h4 className="font-medium text-foreground mb-2">{question.text}</h4>
            <div className="space-y-2">
              {Object.entries(question.options).map(([key, value]) => (
                <div key={key} className="flex items-center gap-3">
                  <div
                    className={`w-4 h-4 rounded-full border flex items-center justify-center ${parseInt(key) === question.answer ? "border-green-500 bg-green-500" : "border-border"}`}
                  >
                    {parseInt(key) === question.answer && (
                      <div className="w-2 h-2 rounded-full bg-white" />
                    )}
                  </div>
                  <span
                    className={`text-sm ${parseInt(key) === question.answer ? "text-green-500 font-medium" : "text-muted-foreground"}`}
                  >
                    {value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <Button
          variant="ghost"
          onClick={onEdit}
          className="p-1.5 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded transition-colors cursor-pointer"
          title="Editar questão"
        >
          <SquarePen className="w-4 h-4" />
        </Button>
        <div onClick={(e) => e.stopPropagation()}>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                className="p-1.5 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded transition-colors cursor-pointer"
                title="Excluir questão"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
                  <Trash2Icon />
                </AlertDialogMedia>
                <AlertDialogTitle>Apagar Questão</AlertDialogTitle>
                <AlertDialogDescription>
                  Deseja apagar esta questão?
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter className="w-full! flex flex-row justify-between!">
                <AlertDialogCancel
                  variant="outline"
                  className="cursor-pointer"
                  size="lg"
                >
                  Cancelar
                </AlertDialogCancel>
                <AlertDialogAction
                  size="lg"
                  variant="destructive"
                  className="cursor-pointer"
                  onClick={onDelete}
                >
                  Apagar
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </div>
  );
}

export default function BancoPerguntasTab({ realId }: { realId: number }) {
  const { data: apiData, isLoading, error } = useQuestions(realId);

  const createTopicMutation = useCreateTopic(realId);
  const updateTopicMutation = useUpdateTopic(realId);
  const deleteTopicMutation = useDeleteTopic(realId);
  const createQuestionMutation = useCreateQuestion(realId);
  const updateQuestionMutation = useUpdateQuestion(realId);
  const deleteQuestionMutation = useDeleteQuestion(realId);

  const [topics, setTopics] = useState<Topic[]>([]);
  const [showTopicModal, setShowTopicModal] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [xmlPreviewOpen, setXmlPreviewOpen] = useState(false);
  const [editingTopic, setEditingTopic] = useState<Topic | null>(null);
  const [editingQuestion, setEditingQuestion] = useState<{
    topicId: number;
    question: Question;
  } | null>(null);
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (apiData && typeof apiData === "object" && "subject_topics" in apiData) {
      const topicsObj = apiData.subject_topics as Record<string, any>;
      setTopics(
        Object.values(topicsObj).map((topic: any) => ({
          id: topic.topic_id,
          name: topic.topic_name,
          questions: Object.values(topic.topic_questions || {}).reduce(
            (acc: Record<number, Question>, q: any) => {
              acc[q.question_id] = {
                id: q.question_id,
                text: q.question_text,
                options: q.question_options || {},
                answer: q.answer || 0,
              };
              return acc;
            },
            {},
          ),
          isOpen: false,
        })),
      );
    }
  }, [apiData]);

  const handleCreateTopic = (name: string) => createTopicMutation.mutate(name);
  const handleUpdateTopic = (id: number, name: string) =>
    updateTopicMutation.mutate({ id, name });

  const handleCreateQuestion = (
    topicId: number,
    question: Omit<Question, "id">,
  ) => {
    createQuestionMutation.mutate({
      questions: [{ topic_id: topicId, question_text: question.text }],
      options: Object.entries(question.options).map(([key, value]) => ({
        question_id: 0,
        option_text: value,
        value: parseInt(key) === question.answer,
      })),
    });
  };

  const handleUpdateQuestion = (
    topicId: number,
    questionId: number,
    question: Omit<Question, "id">,
    oldOptions: Record<number, string>,
  ) => {
    const oldIds = new Set(Object.keys(oldOptions).map((id) => parseInt(id)));
    const newIds = new Set(
      Object.keys(question.options).map((id) => parseInt(id)),
    );
    updateQuestionMutation.mutate({
      id: questionId,
      data: { id: questionId, topic_id: topicId, question_text: question.text },
      toUpdate: Object.entries(question.options)
        .filter(([id]) => oldIds.has(parseInt(id)))
        .map(([id, text]) => ({
          id: parseInt(id),
          option_text: text,
          value: parseInt(id) === question.answer,
        })),
      toCreate: Object.entries(question.options)
        .filter(([id]) => !oldIds.has(parseInt(id)))
        .map(([id, text]) => ({
          question_id: questionId,
          option_text: text,
          value: parseInt(id) === question.answer,
        })),
      toDelete: [...oldIds].filter((id) => !newIds.has(id)),
    });
  };

  const toggleTopic = (topicId: number) =>
    setTopics(
      topics.map((t) => (t.id === topicId ? { ...t, isOpen: !t.isOpen } : t)),
    );

  const closeAllTopics = () =>
    setTopics(topics.map((t) => ({ ...t, isOpen: false })));

  if (isLoading)
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-muted-foreground">Carregando questões...</p>
      </div>
    );
  if (error)
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-red-500">Erro ao carregar questões</p>
      </div>
    );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 sticky top-10 z-10 bg-background py-2 -mx-4 px-4 md:-mx-6 md:px-6">
        <div className="flex gap-2 shrink-0 h-auto">
          <HelperHoverCard
            side="right"
            open={xmlPreviewOpen ? false : undefined}
            content={
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded bg-gray-700 flex items-center justify-center shrink-0">
                    <FileCode className="w-3.5 h-3.5 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-sm text-gray-800">
                      Formato Moodle XML
                    </p>
                    <p className="text-xs text-gray-400 font-mono">
                      .xml · exportado do Moodle
                    </p>
                  </div>
                </div>

                <p className="text-xs text-gray-600 leading-relaxed">
                  Ficheiro exportado diretamente do Moodle. As questões são
                  organizadas por{" "}
                  <span className="font-medium text-gray-800">categorias</span>,
                  que serão usadas como{" "}
                  <span className="font-medium text-gray-800">tópicos</span> no
                  exame.
                </p>

                <div className="space-y-1.5">
                  {[
                    {
                      icon: (
                        <FolderOpen className="w-3 h-3 text-gray-500 mt-0.5 shrink-0" />
                      ),
                      label: "Categorias",
                      desc: 'definidas por question type="category"',
                    },
                    {
                      icon: (
                        <HelpCircle className="w-3 h-3 text-gray-500 mt-0.5 shrink-0" />
                      ),
                      label: "Questões",
                      desc: 'do tipo multichoice com uma resposta correta (fraction="100")',
                    },
                    {
                      icon: (
                        <CheckSquare className="w-3 h-3 text-gray-500 mt-0.5 shrink-0" />
                      ),
                      label: "Opções de resposta",
                      desc: "pelo menos uma correta por questão",
                    },
                  ].map(({ icon, label, desc }) => (
                    <div key={label} className="flex items-start gap-2">
                      {icon}
                      <p className="text-xs text-gray-600 leading-snug">
                        <span className="font-medium text-gray-800">
                          {label}
                        </span>{" "}
                        — {desc}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="bg-gray-800 rounded-md px-3 py-2">
                  <p className="text-[10px] text-gray-500 mb-1.5 uppercase tracking-wide">
                    Exemplo
                  </p>
                  <pre className="text-[11px] text-gray-300 font-mono leading-relaxed overflow-x-auto">{`<quiz>
  <question type="category">
    <category><text>Spring</text></category>
  </question>

  <question type="multichoice">
    <questiontext>
      <text>What is a Spring Bean?</text>
    </questiontext>
    <answer fraction="100">
      <text>A managed object</text>
    </answer>
    <answer fraction="0">
      <text>A Java interface</text>
    </answer>
  </question>
</quiz>`}</pre>
                </div>

                <div className="flex gap-1.5 items-start rounded-md bg-blue-50 border border-blue-100 px-2.5 py-2">
                  <Info className="w-3 h-3 text-blue-500 mt-0.5 shrink-0" />
                  <p className="text-xs text-blue-700 leading-snug">
                    Para exportar do Moodle:{" "}
                    <span className="font-medium">
                      Banco de questões → Exportar → Formato Moodle XML
                    </span>
                    .
                  </p>
                </div>
              </div>
            }
            trigger={
              <XmlUploadButton
                subjectId={realId}
                onPreviewOpenChange={setXmlPreviewOpen}
              />
            }
          />
          <Button
            size="sm"
            onClick={() => {
              closeAllTopics();
              setShowTopicModal(true);
            }}
            className="gap-1 cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            Adicionar Tópico
          </Button>
        </div>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Pesquisar tópico..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {topics
          .filter((t) => t.name.toLowerCase().includes(search.toLowerCase()))
          .map((topic) => (
            <Card key={topic.id} className="overflow-hidden p-0">
              <div className="flex items-center justify-between p-4 bg-muted/50 hover:bg-muted transition-colors cursor-pointer">
                <div
                  className="flex items-center gap-3 flex-1"
                  onClick={() => toggleTopic(topic.id)}
                >
                  {topic.isOpen ? (
                    <ChevronDown size={20} className="text-muted-foreground" />
                  ) : (
                    <ChevronRight size={20} className="text-muted-foreground" />
                  )}
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-foreground">
                      {topic.name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {Object.keys(topic.questions).length}{" "}
                      {Object.keys(topic.questions).length === 1
                        ? "questão"
                        : "questões"}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingTopic(topic);
                      setShowTopicModal(true);
                    }}
                    className="text-muted-foreground hover:text-primary p-1.5 rounded hover:bg-primary/10 transition-colors cursor-pointer"
                    title="Editar tópico"
                  >
                    <SquarePen className="w-5 h-5" />
                  </Button>
                  <div onClick={(e) => e.stopPropagation()}>
                    <AlertDialog>
                      <AlertDialogTrigger asChild>
                        <Button
                          variant="ghost"
                          onClick={(e) => e.stopPropagation()}
                          className="text-muted-foreground hover:text-destructive p-1.5 rounded hover:bg-destructive/10 transition-colors cursor-pointer"
                          title="Excluir tópico"
                        >
                          <Trash2 className="w-5 h-5" />
                        </Button>
                      </AlertDialogTrigger>
                      <AlertDialogContent>
                        <AlertDialogHeader>
                          <AlertDialogMedia className="bg-destructive/10 text-destructive dark:bg-destructive/20 dark:text-destructive">
                            <Trash2Icon />
                          </AlertDialogMedia>
                          <AlertDialogTitle>Apagar Tópico</AlertDialogTitle>
                          <AlertDialogDescription>
                            Deseja apagar este tópico e todas as suas questões?
                          </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter className="w-full! flex flex-row justify-between!">
                          <AlertDialogCancel
                            variant="outline"
                            className="cursor-pointer"
                            size="lg"
                          >
                            Cancelar
                          </AlertDialogCancel>
                          <AlertDialogAction
                            size="lg"
                            variant="destructive"
                            className="cursor-pointer"
                            onClick={() => deleteTopicMutation.mutate(topic.id)}
                          >
                            Apagar
                          </AlertDialogAction>
                        </AlertDialogFooter>
                      </AlertDialogContent>
                    </AlertDialog>
                  </div>
                </div>
              </div>

              {topic.isOpen && (
                <div className="p-4 border-t">
                  {Object.keys(topic.questions).length === 0 ? (
                    <div className="text-center py-6 text-muted-foreground">
                      <p>Nenhuma questão criada neste tópico</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {Object.entries(topic.questions).map(
                        ([, question], index) => (
                          <QuestionItem
                            key={question.id}
                            question={question}
                            questionNumber={index + 1}
                            topicId={topic.id}
                            onEdit={() => {
                              setEditingQuestion({
                                topicId: topic.id,
                                question,
                              });
                              setShowQuestionModal(true);
                            }}
                            onDelete={() =>
                              deleteQuestionMutation.mutate(question.id)
                            }
                          />
                        ),
                      )}
                    </div>
                  )}
                </div>
              )}

              {topic.isOpen && (
                <div className="flex justify-center pb-6">
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      closeAllTopics();
                      setSelectedTopicId(topic.id);
                      setShowQuestionModal(true);
                    }}
                    className="h-10 flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-[#2e2e2e] transition-colors cursor-pointer"
                  >
                    <Plus className="h-5! w-5!" />
                    Adicionar Questão
                  </Button>
                </div>
              )}
            </Card>
          ))}

        {topics.filter((t) =>
          t.name.toLowerCase().includes(search.toLowerCase()),
        ).length === 0 && (
          <Card className="p-8 border-dashed border-2 text-center">
            <p className="text-muted-foreground">
              {search
                ? "Nenhum tópico encontrado"
                : "Para começar, adicione um tópico e acrescente perguntas ou importe um ficheiro XML."}
            </p>
          </Card>
        )}
      </div>

      <TopicModal
        isOpen={showTopicModal}
        onClose={() => {
          setShowTopicModal(false);
          setEditingTopic(null);
        }}
        onCreate={handleCreateTopic}
        onUpdate={handleUpdateTopic}
        editingTopic={editingTopic}
      />

      <QuestionModal
        isOpen={showQuestionModal}
        onClose={() => {
          setShowQuestionModal(false);
          setEditingQuestion(null);
          setSelectedTopicId(null);
        }}
        onCreate={(question) => {
          if (selectedTopicId) handleCreateQuestion(selectedTopicId, question);
        }}
        onUpdate={(questionId, question) => {
          if (editingQuestion)
            handleUpdateQuestion(
              editingQuestion.topicId,
              questionId,
              question,
              editingQuestion.question.options,
            );
        }}
        editingQuestion={editingQuestion}
        topicId={selectedTopicId}
      />
    </div>
  );
}
