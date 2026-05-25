import signatureImg from "@/components/cenas_pa_mail/signature.jpg";
import examCaptureImg from "@/components/cenas_pa_mail/exam_example_pic.jpeg";

export const TOGGLE_OPTIONS = [
  { key: "exam_capture", label: "Captura do exame" },
  { key: "question_weights", label: "Pesos das questões" },
  { key: "red_green_cross_table", label: "Tabela vermelho/verde" },
  { key: "cumulative_score_table", label: "Tabela de pontuação cumulativa" },
] as const;

export type ToggleKey = (typeof TOGGLE_OPTIONS)[number]["key"];

const N = 20;

const CORRECT_ANSWERS = [
  "A",
  "B",
  "C",
  "D",
  "A",
  "B",
  "C",
  "D",
  "A",
  "B",
  "C",
  "D",
  "A",
  "B",
  "C",
  "D",
  "A",
  "B",
  "C",
  "D",
];
const STUDENT_ANSWERS = [
  "B",
  "B",
  "C",
  "A",
  "A",
  "D",
  "C",
  "D",
  "B",
  "B",
  "A",
  "D",
  "A",
  "C",
  "C",
  "D",
  "A",
  "B",
  "D",
  "D",
];
const LABELS = ["A", "B", "C", "D"];

const MOCK = {
  student_name: "Ana Silva",
  nmec: 12345,
  grade: 15.5,
  fraction: 25,
  questions: Array.from({ length: N }, (_, i) => i + 1),
  answer_grid: LABELS.map((label) => ({
    label,
    cells: Array.from({ length: N }, (_, i) => {
      const correct = CORRECT_ANSWERS[i] === label;
      const selected = STUDENT_ANSWERS[i] === label;
      return {
        bg: correct ? "green" : selected && !correct ? "red" : "",
        x: selected,
      };
    }),
  })),
  question_stats: Array.from({ length: N }, (_, i) => ({
    num: i + 1,
    weight: 4.0,
    penalty: 1.0,
  })),
  score_details: Array.from({ length: N }, (_, i) => {
    const correct = STUDENT_ANSWERS[i] === CORRECT_ANSWERS[i] ? 1 : 0;
    const incorrect = STUDENT_ANSWERS[i] !== "" && !correct ? 1 : 0;
    const score = correct ? 4.0 : incorrect ? -1.0 : 0.0;
    return {
      num: i + 1,
      correct,
      incorrect,
      score_display: score > 0 ? `+${score.toFixed(2)}` : score.toFixed(2),
      score_class: correct ? "bg-green" : incorrect ? "bg-red" : "",
      cumulative: 0,
    };
  }).map((q, i, arr) => ({
    ...q,
    cumulative: arr
      .slice(0, i + 1)
      .reduce((s, r) => s + (r.correct ? 4.0 : r.incorrect ? -1.0 : 0), 0),
  })),
};

const thStyle: React.CSSProperties = {
  padding: 6,
  border: "1px solid black",
  backgroundColor: "#f2f2f2",
};
const tdStyle: React.CSSProperties = { padding: 6, border: "1px solid black" };

