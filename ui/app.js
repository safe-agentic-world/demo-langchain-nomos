const taskEl = document.getElementById("task");
const statusEl = document.getElementById("status");
const summaryEl = document.getElementById("summary");
const orderEl = document.getElementById("order");
const refundResultEl = document.getElementById("refund-result");
const compensationResultEl = document.getElementById("compensation-result");
const scenarioButtons = document.querySelectorAll(".scenario-card");

function setStatus(message) {
  statusEl.textContent = message;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function normalizeAssistantMessage(text) {
  if (!text) {
    return "";
  }
  const compact = String(text)
    .replaceAll("**", "")
    .replace(/\s+/g, " ")
    .trim();

  return compact
    .replace(/ (Order ID:)/g, "\n$1")
    .replace(/ (Customer:)/g, "\n$1")
    .replace(/ (Email:)/g, "\n$1")
    .replace(/ (Item:)/g, "\n$1")
    .replace(/ (Amount:)/g, "\n$1")
    .replace(/ (Status:)/g, "\n$1")
    .replace(/ (Shipping City:)/g, "\n$1")
    .replace(/ (Refund Eligible:)/g, "\n$1")
    .replace(/ (You are eligible for a refund for this order\.?)/g, "\n$1")
    .replace(/ (Would you like to proceed with the refund request\??)/g, "\n$1")
    .trim();
}

function setScenarioTask(task) {
  taskEl.value = task;
  scenarioButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.task === task);
  });
}

function renderSummary(data) {
  summaryEl.classList.remove("empty");
  summaryEl.innerHTML = `
    <div class="response-shell">
      <span class="pill pill-primary">Northwind Support</span>
      <p class="response-copy">${escapeHtml(normalizeAssistantMessage(data.final_agent_message)).replaceAll("\n", "<br>")}</p>
    </div>
  `;
}

function eligibilityText(order) {
  if (!order) return "Unknown";
  return order.refund_eligible ? "Eligible for refund" : "Not eligible right now";
}

function renderOrderDetails(order) {
  if (!order) {
    orderEl.className = "detail-panel empty";
    orderEl.textContent = "We will show your order details here.";
    return;
  }
  orderEl.className = "detail-panel";
  orderEl.innerHTML = `
    <div class="detail-list">
      <div><span>Order</span><strong>${escapeHtml(order.order_id)}</strong></div>
      <div><span>Customer</span><strong>${escapeHtml(order.customer)}</strong></div>
      <div><span>Item</span><strong>${escapeHtml(order.item)}</strong></div>
      <div><span>Status</span><strong>${escapeHtml(order.status)}</strong></div>
      <div><span>Total</span><strong>$${escapeHtml(order.amount)} ${escapeHtml(order.currency)}</strong></div>
      <div><span>Shipping City</span><strong>${escapeHtml(order.shipping_city)}</strong></div>
      <div><span>Refund Eligibility</span><strong>${escapeHtml(eligibilityText(order))}</strong></div>
    </div>
  `;
}

function renderRefundResult(data) {
  const order = data.order_details;
  const refund = data.refund_result;
  const refundRequest = data.refund_request;

  if (refund) {
    refundResultEl.className = "detail-panel";
    refundResultEl.innerHTML = `
      <div class="refund-shell success">
        <span class="pill pill-success">Refund Requested</span>
        <p>We submitted your refund request for <strong>${escapeHtml(refund.order_id)}</strong>.</p>
        <div class="detail-list compact">
          <div><span>Refund ID</span><strong>${escapeHtml(refund.refund_id)}</strong></div>
          <div><span>Status</span><strong>${escapeHtml(refund.status)}</strong></div>
          <div><span>Amount</span><strong>$${escapeHtml(refund.amount)} ${escapeHtml(refund.currency)}</strong></div>
          <div><span>Reason</span><strong>${escapeHtml(refund.reason)}</strong></div>
        </div>
      </div>
    `;
    return;
  }

  if (refundRequest && order && !order.refund_eligible) {
    refundResultEl.className = "detail-panel";
    refundResultEl.innerHTML = `
      <div class="refund-shell waiting">
        <span class="pill pill-neutral">Not Available</span>
        <p>This order is not currently eligible for a refund.</p>
      </div>
    `;
    return;
  }

  if (order && order.refund_eligible) {
    refundResultEl.className = "detail-panel";
    refundResultEl.innerHTML = `
      <div class="refund-shell waiting">
        <span class="pill pill-neutral">Eligible</span>
        <p>This order appears eligible for a refund if you would like to request one.</p>
      </div>
    `;
    return;
  }

  refundResultEl.className = "detail-panel empty";
  refundResultEl.textContent = "If a refund is requested, the latest status will appear here.";
}

function renderCompensationResult(data) {
  const compensation = data.compensation_result;
  const compensationRequest = data.compensation_request;

  if (compensation) {
    compensationResultEl.className = "detail-panel";
    compensationResultEl.innerHTML = `
      <div class="refund-shell warning">
        <span class="pill pill-warning">Compensation Approved</span>
        <p>An additional courtesy payment was approved for <strong>${escapeHtml(compensation.order_id)}</strong>.</p>
        <div class="detail-list compact">
          <div><span>Compensation ID</span><strong>${escapeHtml(compensation.compensation_id)}</strong></div>
          <div><span>Status</span><strong>${escapeHtml(compensation.status)}</strong></div>
          <div><span>Amount</span><strong>$${escapeHtml(compensation.amount)} ${escapeHtml(compensation.currency)}</strong></div>
          <div><span>Reason</span><strong>${escapeHtml(compensation.reason)}</strong></div>
        </div>
      </div>
    `;
    return;
  }

  if (compensationRequest) {
    compensationResultEl.className = "detail-panel";
    compensationResultEl.innerHTML = `
      <div class="refund-shell waiting">
        <span class="pill pill-neutral">Requested</span>
        <p>An additional compensation request was attempted.</p>
      </div>
    `;
    return;
  }

  compensationResultEl.className = "detail-panel empty";
  compensationResultEl.textContent = "If extra compensation is granted, the latest status will appear here.";
}

async function runAssistant() {
  setStatus("Checking your order...");
  const response = await fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task: taskEl.value }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  const data = await response.json();
  renderSummary(data);
  renderOrderDetails(data.order_details);
  renderRefundResult(data);
  renderCompensationResult(data);
  setStatus("Your support update is ready.");
}

document.getElementById("run-assistant").addEventListener("click", async () => {
  try {
    await runAssistant();
  } catch (error) {
    setStatus(`We could not complete that request: ${error.message}`);
  }
});

scenarioButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setScenarioTask(button.dataset.task);
    setStatus("Scenario selected.");
  });
});
