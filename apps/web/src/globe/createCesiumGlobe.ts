import {
  Cartesian3,
  EllipsoidTerrainProvider,
  ImageryLayer,
  TileMapServiceImageryProvider,
  Viewer,
  buildModuleUrl,
} from "cesium";
import type { GlobeHandle } from "./lifecycle";

export function createCesiumGlobe(container: HTMLElement): GlobeHandle {
  const viewer = new Viewer(container, {
    animation: false,
    timeline: false,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    infoBox: false,
    selectionIndicator: false,
    fullscreenButton: false,
    terrainProvider: new EllipsoidTerrainProvider(),
    baseLayer: ImageryLayer.fromProviderAsync(
      TileMapServiceImageryProvider.fromUrl(buildModuleUrl("Assets/Textures/NaturalEarthII"), {
        credit: "Natural Earth",
      }),
    ),
    requestRenderMode: true,
  });
  const frameAmericas = () => {
    viewer.camera.setView({
      destination: Cartesian3.fromDegrees(-72, 8, 12_500_000),
    });
    viewer.scene.requestRender();
  };
  frameAmericas();
  const zoom = (direction: 1 | -1) => {
    if (viewer.isDestroyed()) {
      return;
    }
    const distance = viewer.camera.positionCartographic.height * 0.35;
    if (direction > 0) {
      viewer.camera.zoomIn(distance);
    } else {
      viewer.camera.zoomOut(distance);
    }
    viewer.scene.requestRender();
  };
  return {
    destroy() {
      if (!viewer.isDestroyed()) {
        viewer.destroy();
      }
    },
    zoomIn: () => zoom(1),
    zoomOut: () => zoom(-1),
    resize() {
      if (!viewer.isDestroyed()) {
        viewer.resize();
        viewer.scene.requestRender();
      }
    },
  };
}
