(function () {
  if (window.__scenarioSidebarTooltipInit__) {
    return;
  }
  window.__scenarioSidebarTooltipInit__ = true;

  var MIN_TOOLTIP_WIDTH = 176;
  var PREFERRED_TOOLTIP_WIDTH = 244;
  var MAX_TOOLTIP_WIDTH = 272;
  var VIEWPORT_PADDING = 8;
  var VERTICAL_PREFERENCE_PX = 112;
  var RIGHT_ALIGNED_TOOLTIP_SHIFT = 24;

  function isTooltipTrigger(element) {
    return (
      element instanceof HTMLElement &&
      element.classList.contains("scenario-sidebar-tooltip-trigger")
    );
  }

  function getActiveTooltipTriggers() {
    return Array.from(
      document.querySelectorAll(".scenario-sidebar-tooltip-trigger"),
    ).filter(function (trigger) {
      return (
        trigger === document.activeElement ||
        trigger.matches(":hover") ||
        trigger.matches(":focus-visible")
      );
    });
  }

  function setHorizontalPlacement(trigger, viewportRect, triggerRect) {
    var spaceOnLeft = triggerRect.right - viewportRect.left - VIEWPORT_PADDING;
    var spaceOnRight = viewportRect.right - triggerRect.left - VIEWPORT_PADDING;
    var useRightAlignedBubble = spaceOnLeft > spaceOnRight;
    var availableWidth = Math.max(
      Math.min(useRightAlignedBubble ? spaceOnLeft : spaceOnRight, MAX_TOOLTIP_WIDTH),
      0,
    );
    var tooltipWidth = Math.max(
      Math.min(availableWidth, PREFERRED_TOOLTIP_WIDTH),
      Math.min(availableWidth, MIN_TOOLTIP_WIDTH),
    );

    trigger.style.setProperty(
      "--tooltip-width",
      Math.floor(tooltipWidth) + "px",
    );
    trigger.style.setProperty(
      "--tooltip-max-width",
      Math.floor(availableWidth) + "px",
    );

    if (useRightAlignedBubble) {
      trigger.style.setProperty("--tooltip-left", "auto");
      trigger.style.setProperty(
        "--tooltip-right",
        "-" + RIGHT_ALIGNED_TOOLTIP_SHIFT + "px",
      );
      trigger.style.setProperty("--tooltip-arrow-left", "auto");
      trigger.style.setProperty(
        "--tooltip-arrow-right",
        "-" + (RIGHT_ALIGNED_TOOLTIP_SHIFT - 3) + "px",
      );
    } else {
      trigger.style.setProperty("--tooltip-left", "0px");
      trigger.style.setProperty("--tooltip-right", "auto");
      trigger.style.setProperty("--tooltip-arrow-left", "0.2rem");
      trigger.style.setProperty("--tooltip-arrow-right", "auto");
    }
  }

  function setVerticalPlacement(trigger, viewportRect, triggerRect) {
    var spaceBelow = viewportRect.bottom - triggerRect.bottom - VIEWPORT_PADDING;
    var spaceAbove = triggerRect.top - viewportRect.top - VIEWPORT_PADDING;
    var showAbove = spaceBelow < VERTICAL_PREFERENCE_PX && spaceAbove > spaceBelow;

    if (showAbove) {
      trigger.style.setProperty("--tooltip-top", "auto");
      trigger.style.setProperty("--tooltip-bottom", "calc(100% + 0.45rem)");
      trigger.style.setProperty(
        "--tooltip-hidden-transform",
        "translateY(0.15rem)",
      );
      trigger.style.setProperty("--tooltip-visible-transform", "translateY(0)");
      trigger.style.setProperty("--tooltip-arrow-top", "auto");
      trigger.style.setProperty("--tooltip-arrow-bottom", "calc(100% + 0.18rem)");
      trigger.style.setProperty(
        "--tooltip-arrow-origin-transform",
        "rotate(225deg)",
      );
    } else {
      trigger.style.setProperty("--tooltip-top", "calc(100% + 0.45rem)");
      trigger.style.setProperty("--tooltip-bottom", "auto");
      trigger.style.setProperty(
        "--tooltip-hidden-transform",
        "translateY(-0.15rem)",
      );
      trigger.style.setProperty("--tooltip-visible-transform", "translateY(0)");
      trigger.style.setProperty("--tooltip-arrow-top", "calc(100% + 0.18rem)");
      trigger.style.setProperty("--tooltip-arrow-bottom", "auto");
      trigger.style.setProperty(
        "--tooltip-arrow-origin-transform",
        "rotate(45deg)",
      );
    }
  }

  function positionTooltip(trigger) {
    if (!isTooltipTrigger(trigger)) {
      return;
    }

    var viewport = trigger.closest(".scenario-sidebar-content");
    var viewportRect = viewport
      ? viewport.getBoundingClientRect()
      : document.documentElement.getBoundingClientRect();
    var triggerRect = trigger.getBoundingClientRect();

    setHorizontalPlacement(trigger, viewportRect, triggerRect);
    setVerticalPlacement(trigger, viewportRect, triggerRect);
  }

  function refreshActiveTooltips() {
    getActiveTooltipTriggers().forEach(positionTooltip);
  }

  document.addEventListener(
    "mouseover",
    function (event) {
      var trigger = event.target.closest(".scenario-sidebar-tooltip-trigger");
      if (trigger) {
        positionTooltip(trigger);
      }
    },
    true,
  );

  document.addEventListener(
    "focusin",
    function (event) {
      var trigger = event.target.closest(".scenario-sidebar-tooltip-trigger");
      if (trigger) {
        positionTooltip(trigger);
      }
    },
    true,
  );

  window.addEventListener("resize", refreshActiveTooltips, { passive: true });
  document.addEventListener("scroll", refreshActiveTooltips, {
    capture: true,
    passive: true,
  });
})();
