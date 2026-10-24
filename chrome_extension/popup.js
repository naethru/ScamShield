chrome.storage.local.get("lastAlert").then(({lastAlert}) => {
  if (!lastAlert) return;

  const alert = document.getElementById("alert");
  const emptyState = document.getElementById("empty-state");
  const source = document.getElementById("source");
  const reasons = document.getElementById("reasons");

  source.textContent = lastAlert.source
    ? `Website: ${lastAlert.source}`
    : "A Chrome website notification";

  for (const reason of lastAlert.reasons || []) {
    const item = document.createElement("li");
    item.textContent = reason;
    reasons.appendChild(item);
  }

  emptyState.hidden = true;
  alert.hidden = false;
});
