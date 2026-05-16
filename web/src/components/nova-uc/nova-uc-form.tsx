import { useGetUcProfessors, useGetUcRegent } from "@/hooks/use-ucs";
import { UCFormInner, type UCFormProps } from "./nova-uc-form-content";

function EditUCFormLoader({
  ucId,
  onSuccess,
  onCancel,
  lockRegente,
}: {
  ucId: number;
  onSuccess?: () => void;
  onCancel?: () => void;
  lockRegente?: boolean;
}) {
  const { data: regent, isLoading: loadingRegent } = useGetUcRegent(ucId);
  const { data: professors, isLoading: loadingProfs } =
    useGetUcProfessors(ucId);

  if (loadingRegent || loadingProfs) {
    return (
      <div className="flex justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <UCFormInner
      key={`${ucId}-${regent?.id}-${professors?.map((p) => p.id).join(",")}`}
      ucId={ucId}
      initialRegente={regent?.id}
      initialProfessores={professors?.map((p) => p.id)}
      onSuccess={onSuccess}
      onCancel={onCancel}
      lockRegente={lockRegente}
    />
  );
}

export function NovaUCForm(props: UCFormProps = {}) {
  if (props.ucId)
    return (
      <EditUCFormLoader
        ucId={props.ucId}
        onSuccess={props.onSuccess}
        onCancel={props.onCancel}
        lockRegente={props.lockRegente}
      />
    );
  return <UCFormInner {...props} />;
}
