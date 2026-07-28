import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

export class Controller3D {
  constructor(scene) {
    this.scene = scene;
    this.loader = new GLTFLoader();
    this.controller = null;
  }

  async load() {
    return new Promise((resolve, reject) => {
      this.loader.load(
        "../assets/plaiiboyv3.glb",

        (gltf) => {
          this.controller = gltf.scene;

          this.controller.scale.set(1, 1, 1);
          this.controller.position.set(0, 0, 0);

          this.scene.add(this.controller);

          resolve(this.controller);
        },

        undefined,

        reject,
      );
    });
  }
}
