import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

export class Controller3D {
  constructor(scene, camera) {
    this.scene = scene;
    this.camera = camera;
    this.loader = new GLTFLoader();
    this.controller = null;
    this.parts = {};
    this.originalPositions = {};
    this.targets = {};
  }

  load() {
    this.loader.load(
      "./assets/plaiiboyv3.glb",

      (gltf) => {
        this.controller = gltf.scene;
        this.scene.add(this.controller);
        const partNames = [
          "Cross",
          "Circle",
          "Square",
          "Triangle",

          "DpadUp",
          "DpadDown",
          "DpadLeft",
          "DpadRight",

          "LeftStick",
          "RightStick",

          "L1",
          "L2",
          "R1",
          "R2",

          "Share",
          "Options",
          "PS",

          "Touchpad",
          "Lightbar",
        ];

        partNames.forEach((name) => {
          const part = this.controller.getObjectByName(name);

          if (!part) {
            console.warn(`Controller-Teil nicht gefunden: ${name}`);
            return;
          }

          this.parts[name] = part;
          this.originalPositions[name] = part.position.clone();
          this.targets[name] = part.position.clone();
        });

        console.log("Gefundene Controller-Teile:", this.parts);

        // Abmessungen des gesamten Modells bestimmen
        const box = new THREE.Box3().setFromObject(this.controller);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        // Modell exakt um den Weltursprung zentrieren
        this.controller.position.sub(center);

        const maxDimension = Math.max(size.x, size.y, size.z);

        // Kamera automatisch passend vor das Modell stellen
        const distance =
          maxDimension /
          (2 * Math.tan(THREE.MathUtils.degToRad(this.camera.fov / 2)));

        this.camera.position.set(0, maxDimension * 0.15, distance * 1.0);
        this.camera.near = Math.max(distance / 100, 0.001);
        this.camera.far = distance * 100;
        this.camera.lookAt(0, 0, 0);
        this.camera.updateProjectionMatrix();

        console.log("Controller geladen:", this.controller);
        console.log("Modellgröße:", size);
      },

      (progress) => {
        if (progress.total > 0) {
          const percent = Math.round((progress.loaded / progress.total) * 100);
          console.log(`Controller wird geladen: ${percent}%`);
        }
      },

      (error) => {
        console.error("GLB konnte nicht geladen werden:", error);
      },
    );
  }
  setButtonPressed(name, pressed) {
    const originalPosition = this.originalPositions[name];
    const target = this.targets[name];

    if (!originalPosition || !target) {
      console.warn(`Animationsziel fehlt: ${name}`);
      return;
    }

    target.copy(originalPosition);

    if (pressed) {
      target.z -= 0.2;
    }
  }

  setControlActive(control, active) {
    console.log("3D-Eingabe:", control, active);
    const controlToPart = {
      CROSS: "Cross",
      CIRCLE: "Circle",
      SQUARE: "Square",
      TRIANGLE: "Triangle",

      DPAD_UP: "DpadUp",
      DPAD_DOWN: "DpadDown",
      DPAD_LEFT: "DpadLeft",
      DPAD_RIGHT: "DpadRight",

      L1: "L1",
      L2: "L2",
      R1: "R1",
      R2: "R2",

      SHARE: "Share",
      OPTIONS: "Options",
      PS: "PS",

      TOUCHPAD_CLICK: "Touchpad",
    };

    const partName = controlToPart[control];

    if (!partName) {
      return;
    }

    console.log("Bewege Teil:", partName, this.parts[partName]);

    this.setButtonPressed(partName, active);
  }
  update() {
    for (const name in this.parts) {
      const part = this.parts[name];
      const target = this.targets[name];

      if (!part || !target) continue;

      part.position.lerp(target, 0.25);
    }
  }
}
