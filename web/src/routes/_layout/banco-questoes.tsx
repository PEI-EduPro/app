import { AppBreadcrumb } from "@/components/app-breadcrumb";
import { Card } from "@/components/ui/card";
import { createFileRoute } from "@tanstack/react-router";
import { Plus, ChevronDown, ChevronRight, SquarePen, Trash2 } from "lucide-react";
import { useState, useEffect } from "react";
import TopicModal from "@/components/TopicModal";
import QuestionModal from "@/components/QuestionModal";
import XmlUploadButton from "@/components/XmlUploadButton";
import { useQuestions, useSubject, useCreateTopic, useUpdateTopic, useDeleteTopic, useCreateQuestion, useUpdateQuestion, useDeleteQuestion } from "@/hooks/use-questions";
import { z } from "zod";

const bancoQuestoesSearchSchema = z.object({
  ucId: z.number(),
});

export const Route = createFileRoute("/_layout/banco-questoes")({
  validateSearch: bancoQuestoesSearchSchema,
  component: BancoQuestões,
});

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

function BancoQuestões() {
  const { ucId } = Route.useSearch();
  const { data: subjectData } = useSubject(ucId);
  const { data: apiData, isLoading, error } = useQuestions(ucId);
  
  const createTopicMutation = useCreateTopic(ucId);
  const updateTopicMutation = useUpdateTopic(ucId);
  const deleteTopicMutation = useDeleteTopic(ucId);
  const createQuestionMutation = useCreateQuestion(ucId);
  const updateQuestionMutation = useUpdateQuestion(ucId);
  const deleteQuestionMutation = useDeleteQuestion(ucId);

  const [topics, setTopics] = useState<Topic[]>([]);
  const [showTopicModal, setShowTopicModal] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [editingTopic, setEditingTopic] = useState<Topic | null>(null);
  const [editingQuestion, setEditingQuestion] = useState<{
    topicId: number;
    question: Question;
  } | null>(null);
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null);

  // Transform API data to local state format
  useEffect(() => {
    if (apiData && typeof apiData === 'object' && 'subject_topics' in apiData) {
      const topicsObj = apiData.subject_topics as Record<string, any>;
      const transformedTopics: Topic[] = Object.values(topicsObj).map((topic: any) => ({
        id: topic.topic_id,
        name: topic.topic_name,
        questions: Object.values(topic.topic_questions || {}).reduce((acc: Record<number, Question>, q: any) => {
          acc[q.question_id] = {
            id: q.question_id,
            text: q.question_text,
            options: Object.values(q.question_options || {}).reduce((opts: Record<number, string>, opt: any) => {
              opts[opt.option_id] = opt.option_text;
              return opts;
            }, {}),
            answer: Object.values(q.question_options || {}).find((opt: any) => opt.is_correct)?.option_id || 0,
          };
          return acc;
        }, {}),
        isOpen: false,
      }));
      setTopics(transformedTopics);
    }
  }, [apiData]);

  // Topic CRUD operations
  const handleCreateTopic = (name: string) => {
    createTopicMutation.mutate(name);
  };

  const handleUpdateTopic = (id: number, name: string) => {
    updateTopicMutation.mutate({ id, name });
  };

  const handleDeleteTopic = (id: number) => {
    if (confirm("Deseja apagar este tópico e todas as suas questões?")) {
      deleteTopicMutation.mutate(id);
    }
  };

  // Question CRUD operations
  const handleCreateQuestion = (topicId: number, question: Omit<Question, "id">) => {
    const questions = [{
      topic_id: topicId,
      question_text: question.text,
    }];
    
    const options = Object.entries(question.options).map(([key, value]) => ({
      question_id: 0,
      option_text: value,
      value: parseInt(key) === question.answer,
    }));
    
    createQuestionMutation.mutate({ questions, options });
  };

  const handleUpdateQuestion = (topicId: number, questionId: number, question: Omit<Question, "id">) => {
    updateQuestionMutation.mutate({
      id: questionId,
      data: {
        id: questionId,
        topic_id: topicId,
        question_text: question.text,
      }
    });
  };

  const handleDeleteQuestion = (_topicId: number, questionId: number) => {
    if (confirm("Deseja apagar esta questão?")) {
      deleteQuestionMutation.mutate(questionId);
    }
  };

  const toggleTopic = (topicId: number) => {
    setTopics(topics.map(topic => 
      topic.id === topicId ? { ...topic, isOpen: !topic.isOpen } : topic
    ));
  };

  const closeAllTopics = () => {
    setTopics(topics.map(topic => ({ ...topic, isOpen: false })));
  };

  if (isLoading) {
    return (
      <div className="py-3.5 px-6 w-full">
        <AppBreadcrumb
          page="Banco de Questões"
          crumbs={[
            { name: "Unidades Curriculares", link: "/unidades-curriculares" },
            { name: subjectData?.name || "...", link: `/detalhes-uc?ucId=${ucId}` },
          ]}
        />
        <div className="flex justify-center items-center h-64">
          <p className="text-gray-500">Carregando questões...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-3.5 px-6 w-full">
        <AppBreadcrumb
          page="Banco de Questões"
          crumbs={[
            { name: "Unidades Curriculares", link: "/unidades-curriculares" },
            { name: subjectData?.name || "...", link: `/detalhes-uc?ucId=${ucId}` },
          ]}
        />
        <div className="flex justify-center items-center h-64">
          <p className="text-red-500">Erro ao carregar questões</p>
        </div>
      </div>
    );
  }

  return (
    <div className="py-3.5 px-6 w-full">
      <AppBreadcrumb
        page="Banco de Questões"
        crumbs={[
          { name: "Unidades Curriculares", link: "/unidades-curriculares" },
          { name: subjectData?.name || "...", link: `/detalhes-uc?ucId=${ucId}` },
        ]}
      />
      <div className="flex justify-center mb-8">
        <div className="text-center">
          <div className="text-5xl">
            {subjectData?.name || "UNIDADE CURRICULAR"}
          </div>
          <h1 className="text-3xl mt-4 text-[#3263A8]">
            Banco de questões
          </h1>
        </div>
      </div>

      <div className="flex mb-6 justify-between">
        {/* Upload XML File Button */}
        <XmlUploadButton />

        {/* Add Topic Button */}
        <button
          onClick={() => {
            closeAllTopics();
            setShowTopicModal(true);
          }}
          className="flex items-center gap-2 bg-[#3263A8] text-white px-4 py-2 rounded-lg hover:bg-[#2a5390] transition-colors"
        >
          <Plus size={20} />
          Adicionar Tópico
        </button>
      </div>

      {/* Topics List - One per line */}
      <div className="space-y-4">
        {topics.map(topic => (
          <Card key={topic.id} className="overflow-hidden p-0">
            {/* Topic Header */}
            <div className="flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors cursor-pointer">
              <div 
                className="flex items-center gap-3 flex-1"
                onClick={() => toggleTopic(topic.id)}
              >
                {topic.isOpen ? (
                  <ChevronDown size={20} className="text-gray-500" />
                ) : (
                  <ChevronRight size={20} className="text-gray-500" />
                )}
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-800">
                    {topic.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {Object.keys(topic.questions).length} {Object.keys(topic.questions).length === 1 ? 'questão' : 'questões'}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingTopic(topic);
                    setShowTopicModal(true);
                  }}
                  className="text-gray-600 hover:text-blue-600 p-1.5 rounded hover:bg-blue-50 transition-colors"
                  title="Editar tópico"
                >
                  <SquarePen className="w-5 h-5"/>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteTopic(topic.id);
                  }}
                  className="text-gray-600 hover:text-red-600 p-1.5 rounded hover:bg-red-50 transition-colors"
                  title="Excluir tópico"
                >
                  <Trash2 className="w-5 h-5"/>
                </button>
              </div>
            </div>

            {/* Questions Content (Collapsible) */}
            {topic.isOpen && (
              <div className="p-4 border-t">
                {Object.keys(topic.questions).length === 0 ? (
                  <div className="text-center py-6 text-gray-500">
                    <p>Nenhuma questão criada neste tópico</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {Object.entries(topic.questions).map(([, question]) => (
                      <QuestionItem
                        key={question.id}
                        question={question}
                        topicId={topic.id}
                        onEdit={() => {
                          setEditingQuestion({
                            topicId: topic.id,
                            question
                          });
                          setShowQuestionModal(true);
                        }}
                        onDelete={() => handleDeleteQuestion(topic.id, question.id)}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-center pb-6">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  closeAllTopics();
                  setSelectedTopicId(topic.id);
                  setShowQuestionModal(true);
                }}
                className="w-fit flex items-center gap-2 bg-black text-white px-4 py-2 rounded-lg hover:bg-[#2e2e2e] transition-colors"
              >
                <Plus size={16}/>
                Adicionar Questão
              </button>
            </div>
          </Card>
        ))}
        
        {/* Empty state */}
        {topics.length === 0 && (
          <Card className="p-8 border-dashed border-2 text-center">
            <p className="text-gray-500">Nenhum tópico criado ainda</p>
          </Card>
        )}
      </div>

      {/* Modals */}
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
          if (selectedTopicId) {
            handleCreateQuestion(selectedTopicId, question);
          }
        }}
        onUpdate={(questionId, question) => {
          if (editingQuestion) {
            handleUpdateQuestion(editingQuestion.topicId, questionId, question);
          }
        }}
        editingQuestion={editingQuestion}
        topicId={selectedTopicId}
      />
    </div>
  );
}

