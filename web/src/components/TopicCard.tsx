import { Card } from "@/components/ui/card";
import { Edit2, Trash2, Plus, FileText } from "lucide-react";

interface Question {
  id: number;
  text: string;
  options: {
    1: string;
    2: string;
    3: string;
    4: string;
  };
  answer: number;
}

interface Topic {
  id: number;
  name: string;
  questions: Record<number, Question>;
}

interface TopicCardProps {
  topic: Topic;
  onEdit: () => void;
  onDelete: () => void;
  onAddQuestion: () => void;
  onEditQuestion: (questionId: number) => void;
  onDeleteQuestion: (topicId: number, questionId: number) => void;
}

export default function TopicCard({
  topic,
  onEdit,
  onDelete,
  onAddQuestion,
  onEditQuestion,
  onDeleteQuestion
}: TopicCardProps) {
  const questionCount = Object.keys(topic.questions).length;

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-xl font-semibold text-gray-800">{topic.name}</h3>
          <p className="text-sm text-gray-500 mt-1">
            {questionCount} {questionCount === 1 ? 'questão' : 'questões'}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onEdit}
            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
            title="Editar tópico"
          >
            <Edit2 size={18} />
          </button>
          <button
            onClick={onDelete}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-full transition-colors"
            title="Excluir tópico"
          >
            <Trash2 size={18} />
          </button>
        </div>
      </div>

      {/* Questions List */}
      <div className="space-y-3 mb-4 max-h-60 overflow-y-auto pr-2">
        {Object.entries(topic.questions).map(([id, question]) => (
          <div
            key={id}
            className="flex items-center justify-between p-3 bg-gray-50 rounded-lg group"
          >
            <div className="flex items-center gap-3">
              <FileText size={16} className="text-gray-400" />
              <div>
                <p className="font-medium text-sm truncate max-w-[200px]">
                  {question.text}
                </p>
                <p className="text-xs text-gray-500">
                  Resposta: Opção {question.answer}
                </p>
              </div>
            </div>
            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => onEditQuestion(question.id)}
                className="p-1 text-gray-500 hover:text-blue-600"
                title="Editar questão"
              >
                <Edit2 size={14} />
              </button>
              <button
                onClick={() => onDeleteQuestion(topic.id, question.id)}
                className="p-1 text-gray-500 hover:text-red-600"
                title="Excluir questão"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}

        {questionCount === 0 && (
          <div className="text-center py-4 text-gray-500 text-sm">
            Nenhuma questão criada
          </div>
        )}
      </div>

      {/* Add Question Button */}
      <button
        onClick={onAddQuestion}
        className="w-full flex items-center justify-center gap-2 py-2 text-[#3263A8] hover:text-[#2a5390] hover:bg-blue-50 rounded-lg transition-colors border border-dashed border-gray-300"
      >
        <Plus size={18} />
        Adicionar Questão
      </button>
    </Card>
  );
}