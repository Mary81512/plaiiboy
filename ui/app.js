function setText(id, value) {
  const element = document.getElementById(id);

  if (element) {
    element.textContent = value;
  }
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
      setText("deck-status", status.activeDeck);
    }

    if (status.seekMode !== undefined) {
      setText("seek-status", status.seekMode);
    }

    if (status.lastInput !== undefined) {
      setText("last-input", status.lastInput);
    }

    if (status.lastAction !== undefined) {
      setText("last-action", status.lastAction);
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
