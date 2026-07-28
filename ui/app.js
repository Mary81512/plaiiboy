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

window.plaiiboy = {
  updateStatus(status) {
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
