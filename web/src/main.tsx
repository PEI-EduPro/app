import { StrictMode } from "react";
import ReactDOM from "react-dom/client";

// Import the generated route tree
import { Providers } from "./lib/providers";
import { App } from "./App";

const rootElement = document.getElementById("root")!;
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <StrictMode>
      <Providers>
        <App />
      </Providers>
    </StrictMode>,
  );
}