export function EmailPreview({
  options,
  customText,
}: {
  options: Record<ToggleKey, boolean>;
  customText: string;
}) {
  return (
    <div
      style={{ fontFamily: "Arial, sans-serif", color: "#333", fontSize: 13 }}
    >
      {customText && (
        <div
          style={{ margin: "20px 0", lineHeight: 1.5, whiteSpace: "pre-wrap" }}
        >
          {customText}
        </div>
      )}
      <p>Identificação do aluno:</p>
      <table
        style={{
          borderCollapse: "collapse",
          width: "80%",
          margin: "0 auto",
          textAlign: "center",
          border: "1px solid black",
        }}
      >
        <thead>
          <tr>
            <th style={thStyle}>Nome</th>
            <th style={thStyle}>NMEC</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={tdStyle}>{MOCK.student_name}</td>
            <td style={tdStyle}>{MOCK.nmec}</td>
          </tr>
        </tbody>
      </table>
      <br />

      {options.exam_capture && (
        <>
          <p>
            Foto da sua tabela de resposta:
            <br />
            <br />
          </p>
          <img
            src={examCaptureImg}
            style={{
              maxWidth: "80%",
              height: "auto",
              display: "block",
              margin: "auto",
              border: "1px solid #ccc",
            }}
          />
          <br />
        </>
      )}

      {options.red_green_cross_table && (
        <>
          <p>A sua tabela digitalizada:</p>
          <table
            style={{
              borderCollapse: "collapse",
              width: "80%",
              margin: "0 auto",
              textAlign: "center",
              border: "1px solid black",
            }}
          >
            <thead>
              <tr>
                <th style={thStyle}></th>
                {MOCK.questions.map((q) => (
                  <th key={q} style={thStyle}>
                    {String(q).padStart(2, "0")}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MOCK.answer_grid.map((row) => (
                <tr key={row.label}>
                  <th style={thStyle}>{row.label}</th>
                  {row.cells.map((cell, i) => (
                    <td
                      key={i}
                      style={{
                        ...tdStyle,
                        backgroundColor:
                          cell.bg === "green"
                            ? "#a8e6cf"
                            : cell.bg === "red"
                              ? "#ff8b94"
                              : undefined,
                      }}
                    >
                      {cell.x ? <b>X</b> : ""}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <br />
          <div style={{ fontSize: 12 }}>
            <div>
              <span
                style={{
                  display: "inline-block",
                  width: 20,
                  height: 20,
                  border: "1px solid black",
                  backgroundColor: "#a8e6cf",
                  marginRight: 8,
                }}
              />
              Resposta correta
            </div>
            <div>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 20,
                  height: 20,
                  border: "1px solid black",
                  backgroundColor: "#a8e6cf",
                  marginRight: 8,
                }}
              >
                <b>X</b>
              </span>
              Resposta correta selecionada
            </div>
            <div>
              <span
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 20,
                  height: 20,
                  border: "1px solid black",
                  backgroundColor: "#ff8b94",
                  marginRight: 8,
                }}
              >
                <b>X</b>
              </span>
              Resposta incorreta selecionada
            </div>
          </div>
          <br />
        </>
      )}

      {options.question_weights && (
        <>
          <p>Distribuição de cotações por questão:</p>
          <table
            style={{
              borderCollapse: "collapse",
              width: "80%",
              margin: "0 auto",
              textAlign: "center",
              border: "1px solid black",
            }}
          >
            <tbody>
              <tr>
                <th style={thStyle}>Pergunta</th>
                {MOCK.question_stats.map((q) => (
                  <th key={q.num} style={thStyle}>
                    {q.num}
                  </th>
                ))}
              </tr>
              <tr>
                <th style={thStyle}>Cotação</th>
                {MOCK.question_stats.map((q) => (
                  <td key={q.num} style={tdStyle}>
                    {q.weight.toFixed(2)}
                  </td>
                ))}
              </tr>
              <tr>
                <th style={thStyle}>Desconto ({MOCK.fraction}%)</th>
                {MOCK.question_stats.map((q) => (
                  <td key={q.num} style={tdStyle}>
                    {q.penalty.toFixed(2)}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
          <br />
        </>
      )}

      {options.cumulative_score_table && (
        <>
          <p>Das suas respostas resultaram as seguintes cotações:</p>
          <table
            style={{
              borderCollapse: "collapse",
              width: "80%",
              margin: "0 auto",
              textAlign: "center",
              border: "1px solid black",
            }}
          >
            <tbody>
              <tr>
                <th style={thStyle}>Pergunta</th>
                {MOCK.score_details.map((q) => (
                  <th key={q.num} style={thStyle}>
                    {q.num}
                  </th>
                ))}
              </tr>
              <tr>
                <th style={thStyle}>Respostas corretas</th>
                {MOCK.score_details.map((q) => (
                  <td
                    key={q.num}
                    style={{
                      ...tdStyle,
                      backgroundColor: q.correct === 1 ? "#a8e6cf" : undefined,
                    }}
                  >
                    {q.correct}
                  </td>
                ))}
              </tr>
              <tr>
                <th style={thStyle}>Respostas incorretas</th>
                {MOCK.score_details.map((q) => (
                  <td
                    key={q.num}
                    style={{
                      ...tdStyle,
                      backgroundColor: q.incorrect > 0 ? "#ff8b94" : undefined,
                    }}
                  >
                    {q.incorrect}
                  </td>
                ))}
              </tr>
              <tr>
                <th style={thStyle}>Cotação obtida</th>
                {MOCK.score_details.map((q) => (
                  <td key={q.num} style={tdStyle}>
                    {q.score_display}
                  </td>
                ))}
              </tr>
              <tr>
                <th style={thStyle}>Cotação acumulada</th>
                {MOCK.score_details.map((q) => (
                  <td key={q.num} style={tdStyle}>
                    {q.cumulative.toFixed(2)}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
          <br />
        </>
      )}

      <div style={{ textAlign: "center", margin: "30px 0" }}>
        <div style={{ fontSize: 18, fontWeight: "bold", color: "#555" }}>
          Nota
        </div>
        <div
          style={{
            fontSize: 36,
            fontWeight: "bold",
            color: "#000",
            marginTop: 5,
          }}
        >
          {MOCK.grade.toFixed(2)}/20
        </div>
      </div>

      <p>
        <br />
        Continuação de um bom ano letivo.
        <br />
        <b>EduPro @ UA</b>
      </p>
      <div style={{ textAlign: "center", color: "#888", fontSize: 12 }}>
        Email enviado automaticamente.
        <br />
        Por favor não responda a este email.
      </div>
      <br />
      <br />
      <img
        src={signatureImg}
        style={{
          width: "100%",
          height: "auto",
          display: "block",
          margin: "auto",
        }}
      />
    </div>
  );
}
