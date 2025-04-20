let pdfPath = null; // Start with no PDF loaded
let pdfDoc = null;
let currentPage = 1;

const canvas = document.getElementById("pdfCanvas");
const ctx = canvas.getContext("2d");

// Dynamically create click zones
const panelWrapper = document.getElementById("panelWrapper");

const leftZone = document.createElement("div");
leftZone.className = "click-zone click-zone-left";
panelWrapper.appendChild(leftZone);

const rightZone = document.createElement("div");
rightZone.className = "click-zone click-zone-right";
panelWrapper.appendChild(rightZone);

// Now attach event listeners to the created elements
leftZone.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    renderPage(currentPage);
  }
});

rightZone.addEventListener("click", () => {
  if (currentPage < pdfDoc.numPages) {
    currentPage++;
    renderPage(currentPage);
  }
});

function renderPage(pageNum) {
  pdfDoc.getPage(pageNum).then((page) => {
    const viewport = page.getViewport({ scale: 1.5 });
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    // 🌑 Fill canvas with current background color (before rendering page)
    ctx.save();
    ctx.fillStyle = getComputedStyle(canvas).backgroundColor;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.restore();

    const renderContext = {
      canvasContext: ctx,
      viewport: viewport
    };

    page.render(renderContext);
  });
}

function showWelcomeMessage() {
  const canvas = document.getElementById("pdfCanvas");
  const ctx = canvas.getContext("2d");

  // Set dimensions for placeholder canvas
  canvas.width = 800;
  canvas.height = 600;

  // Get current theme color
  const isLight = document.body.classList.contains("light-mode");
  const bgColor = isLight ? "#f3f1ec" : "#121212";
  const textColor = isLight ? "#222" : "#e0e0e0";

  // Fill background
  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Welcome text
  ctx.fillStyle = textColor;
  ctx.font = "24px 'Rajdhani', sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("🖋️ Your manga will appear here", canvas.width / 2, canvas.height / 2 - 10);
  ctx.fillText("Describe a scene and click Generate Panels!", canvas.width / 2, canvas.height / 2 + 30);
}


document.getElementById("themeToggle").addEventListener("change", () => {
  document.body.classList.toggle("light-mode");

  if (pdfDoc) {
    renderPage(currentPage); // if a PDF is loaded
  } else {
    showWelcomeMessage(); // fallback
  }
});


document.getElementById("downloadBtn").addEventListener("click", () => {
  const link = document.createElement("a");
  link.href = "/static/generated/manga_story.pdf"; // Adjust path if needed
  link.download = "manga_story.pdf"; // Desired filename
  link.click();
});

document.getElementById("generateBtn").addEventListener("click", () => {
  const prompt = document.querySelector(".prompt-box").value;

  // Temporary message
  const ctx = canvas.getContext("2d");
  canvas.width = 800;
  canvas.height = 600;
  const isLight = document.body.classList.contains("light-mode");
  ctx.fillStyle = isLight ? "#f3f1ec" : "#121212";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = isLight ? "#222" : "#fff";

  ctx.font = "20px 'Rajdhani', sans-serif";
  ctx.textAlign = "center";
  ctx.fillText("⏳ Generating your manga...", canvas.width / 2, canvas.height / 2);

  fetch("/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ prompt: prompt })
  })
  .then(response => response.json())
  .then(data => {
    console.log("✅ Generated Story:", data);
    loadNewPDF(data.title);
  })
  .catch(err => {
    console.error("❌ Error generating story:", err);
  });
});



function loadNewPDF(title) {
  const safeTitle = title.replace(/\s+/g, "_");
  pdfPath = `/static/generated/${safeTitle}.pdf`;

  pdfjsLib.getDocument(pdfPath).promise
  .then((doc) => {
    pdfDoc = doc;
    currentPage = 1;
    renderPage(currentPage);
  })
  .catch(err => {
    console.error("❌ Failed to load PDF:", err);
    showWelcomeMessage(); // Fallback
  });
}

// Show initial welcome screen on load
document.addEventListener("DOMContentLoaded", showWelcomeMessage);

