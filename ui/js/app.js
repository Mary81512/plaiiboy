import { Scene3D } from "./scene.js";
let scene3d = null;

function setText(id, value) {
  const element = document.getElementById(id);

  if (element) {
    element.textContent = value;
  }
}

const inputLabels = {
  CROSS: "✕ Taste",
  CIRCLE: "○ Taste",
  SQUARE: "□ Taste",
  TRIANGLE: "△ Taste",

  DPAD_UP: "Steuerkreuz ↑",
  DPAD_DOWN: "Steuerkreuz ↓",
  DPAD_LEFT: "Steuerkreuz ←",
  DPAD_RIGHT: "Steuerkreuz →",

  LEFT_STICK: "Linker Stick",
  RIGHT_STICK: "Rechter Stick",
  L3: "Linker Stick-Klick",
  R3: "Rechter Stick-Klick",

  L1: "L1",
  L2: "L2",
  R1: "R1",
  R2: "R2",

  OPTIONS: "OPTIONS",
  SHARE: "SHARE",
  PS: "PS-Taste",

  TOUCHPAD_CLICK: "Touchpad Click",
  TOUCHPAD_SWIPE_LEFT: "Touchpad Swipe ←",
  TOUCHPAD_SWIPE_RIGHT: "Touchpad Swipe →",
  TOUCHPAD_SWIPE_UP: "Touchpad Swipe ↑",
  TOUCHPAD_SWIPE_DOWN: "Touchpad Swipe ↓",
};

const actionLabels = {
  DECK_1_PLAY_TOGGLE: "Deck A – Play/Pause",
  DECK_2_PLAY_TOGGLE: "Deck B – Play/Pause",

  DECK_1_CUE: "Deck A – Cue",
  DECK_2_CUE: "Deck B – Cue",

  DECK_1_SYNC: "Deck A – Sync",
  DECK_2_SYNC: "Deck B – Sync",

  DECK_1_LOAD_TRACK: "Track auf Deck A laden",
  DECK_2_LOAD_TRACK: "Track auf Deck B laden",

  BROWSER_UP: "Liste nach oben",
  BROWSER_DOWN: "Liste nach unten",

  BROWSER_LEVEL_UP: "Eine Ebene zurück",
  BROWSER_LEVEL_DOWN: "Öffnen",

  BROWSER_TREE_UP: "Liste nach oben",
  BROWSER_TREE_DOWN: "Liste nach unten",

  BROWSER_LIST_UP: "Liste nach oben",
  BROWSER_LIST_DOWN: "Liste nach unten",

  BROWSER_TREE_COLLAPSE: "Eine Ebene zurück",
  BROWSER_TREE_EXPAND: "Öffnen",

  TOGGLE_ACTIVE_DECK: "Aktives Deck wechseln",

  ACTIVE_DECK_HOTCUE_PREVIOUS: "Vorheriger Hotcue",
  ACTIVE_DECK_HOTCUE_NEXT: "Nächster Hotcue",
  ACTIVE_DECK_HOTCUE_TOGGLE: "Hotcue setzen/löschen",

  DECK_1_HOTCUE_PREVIOUS: "Deck A – Vorheriger Hotcue",
  DECK_1_HOTCUE_NEXT: "Deck A – Nächster Hotcue",
  DECK_1_HOTCUE_TOGGLE: "Deck A – Hotcue setzen/löschen",

  DECK_2_HOTCUE_PREVIOUS: "Deck B – Vorheriger Hotcue",
  DECK_2_HOTCUE_NEXT: "Deck B – Nächster Hotcue",
  DECK_2_HOTCUE_TOGGLE: "Deck B – Hotcue setzen/löschen",

  DECK_1_LOOP_SIZE_DECREASE: "Deck A – Loop verkleinern",
  DECK_1_LOOP_SIZE_INCREASE: "Deck A – Loop vergrößern",
  DECK_1_LOOP_TOGGLE: "Deck A – Loop ein/aus",

  DECK_2_LOOP_SIZE_DECREASE: "Deck B – Loop verkleinern",
  DECK_2_LOOP_SIZE_INCREASE: "Deck B – Loop vergrößern",
  DECK_2_LOOP_TOGGLE: "Deck B – Loop ein/aus",

  DECK_1_BPM_INCREASE: "Deck A – BPM erhöhen",
  DECK_1_BPM_DECREASE: "Deck A – BPM verringern",
  DECK_2_BPM_INCREASE: "Deck B – BPM erhöhen",
  DECK_2_BPM_DECREASE: "Deck B – BPM verringern",

  ACTIVE_DECK_SEEK_BACKWARD: "Aktives Deck – Zurückspulen",
  ACTIVE_DECK_SEEK_FORWARD: "Aktives Deck – Vorspulen",

  DECK_1_SEEK_FINE_BACKWARD: "Deck A – 1 Takt zurück",
  DECK_1_SEEK_FINE_FORWARD: "Deck A – 1 Takt vor",
  DECK_1_SEEK_4_BARS_BACKWARD: "Deck A – 4 Takte zurück",
  DECK_1_SEEK_4_BARS_FORWARD: "Deck A – 4 Takte vor",
  DECK_1_SEEK_8_BARS_BACKWARD: "Deck A – 8 Takte zurück",
  DECK_1_SEEK_8_BARS_FORWARD: "Deck A – 8 Takte vor",

  DECK_2_SEEK_FINE_BACKWARD: "Deck B – 1 Takt zurück",
  DECK_2_SEEK_FINE_FORWARD: "Deck B – 1 Takt vor",
  DECK_2_SEEK_4_BARS_BACKWARD: "Deck B – 4 Takte zurück",
  DECK_2_SEEK_4_BARS_FORWARD: "Deck B – 4 Takte vor",
  DECK_2_SEEK_8_BARS_BACKWARD: "Deck B – 8 Takte zurück",
  DECK_2_SEEK_8_BARS_FORWARD: "Deck B – 8 Takte vor",

  CYCLE_SEEK_SPEED: "Touchpad-Suchmodus wechseln",

  FEEDBACK_ACTIVE_DECK_1: "Deck A ausgewählt",
  FEEDBACK_ACTIVE_DECK_2: "Deck B ausgewählt",
};

