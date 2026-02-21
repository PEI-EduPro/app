import { createContext, useContext } from "react";
import { type KeycloakContextValue } from "../lib/keycloak-provider";

export function useKeycloak(): KeycloakContextValue {
  const ctx = useContext(KeycloakContext);
  if (!ctx) {
    throw new Error("useKeycloak must be used within a <KeycloakProvider>");
  }
  return ctx;
}

export const KeycloakContext = createContext<KeycloakContextValue | null>(null);
