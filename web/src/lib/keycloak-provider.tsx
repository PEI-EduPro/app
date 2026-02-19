/* eslint-disable @typescript-eslint/no-explicit-any */
import Keycloak from "keycloak-js";
import { useEffect, useState, type ReactNode } from "react";
import { KeycloakContext } from "./use-keycloak";

export interface KeycloakContextValue {
  keycloak: Keycloak;
  initialized: boolean;
}

interface KeycloakProviderProps {
  authClient: Keycloak;
  initOptions?: Keycloak.KeycloakInitOptions;
  children: ReactNode;
}

export function KeycloakProvider({
  authClient,
  initOptions,
  children,
}: KeycloakProviderProps) {
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if ((authClient as any)._initialized) return;
    (authClient as any)._initialized = true;

    authClient
      .init(initOptions ?? {})
      .then(() => setInitialized(true))
      .catch((err) => {
        console.error("Keycloak initialization failed", err);
        setInitialized(true);
      });
  }, [authClient, initOptions]);

  return (
    <KeycloakContext.Provider value={{ keycloak: authClient, initialized }}>
      {children}
    </KeycloakContext.Provider>
  );
}
