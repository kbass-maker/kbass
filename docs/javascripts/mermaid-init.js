document.addEventListener("DOMContentLoaded", async () => {
  if (typeof mermaid === "undefined") {
    console.error("Mermaid library could not be loaded.");
    return;
  }

  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "neutral"
  });

  try {
    await mermaid.run({
      querySelector: ".mermaid"
    });
  } catch (error) {
    console.error("Mermaid diagram rendering failed:", error);
  }
});
