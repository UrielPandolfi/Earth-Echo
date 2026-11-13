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
  viewer.camera.setView({
    destination: Cartesian3.fromDegrees(-60, -15, 18_000_000),
  });
  viewer.scene.requestRender();
  return {
    destroy() {
      if (!viewer.isDestroyed()) {
        viewer.destroy();
      }
    },
  };
}
