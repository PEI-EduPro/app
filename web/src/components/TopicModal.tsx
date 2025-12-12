import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { Card } from "@/components/ui/card";

interface TopicModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string) => void;
  onUpdate: (id: number, name: string) => void;
  editingTopic: { id: number; name: string } | null;
}

export default function TopicModal({
  isOpen,
  onClose,
  onCreate,
  onUpdate,
  editingTopic
}: TopicModalProps) {
  const [topicName, setTopicName] = useState("");

  useEffect(() => {
    if (editingTopic) {
      setTopicName(editingTopic.name);
    } else {
      setTopicName("");
    }
  }, [editingTopic]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topicName.trim()) {
      if (editingTopic) {
        onUpdate(editingTopic.id, topicName.trim());
      } else {
        onCreate(topicName.trim());
      }
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-md">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-semibold">
              {editingTopic ? "Editar Tópico" : "Novo Tópico"}
            </h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nome do Tópico
              </label>
              <input
                type="text"
                value={topicName}
                onChange={(e) => setTopicName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                placeholder="Ex: Instruções de decisão, Recursividade, etc."
                autoFocus
              />
            </div>

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
                {editingTopic ? "Guardar" : "Criar"}
              </button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}