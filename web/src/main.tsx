import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import keycloak from './lib/keycloak'

// Import the generated route tree
import { routeTree } from './routeTree.gen'
import { Providers } from './lib/providers'

// Create a new router instance
const router = createRouter({ routeTree })

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

keycloak.init({
  onLoad: 'login-required',
  redirectUri: 'http://localhost:5173/', //TODO seria boa ideia por isto dinâmico
  checkLoginIframe: false
}).then((authenticated) => {
  if (!authenticated) {
    console.error('User is not authenticated');
    return;
  }

  console.log('Keycloak initialized successfully');

  setInterval(() => {
    keycloak.updateToken(70).catch(() => {
      console.error('Failed to refresh token');
    });
  }, 300000);

  // Render the app
  const rootElement = document.getElementById('root')!
  if (!rootElement.innerHTML) {
    const root = ReactDOM.createRoot(rootElement)
    root.render(
      <StrictMode>
        <Providers>
          <RouterProvider router={router} />
        </Providers>
      </StrictMode>,
    )
  }
}).catch((error) => {
  console.error('Failed to initialize Keycloak:', error);
});