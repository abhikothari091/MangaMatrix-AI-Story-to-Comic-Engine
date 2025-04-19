const panels = [
    "/static/images/panels/panel1.png",
    "/static/images/panels/panel2.png",
    "/static/images/panels/panel3.png",
    "/static/images/panels/panel4.png",
    "/static/images/panels/panel5.png"
  ];
  
  let currentIndex = 0;
  
  const scrollContainer = document.getElementById("panelScrollContainer");
  const panelImage = document.getElementById("panelImage");
  
  // Load current panel
  function updatePanel() {
    panelImage.style.opacity = 0; // Start fade-out
  
    setTimeout(() => {
      panelImage.src = panels[currentIndex];
      scrollContainer.scrollTo({ top: 0, behavior: "auto" });
      panelImage.onload = () => {
        panelImage.style.opacity = 1; // Fade-in after load
      };
    }, 200); // Delay gives a smooth transition feel
  }
  
  
  // Setup clickable zones
  const panelWrapper = document.getElementById("panelWrapper");
  
  const leftZone = document.createElement("div");
  leftZone.className = "click-zone click-zone-left";
  leftZone.addEventListener("click", () => {
    if (currentIndex > 0) {
      currentIndex--;
      updatePanel();
    }
  });
  
  const rightZone = document.createElement("div");
  rightZone.className = "click-zone click-zone-right";
  rightZone.addEventListener("click", () => {
    if (currentIndex < panels.length - 1) {
      currentIndex++;
      updatePanel();
    }
  });
  
  panelWrapper.appendChild(leftZone);
  panelWrapper.appendChild(rightZone);
  
  // Theme toggle
  document.getElementById("themeToggle").addEventListener("change", () => {
    document.body.classList.toggle("light-mode");
  });
  
  // Initial load
  updatePanel();
  