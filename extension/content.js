function extractSemanticContent() {
  const headings = Array.from(
    document.querySelectorAll("h1, h2, h3")
  ).slice(0, 5).map(h => h.innerText.trim());

  const text = document.body.innerText
    .replace(/\s+/g, " ")
    .slice(0, 1500);

  return { headings, text };
}

chrome.runtime.sendMessage({
  type: "SEMANTIC_CONTENT",
  payload: extractSemanticContent()
});