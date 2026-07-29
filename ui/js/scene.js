import * as THREE from "three";
import { EXRLoader } from "three/addons/loaders/EXRLoader.js";
import { Controller3D } from "./controller3d.js";

export class Scene3D {
  constructor(container) {
    this.scene = new THREE.Scene();

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
     * Farb- und Helligkeitsdarstellung.
     */
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;

    this.renderer.toneMappingExposure = 1.0;

    /*
     * Schatten bleiben aktiviert.
     * Ohne zusätzliche Lampe entstehen dadurch momentan
     * allerdings keine klassischen gerichteten Schlagschatten.
     */
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFShadowMap;

    container.appendChild(this.renderer.domElement);

    /*
     * Blender-EXR als sichtbarer Hintergrund
     * und als Beleuchtung für das Modell.
     */
    const exrLoader = new EXRLoader();

    exrLoader.load(
      "./assets/sunrise.exr",

      (texture) => {
        texture.mapping = THREE.EquirectangularReflectionMapping;

        this.scene.environment = texture;
        this.scene.background = texture;

        /*
         * Blender-Viewport-Rotation:
         * 49,4 Grad.
         *
         * Falls die Lichtseite spiegelverkehrt wirkt,
         * hier -49.4 durch 49.4 ersetzen.
         */
        const environmentRotation = THREE.MathUtils.degToRad(-20.4);

        this.scene.environmentRotation.set(0, environmentRotation, 0);

        this.scene.backgroundRotation.set(0, environmentRotation, 0);

        /*
         * Stärke der EXR-Beleuchtung auf dem Controller.
         */
        this.scene.environmentIntensity = 1.0;

        /*
         * Helligkeit des sichtbaren Hintergrunds.
         * Etwas niedriger als das Licht, damit er nicht blendet.
         */
        this.scene.backgroundIntensity = 0.9;

        /*
         * Leichte Unschärfe.
         * Kleinerer Wert = schärferer Hintergrund.
         */
        this.scene.backgroundBlurriness = 0.0;

        console.log("EXR-Umgebung geladen.");
      },

      undefined,

      (error) => {
        console.error("EXR konnte nicht geladen werden:", error);
      },
    );

    /*
     * Controller laden.
     */
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
