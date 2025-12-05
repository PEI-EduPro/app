import { useState, useEffect } from "react";
import { X, Plus, Trash2 } from "lucide-react";
import { Card } from "@/components/ui/card";

interface Question {
  id: number;
  text: string;
  options: Record<number, string>; // Changed to Record
  answer: number;
}

interface QuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (question: Omit<Question, "id">) => void;
  onUpdate: (questionId: number, question: Omit<Question, "id">) => void;
  editingQuestion: { topicId: number; question: Question } | null;
  topicId: number | null;
}

export default function QuestionModal({
  isOpen,
  onClose,
  onCreate,
  onUpdate,
  editingQuestion,
  topicId
}: QuestionModalProps) {
  const [questionText, setQuestionText] = useState("");
  const [options, setOptions] = useState<{ id: number; value: string }[]>([
    { id: 1, value: "" },
    { id: 2, value: "" },
    { id: 3, value: "" },
    { id: 4, value: "" }
  ]);
  const [correctAnswer, setCorrectAnswer] = useState<number | null>(null);

  useEffect(() => {
    if (editingQuestion?.question) {
      const q = editingQuestion.question;
      setQuestionText(q.text);
      
      // Convert options object to array
      const optionsArray = Object.entries(q.options).map(([key, value]) => ({
        id: parseInt(key),
        value
      }));
      setOptions(optionsArray);
      setCorrectAnswer(q.answer);
    } else {
      setQuestionText("");
      setOptions([
        { id: 1, value: "" },
        { id: 2, value: "" },
        { id: 3, value: "" },
        { id: 4, value: "" }
      ]);
      setCorrectAnswer(null);
    }
  }, [editingQuestion]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!questionText.trim()) {
      alert("Por favor, insira o texto da questão");
      return;
    }
    
    // Check for empty options
    const emptyOptions = options.filter(opt => !opt.value.trim());
    if (emptyOptions.length > 0) {
      alert("Por favor, preencha todas as opções");
      return;
    }
    
    if (correctAnswer === null) {
      alert("Por favor, selecione a resposta correta");
      return;
    }

    // Convert options array back to object
    const optionsObject: { [key: number]: string } = {};
    options.forEach(opt => {
      optionsObject[opt.id] = opt.value.trim();
    });

    const questionData: Omit<Question, "id"> = {
      text: questionText.trim(),
      options: optionsObject,
      answer: correctAnswer
    };

    if (editingQuestion) {
      onUpdate(editingQuestion.question.id, questionData);
    } else if (topicId) {
      onCreate(questionData);
    }
    
    onClose();
  };

  const handleOptionChange = (id: number, value: string) => {
    setOptions(options.map(opt => 
      opt.id === id ? { ...opt, value } : opt
    ));
  };

  const addOption = () => {
    const newId = Math.max(...options.map(opt => opt.id)) + 1;
    setOptions([...options, { id: newId, value: "" }]);
  };

  const removeOption = (id: number) => {
    if (options.length <= 2) {
      alert("A questão deve ter pelo menos 2 opções");
      return;
    }
    
    const newOptions = options.filter(opt => opt.id !== id);
    setOptions(newOptions);
    
    // Reset correct answer if it was the removed option
    if (correctAnswer === id) {
      setCorrectAnswer(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="px-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">
              {editingQuestion ? "Editar Questão" : "Nova Questão"}
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            {/* Question Text */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Texto da Questão
              </label>
              <textarea
                value={questionText}
                onChange={(e) => setQuestionText(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition resize-none"
                placeholder="Escreva a questão aqui..."
                rows={3}
              />
            </div>

            {/* Options */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-4">
                <label className="block text-sm font-medium text-gray-700">
                  Opções de Resposta
                </label>
                <button
                  type="button"
                  onClick={addOption}
                  className="flex items-center gap-2 text-sm text-[#3263A8] hover:text-[#2a5390]"
                >
                  <Plus size={16} />
                  Adicionar Opção
                </button>
              </div>
              
              <div className="space-y-3">
                {options.map((option, index) => (
                  <div key={option.id} className="flex items-center gap-3 group">
                    <input
                      type="radio"
                      id={`option-${option.id}`}
                      name="correct-answer"
                      checked={correctAnswer === option.id}
                      onChange={() => setCorrectAnswer(option.id)}
                      className="h-5 w-5 text-blue-600"
                    />
                    <label
                      htmlFor={`option-${option.id}`}
                      className="flex-1 flex items-center gap-3"
                    >
                      <span className="w-8 text-sm font-medium text-gray-500">
                        {index + 1}.
                      </span>
                    <input
                      type="text"
                      value={option.value}
                      onChange={(e) => handleOptionChange(option.id, e.target.value)}
                      className={`flex-1 px-3 py-2 border rounded-lg outline-none transition
                        ${correctAnswer === option.id 
                          ? "border-green-500 focus:ring-2 focus:ring-green-500 focus:border-green-500"
                          : "border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        }`}
                      placeholder={`Opção ${index + 1}`}
                    />
                    </label>
                    {options.length > 2 && (
                      <button
                        type="button"
                        onClick={() => removeOption(option.id)}
                        className="p-2 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Remover opção"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-500 mt-3">
                Selecione a opção correta clicando no círculo ao lado
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-black text-white rounded-lg hover:bg-[#2e2e2e] transition-colors"
              >
                {editingQuestion ? "Guardar" : "Criar"}
              </button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}