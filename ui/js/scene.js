import * as THREE from "three";
import { Controller3D } from "./controller3d.js";

export class Scene3D {
  constructor(container) {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x181818);

    this.camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      100,
    );

    this.camera.position.set(0, 2, 6);

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
    });

    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.setSize(container.clientWidth, container.clientHeight);

    container.appendChild(this.renderer.domElement);

    const ambient = new THREE.AmbientLight(0xffffff, 1.5);
    this.scene.add(ambient);

    const dir = new THREE.DirectionalLight(0xffffff, 2);
    dir.position.set(4, 5, 3);
    this.scene.add(dir);

    this.controller = new Controller3D(this.scene, this.camera);
    this.controller.load();

    window.addEventListener("resize", () => this.resize(container));

    this.animate();
  }

  resize(container) {
    this.camera.aspect = container.clientWidth / container.clientHeight;

    this.camera.updateProjectionMatrix();

    this.renderer.setSize(container.clientWidth, container.clientHeight);
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    this.controller.update();

    this.renderer.render(this.scene, this.camera);
  }
}
