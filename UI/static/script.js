const pdfPath = "/static/generated/manga_story.pdf";
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

// Load and render PDF
pdfjsLib.getDocument(pdfPath).promise.then((doc) => {
  pdfDoc = doc;
  renderPage(currentPage);
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

document.getElementById("themeToggle").addEventListener("change", () => {
  document.body.classList.toggle("light-mode");
  renderPage(currentPage); // 🧠 This redraws the canvas using new theme background
});

document.getElementById("downloadBtn").addEventListener("click", () => {
  const link = document.createElement("a");
  link.href = "/static/generated/manga_story.pdf"; // Adjust path if needed
  link.download = "manga_story.pdf"; // Desired filename
  link.click();
});