export const encodeId = (id: number) => btoa(String(id));
export const decodeId = (encoded: string) => Number(atob(encoded));
