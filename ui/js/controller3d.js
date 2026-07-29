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
    this.originalRotations = {};
    this.targets = {};
    this.animationSpeed = {};
    this.controllerTargetRotation = new THREE.Euler(0, 0, 0, "YXZ");
    this.controllerRotationSpeed = 0.15;
  }

  setOrientation(pitch = 0, yaw = 0, roll = 0) {
    if (!this.controller) {
      return;
    }

    this.controllerTargetRotation.set(pitch, yaw, roll, "YXZ");
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
          this.originalRotations[name] = part.rotation.clone();
          this.targets[name] = {
            position: part.position.clone(),
            rotation: part.rotation.clone(),
          };
          this.animationSpeed[name] = 0.25;
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

        this.camera.position.set(0, maxDimension * -0.5, distance * 1.0);
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

  setPositionOffset(name, offset = {}) {
    const originalPosition = this.originalPositions[name];
    const target = this.targets[name];

    if (!originalPosition || !target) {
      console.warn(`Animationsziel fehlt: ${name}`);
      return;
    }

    target.position.copy(originalPosition);

    target.position.x += offset.x ?? 0;
    target.position.y += offset.y ?? 0;
    target.position.z += offset.z ?? 0;
  }

  setRotationOffset(name, offset = {}) {
    const originalRotation = this.originalRotations[name];
    const target = this.targets[name];

    if (!originalRotation || !target) {
      console.warn(`Rotationsziel fehlt: ${name}`);
      return;
    }

    target.rotation.copy(originalRotation);

    target.rotation.x += offset.x ?? 0;
    target.rotation.y += offset.y ?? 0;
    target.rotation.z += offset.z ?? 0;
  }

  setStickTilt(name, x = 0, y = 0) {
    const originalRotation = this.originalRotations[name];
    const target = this.targets[name];

    if (!originalRotation || !target) {
      return;
    }

    const maximumTilt = 0.32;

    target.rotation.copy(originalRotation);

    /*
     * Vor/zurück wird über die lokale X-Achse gekippt.
     * Links/rechts wird über die lokale Z-Achse gekippt.
     */
    target.rotation.x += y * maximumTilt;
    target.rotation.z -= x * maximumTilt;
  }

  setButtonPressed(name, pressed) {
    this.setPositionOffset(name, {
      z: pressed ? -0.12 : 0,
    });

    this.setRotationOffset(name, {
      x: pressed ? -0.05 : 0,
    });
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
      L3: "LeftStick",
      R3: "RightStick",

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

    if (partName === "L1" || partName === "R1") {
      this.setShoulderPressed(partName, active);
      return;
    }

    if (partName === "L2" || partName === "R2") {
      this.setTriggerPressed(partName, active);
      return;
    }

    this.setButtonPressed(partName, active);
  }

  setShoulderPressed(name, pressed) {
    this.setRotationOffset(name, {
      x: pressed ? -0.18 : 0,
    });
  }

  setAnimationSpeed(name, speed) {
    if (this.animationSpeed[name] === undefined) {
      return;
    }

    this.animationSpeed[name] = speed;

    if (name === "LeftStick" || name === "RightStick") {
      this.animationSpeed[name] = 0.4;
    }
  }

  update() {
    for (const name in this.parts) {
      const part = this.parts[name];
      const target = this.targets[name];
      const speed = this.animationSpeed[name];

      if (!part || !target) {
        continue;
      }

      part.position.lerp(target.position, speed);

      part.rotation.x += (target.rotation.x - part.rotation.x) * speed;

      part.rotation.y += (target.rotation.y - part.rotation.y) * speed;

      part.rotation.z += (target.rotation.z - part.rotation.z) * speed;
    }

    if (this.controller) {
      const speed = this.controllerRotationSpeed;

      this.controller.rotation.x +=
        (this.controllerTargetRotation.x - this.controller.rotation.x) * speed;

      this.controller.rotation.y +=
        (this.controllerTargetRotation.y - this.controller.rotation.y) * speed;

      this.controller.rotation.z +=
        (this.controllerTargetRotation.z - this.controller.rotation.z) * speed;
    }
  }

  setTriggerPressed(name, pressed) {
    this.setRotationOffset(name, {
      x: pressed ? -0.9 : 0,
    });
  }
}