function makeReadableFallback(value) {
  if (typeof value !== "string") {
    return value;
  }

  return value
    .toLowerCase()
    .split("_")
    .map((word) => {
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(" ");
}

function formatInput(input) {
  if (input === undefined || input === null || input === "") {
    return "—";
  }

  return inputLabels[input] ?? makeReadableFallback(input);
}

function formatAction(action) {
  if (action === undefined || action === null || action === "") {
    return "—";
  }

  return actionLabels[action] ?? makeReadableFallback(action);
}

const activeControls = new Map();

function findControlElements(control) {
  return document.querySelectorAll(`[data-control="${control}"]`);
}

function setControlActive(control, active) {
  const elements = findControlElements(control);

  elements.forEach((element) => {
    element.classList.toggle("is-active", active);
  });

  scene3d?.controller?.setControlActive(control, active);
}

function pulseControl(control, duration = 180) {
  setControlActive(control, true);

  const existingTimer = activeControls.get(control);

  if (existingTimer !== undefined) {
    clearTimeout(existingTimer);
  }

  const timer = setTimeout(() => {
    setControlActive(control, false);
    activeControls.delete(control);
  }, duration);

  activeControls.set(control, timer);
}

function showTouchpadFeedback(control) {
  const feedback = document.getElementById("touchpad-feedback");

  if (!feedback) {
    return;
  }

  const labels = {
    TOUCHPAD_CLICK: "Click",
    TOUCHPAD_SWIPE_LEFT: "Swipe ←",
    TOUCHPAD_SWIPE_RIGHT: "Swipe →",
    TOUCHPAD_SWIPE_UP: "Swipe ↑",
    TOUCHPAD_SWIPE_DOWN: "Swipe ↓",
  };

  feedback.textContent = labels[control] ?? "Touchpad";
}

function handleControllerEvent(event) {
  if (!event || !event.control) {
    return;
  }

  const control = event.control;
  const eventType = String(event.eventType ?? "");
  const value = Number(event.value ?? 0);

  if (control.startsWith("TOUCHPAD_")) {
    showTouchpadFeedback(control);
  }

  const isPressed =
    eventType.includes("PRESSED") || eventType.includes("HELD") || value > 0.5;

  const isReleased = eventType.includes("RELEASED") || eventType.includes("UP");

  if (isReleased) {
    setControlActive(control, false);
    return;
  }

  if (isPressed) {
    setControlActive(control, true);
    return;
  }

  /*
   * Manche Events wie Swipe oder Double Press haben kein separates
   * Release-Event. Diese werden deshalb kurz sichtbar aufgeblendet.
   */
  pulseControl(control);
}

const orientation = {
  pitch: 0,
  yaw: 0,
  roll: 0,
};

let lastMotionTime = null;

function handleMotion(motion) {
  const controller = scene3d?.controller;

  if (
    !motion ||
    !controller ||
    typeof controller.setOrientation !== "function"
  ) {
    return;
  }

  const currentTime = performance.now();

  if (lastMotionTime === null) {
    lastMotionTime = currentTime;
    return;
  }

  /*
   * Vergangene Zeit in Sekunden.
   * Große Sprünge werden begrenzt, etwa wenn das Fenster kurz hängt.
   */
  const deltaTime = Math.min((currentTime - lastMotionTime) / 1000, 0.05);

  lastMotionTime = currentTime;

  const gyroX = Number(motion.gyroX ?? 0);
  const gyroY = Number(motion.gyroY ?? 0);
  const gyroZ = Number(motion.gyroZ ?? 0);

  /*
   * Kleine Ruhewerte ignorieren, damit das Modell weniger driftet.
   */
  const deadzone = 80;

  const filteredGyroX = Math.abs(gyroX) >= deadzone ? gyroX : 0;

  const filteredGyroY = Math.abs(gyroY) >= deadzone ? gyroY : 0;

  const filteredGyroZ = Math.abs(gyroZ) >= deadzone ? gyroZ : 0;

  /*
   * Rohwert → ungefährer Winkel pro Sekunde.
   * Kann später nach Gefühl angepasst werden.
   */
  const sensitivity = 0.0012;

  orientation.pitch += filteredGyroX * sensitivity * deltaTime;

  orientation.yaw += filteredGyroZ * sensitivity * deltaTime;

  orientation.roll += filteredGyroY * sensitivity * deltaTime;

  controller.setOrientation(
    orientation.pitch,
    orientation.yaw,
    orientation.roll,
  );
}

function readAxis(axes, ...names) {
  for (const name of names) {
    if (axes[name] !== undefined) {
      return Number(axes[name]);
    }
  }

  return 0;
}

function normalizeStickAxis(value) {
  if (!Number.isFinite(value)) {
    return 0;
  }

  /*
   * Unterstützt sowohl bereits normalisierte Werte von -1 bis 1
   * als auch rohe Controllerwerte von 0 bis 255.
   */
  let normalized = value;

  if (value < -1 || value > 1) {
    normalized = (value - 127.5) / 127.5;
  }

  normalized = THREEClamp(normalized, -1, 1);

  /*
   * Kleine Bewegungen in der Stickmitte ausblenden.
   */
  const deadzone = 0.08;

  if (Math.abs(normalized) < deadzone) {
    return 0;
  }

  const direction = Math.sign(normalized);
  const magnitude = (Math.abs(normalized) - deadzone) / (1 - deadzone);

  return direction * magnitude;
}

function THREEClamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

function handleAxes(axes) {
  const controller = scene3d?.controller;

  if (!axes || !controller || typeof controller.setStickTilt !== "function") {
    return;
  }

  const leftX = normalizeStickAxis(
    readAxis(axes, "LEFT_STICK_X", "LEFT_X", "LX"),
  );

  const leftY = normalizeStickAxis(
    readAxis(axes, "LEFT_STICK_Y", "LEFT_Y", "LY"),
  );

  const rightX = normalizeStickAxis(
    readAxis(axes, "RIGHT_STICK_X", "RIGHT_X", "RX"),
  );

  const rightY = normalizeStickAxis(
    readAxis(axes, "RIGHT_STICK_Y", "RIGHT_Y", "RY"),
  );

  controller.setStickTilt("LeftStick", leftX, leftY);

  controller.setStickTilt("RightStick", rightX, rightY);
}

window.plaiiboy = {
  updateStatus(status) {
    if (status.axes !== undefined) {
      handleAxes(status.axes);
    }

    if (status.motion !== undefined) {
      handleMotion(status.motion);
    }

    if (status.controllerEvent !== undefined) {
      handleControllerEvent(status.controllerEvent);
    }

    if (status.controller !== undefined) {
      setText("controller-status", status.controller);
    }

    if (status.midi !== undefined) {
      setText("midi-status", status.midi);
    }

    if (status.layer !== undefined) {
      setText("layer-status", status.layer);
    }

    if (status.activeDeck !== undefined) {
      const deck =
        status.activeDeck === 1 || status.activeDeck === "1"
          ? "Deck A"
          : status.activeDeck === 2 || status.activeDeck === "2"
            ? "Deck B"
            : status.activeDeck;

      setText("deck-status", deck);
    }

    if (status.seekMode !== undefined) {
      setText("seek-status", status.seekMode);
    }

    if (status.lastInput !== undefined) {
      setText("last-input", formatInput(status.lastInput));
    }

    if (status.lastAction !== undefined) {
      setText("last-action", formatAction(status.lastAction));
    }
  },
};

async function notifyPythonThatInterfaceIsReady() {
  if (!window.pywebview?.api) {
    return;
  }

  try {
    await window.pywebview.api.ready();
  } catch (error) {
    console.error("Interface konnte nicht initialisiert werden:", error);
  }
}

window.addEventListener("pywebviewready", notifyPythonThatInterfaceIsReady);

window.addEventListener("DOMContentLoaded", () => {
  scene3d = new Scene3D(document.getElementById("controller3d"));
});