// Question Item Component for inline display
interface QuestionItemProps {
  question: Question;
  topicId: number;
  onEdit: () => void;
  onDelete: () => void;
}

function QuestionItem({ question, onEdit, onDelete }: QuestionItemProps) {
  return (
    <div className="group flex items-start gap-4 p-4 bg-white border rounded-lg hover:bg-gray-50 transition-colors">
      <div className="flex-1">
        <div className="flex items-start gap-3">
          <div className="mt-1">
            <div className="w-6 h-6 flex items-center justify-center rounded-full bg-blue-100 text-blue-600 text-xs font-medium">
              {question.id}
            </div>
          </div>
          <div className="flex-1">
            <h4 className="font-medium text-gray-800 mb-2">{question.text}</h4>
            <div className="space-y-2">
              {Object.entries(question.options).map(([key, value]) => (
                <div key={key} className="flex items-center gap-3">
                  <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${parseInt(key) === question.answer ? 'border-green-500 bg-green-500' : 'border-gray-300'}`}>
                    {parseInt(key) === question.answer && (
                      <div className="w-2 h-2 rounded-full bg-white"></div>
                    )}
                  </div>
                  <span className={`text-sm ${parseInt(key) === question.answer ? 'text-green-600 font-medium' : 'text-gray-600'}`}>
                    {value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={onEdit}
          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
          title="Editar questão"
        >
          <SquarePen className="w-4 h-4"/>
        </button>
        <button
          onClick={onDelete}
          className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Excluir questão"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default BancoQuestões;