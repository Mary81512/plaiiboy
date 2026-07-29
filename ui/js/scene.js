import * as THREE from "three";
import { Controller3D } from "./controller3d.js";

export class Scene3D {
  constructor(container) {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xe9edf3);

    this.camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      100,
    );

    this.camera.position.set(0, 0, 6);
    this.camera.lookAt(0, 0, 0);

    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
    });

    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

    this.renderer.setSize(container.clientWidth, container.clientHeight);

    /*
     * Realistischere Helligkeits- und Farbdarstellung.
     */
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;

    /*
     * Schatten aktivieren.
     */
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    container.appendChild(this.renderer.domElement);

    /*
     * Weiches Grundlicht:
     * hellt die dunklen Bereiche auf, ohne alles flach zu machen.
     */
    const hemisphereLight = new THREE.HemisphereLight(0xffffff, 0x667080, 1.65);

    hemisphereLight.position.set(0, 5, 0);
    this.scene.add(hemisphereLight);

    /*
     * Hauptlicht von links oben.
     */
    const keyLight = new THREE.DirectionalLight(0xffffff, 4.2);

    keyLight.position.set(-4, 6, 5);
    keyLight.castShadow = true;

    keyLight.shadow.mapSize.set(2048, 2048);
    keyLight.shadow.bias = -0.0005;
    keyLight.shadow.normalBias = 0.025;

    keyLight.shadow.camera.near = 0.1;
    keyLight.shadow.camera.far = 30;
    keyLight.shadow.camera.left = -8;
    keyLight.shadow.camera.right = 8;
    keyLight.shadow.camera.top = 8;
    keyLight.shadow.camera.bottom = -8;

    this.scene.add(keyLight);

    /*
     * Schwächeres Licht von rechts.
     * Dadurch bleiben die rechten Griffe und Buttons sichtbar.
     */
    const fillLight = new THREE.DirectionalLight(0xcddcff, 1.8);

    fillLight.position.set(5, 2, 4);
    this.scene.add(fillLight);

    /*
     * Lichtkante von hinten/oben.
     * Hebt die Außenkontur vom Hintergrund ab.
     */
    const rimLight = new THREE.DirectionalLight(0xffffff, 2.2);

    rimLight.position.set(0, 5, -5);
    this.scene.add(rimLight);

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
