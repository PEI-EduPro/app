import Keycloak from "keycloak-js";

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080",
  realm: "edupro",
  clientId: "frontend",
});

export const keycloakInitOptions = {
  onLoad: "check-sso" as const,
  checkLoginIframe: false,
};
