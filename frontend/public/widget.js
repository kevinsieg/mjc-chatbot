(function () {
  var script = document.currentScript;
  var origin = script ? new URL(script.src).origin : window.location.origin;

  function init() {
  var embedUrl = origin + "/embed";
  var mascotUrl = origin + "/brand/goellan.png";

  var iframe = null;
  var isOpen = false;

  // Inject CSS for animations and hover effects
  var style = document.createElement("style");
  style.textContent =
    ".mjc-bubble{transition:transform 0.2s ease,box-shadow 0.2s ease;}" +
    ".mjc-bubble:hover{transform:scale(1.08);box-shadow:0 8px 28px rgba(0,112,184,0.35)!important;}" +
    ".mjc-bubble:hover .mjc-img{transform:scale(1.14);}" +
    ".mjc-img{display:block;transition:transform 0.25s ease;}" +
    ".mjc-pulse{position:fixed;bottom:24px;right:24px;width:64px;height:64px;" +
    "border-radius:50%;border:2px solid rgba(0,112,184,0.45);" +
    "pointer-events:none;z-index:9997;" +
    "animation:mjc-pulse 2s ease-out infinite;}" +
    ".mjc-pulse.mjc-hidden{display:none;}" +
    ".mjc-tooltip{position:fixed;bottom:38px;right:96px;" +
    "background:#fff;color:#0070B8;" +
    "font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;" +
    "font-size:13px;font-weight:600;line-height:1;" +
    "padding:8px 14px;border-radius:20px;" +
    "border:1.5px solid #0070B8;" +
    "box-shadow:0 4px 16px rgba(0,112,184,0.15);" +
    "white-space:nowrap;pointer-events:none;z-index:9998;" +
    "opacity:0;transform:translateX(10px);" +
    "transition:opacity 0.2s ease,transform 0.2s ease;}" +
    ".mjc-tooltip.mjc-visible{opacity:1;transform:translateX(0);}" +
    "@keyframes mjc-pulse{0%{transform:scale(1);opacity:0.7;}100%{transform:scale(1.7);opacity:0;}}";
  document.head.appendChild(style);

  // Pulse ring (idle attention effect, hidden once chat is opened)
  var pulse = document.createElement("div");
  pulse.className = "mjc-pulse";
  document.body.appendChild(pulse);

  // Tooltip
  var tooltip = document.createElement("div");
  tooltip.className = "mjc-tooltip";
  tooltip.textContent = "Une question sur la MJC ?";
  document.body.appendChild(tooltip);

  // Bubble button
  var bubble = document.createElement("button");
  bubble.className = "mjc-bubble";
  bubble.setAttribute("aria-label", "Ouvrir le chatbot MJC");
  bubble.setAttribute("type", "button");
  bubble.style.cssText =
    "position:fixed;bottom:24px;right:24px;width:64px;height:64px;" +
    "border-radius:50% 50% 4px 50%;border:2.5px solid #0070B8;cursor:pointer;" +
    "background:#fff;box-shadow:0 4px 20px rgba(0,112,184,0.25);z-index:9999;" +
    "padding:4px;display:flex;align-items:center;justify-content:center;";

  var img = document.createElement("img");
  img.src = mascotUrl;
  img.alt = "";
  img.className = "mjc-img";
  img.setAttribute("aria-hidden", "true");
  img.style.cssText = "width:40px;height:auto;";
  bubble.appendChild(img);
  document.body.appendChild(bubble);

  // Hover: show/hide tooltip
  bubble.addEventListener("mouseenter", function () {
    tooltip.classList.add("mjc-visible");
  });
  bubble.addEventListener("mouseleave", function () {
    tooltip.classList.remove("mjc-visible");
  });

  function createIframe() {
    iframe = document.createElement("iframe");
    iframe.src = embedUrl;
    iframe.title = "MJC Chatbot";
    iframe.style.cssText =
      "position:fixed;bottom:100px;right:24px;width:380px;height:580px;" +
      "border:none;border-radius:16px;" +
      "box-shadow:0 8px 32px rgba(0,0,0,0.18);z-index:9998;";
    document.body.appendChild(iframe);
  }

  bubble.addEventListener("click", function () {
    pulse.classList.add("mjc-hidden");
    tooltip.classList.remove("mjc-visible");

    if (!iframe) {
      createIframe();
      isOpen = true;
    } else {
      isOpen = !isOpen;
      iframe.style.display = isOpen ? "" : "none";
    }
  });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
