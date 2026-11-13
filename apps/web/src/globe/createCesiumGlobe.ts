import {
  Cartesian2,
  Cartesian3,
  Credit,
  EllipsoidalOccluder,
  EllipsoidTerrainProvider,
  ImageryLayer,
  Math as CesiumMath,
  SceneTransforms,
  TileMapServiceImageryProvider,
  UrlTemplateImageryProvider,
  Viewer,
  buildModuleUrl,
} from "cesium";
import {
  americasPreset,
  cameraLimits,
  lightingMode,
  facingCamera,
  frameExtent,
  isClick,
  placeMarkers,
  technicalMarkers,
  type GeoExtent,
  type PlacedMarker,
} from "./geography";
import type { GlobeHandle } from "./lifecycle";

export type GlobeStatus =
  | { state: "loading"; detail: string }
  | { state: "ready"; detail: string }
  | { state: "fallback"; detail: string }
  | { state: "error"; detail: string };

const GIBS_BLUE_MARBLE =
  "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg";

export function createCesiumGlobe(container: HTMLElement): GlobeHandle {
  if (!hasWebGl()) {
    throw new Error("WebGL no está disponible. El resto de la pantalla sigue usable.");
  }

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
    skyBox: undefined,
    terrainProvider: new EllipsoidTerrainProvider(),
    baseLayer: ImageryLayer.fromProviderAsync(
      TileMapServiceImageryProvider.fromUrl(buildModuleUrl("Assets/Textures/NaturalEarthII"), {
        credit: "Natural Earth II",
      }),
    ),
    requestRenderMode: true,
    maximumRenderTimeChange: Number.POSITIVE_INFINITY,
  });

  const removals: Array<() => void> = [];
  let destroyed = false;
  let gibsFailed = false;
  let overlayListener: ((markers: PlacedMarker[]) => void) | null = null;
  let statusListener: ((status: GlobeStatus) => void) | null = null;
  let selectionListener: ((selection: string | null) => void) | null = null;
  let latestStatus: GlobeStatus = {
    state: "loading",
    detail: "Cargando la base geográfica.",
  };
  const markers = new Map(technicalMarkers.map((marker) => [marker.id, { ...marker }]));

  const publish = (status: GlobeStatus) => {
    latestStatus = status;
    statusListener?.(status);
  };

  const scene = viewer.scene;
  const globe = scene.globe;
  const camera = viewer.camera;
  const controller = scene.screenSpaceCameraController;
  globe.showGroundAtmosphere = true;
  globe.atmosphereLightIntensity = 7;
  globe.enableLighting = lightingMode !== "presentation";
  globe.depthTestAgainstTerrain = false;
  scene.fog.enabled = false;
  if (scene.sun) {
    scene.sun.show = false;
  }
  if (scene.moon) {
    scene.moon.show = false;
  }
  if (scene.skyAtmosphere) {
    scene.skyAtmosphere.show = true;
    scene.skyAtmosphere.brightnessShift = -0.25;
    scene.skyAtmosphere.saturationShift = -0.1;
  }
  controller.minimumZoomDistance = cameraLimits.minimumHeightMeters;
  controller.maximumZoomDistance = cameraLimits.maximumHeightMeters;
  controller.enableCollisionDetection = true;
  controller.maximumTiltAngle = Math.PI / 2;
  controller.inertiaSpin = 0.55;
  controller.inertiaZoom = 0.35;
  viewer.clock.shouldAnimate = false;
  camera.percentageChanged = 0.01;

  const gibs = new UrlTemplateImageryProvider({
    url: GIBS_BLUE_MARBLE,
    credit: new Credit("NASA GIBS · Blue Marble Shaded Relief and Bathymetry", true),
    maximumLevel: 8,
    hasAlphaChannel: false,
  });
  const gibsLayer = viewer.imageryLayers.addImageryProvider(gibs);
  gibsLayer.saturation = 0.88;
  gibsLayer.brightness = 1.02;
  gibsLayer.contrast = 1.04;
  const onGibsError = () => {
    if (gibsFailed || destroyed) {
      return;
    }
    gibsFailed = true;
    viewer.imageryLayers.remove(gibsLayer, false);
    publish({
      state: "fallback",
      detail: "NASA GIBS no entregó teselas. Se muestra Natural Earth II, incluido en CesiumJS.",
    });
    scene.requestRender();
  };
  gibs.errorEvent.addEventListener(onGibsError);
  removals.push(() => gibs.errorEvent.removeEventListener(onGibsError));

  let sawTileWork = false;
  const onTiles = (remaining: number) => {
    if (remaining > 0) {
      sawTileWork = true;
      return;
    }
    if (!sawTileWork || gibsFailed) {
      return;
    }
    publish({
      state: "ready",
      detail: "Base visual: NASA GIBS, Blue Marble. Iluminación de presentación, no astronómica.",
    });
  };
  globe.tileLoadProgressEvent.addEventListener(onTiles);
  removals.push(() => globe.tileLoadProgressEvent.removeEventListener(onTiles));

  const occluder = new EllipsoidalOccluder(globe.ellipsoid, camera.positionWC);
  const scratch = new Cartesian3();
  const windowPosition = new Cartesian2();

  const publishOverlays = () => {
    if (destroyed) {
      return;
    }
    occluder.cameraPosition = camera.positionWC;
    const width = container.clientWidth;
    const height = container.clientHeight;
    const projected = [...markers.values()].map((marker) => {
      const position = Cartesian3.fromDegrees(marker.longitude, marker.latitude, 0, globe.ellipsoid, scratch);
      const visibleToCamera = occluder.isPointVisible(position);
      const screen = SceneTransforms.worldToWindowCoordinates(scene, position, windowPosition);
      return {
        id: marker.id,
        title: marker.title,
        x: screen?.x ?? -1,
        y: screen?.y ?? -1,
        facing: visibleToCamera && facingCamera(
          CesiumMath.toDegrees(camera.positionCartographic.longitude),
          CesiumMath.toDegrees(camera.positionCartographic.latitude),
          marker.longitude,
          marker.latitude,
        ),
        priority: marker.priority,
      };
    });
    overlayListener?.(placeMarkers(projected, width, height));
  };

  const onFrame = () => publishOverlays();
  scene.preRender.addEventListener(onFrame);
  removals.push(() => scene.preRender.removeEventListener(onFrame));

  const motionDuration = () =>
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ? 0 : 1.15;

  const flyToView = (longitude: number, latitude: number, heightMeters: number) => {
    if (destroyed || viewer.isDestroyed()) {
      return;
    }
    camera.cancelFlight();
    camera.flyTo({
      destination: Cartesian3.fromDegrees(longitude, latitude, heightMeters, globe.ellipsoid),
      duration: motionDuration(),
      pitchAdjustHeight: 1_000_000,
    });
  };

  const restoreView = () => {
    flyToView(americasPreset.longitude, americasPreset.latitude, americasPreset.heightMeters);
  };

  const canvas = scene.canvas;
  const interrupt = () => {
    if (!destroyed) {
      camera.cancelFlight();
    }
  };
  let pointerStart: { x: number; y: number } | null = null;
  const onPointerDown = (event: PointerEvent) => {
    pointerStart = { x: event.clientX, y: event.clientY };
    interrupt();
  };
  const onPointerUp = (event: PointerEvent) => {
    if (!pointerStart) {
      return;
    }
    const dx = event.clientX - pointerStart.x;
    const dy = event.clientY - pointerStart.y;
    pointerStart = null;
    if (!isClick(dx, dy)) {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const hit = [...markers.values()]
      .map((marker) => {
        const position = Cartesian3.fromDegrees(marker.longitude, marker.latitude, 0, globe.ellipsoid);
        if (!occluder.isPointVisible(position)) {
          return null;
        }
        const screen = SceneTransforms.worldToWindowCoordinates(scene, position);
        if (!screen) {
          return null;
        }
        const distance = Math.hypot(screen.x - x, screen.y - y);
        return distance <= 22 ? { id: marker.id, note: marker.note, distance } : null;
      })
      .filter((item): item is { id: string; note: string; distance: number } => item !== null)
      .sort((a, b) => a.distance - b.distance)[0];
    selectionListener?.(
      hit ? `${hit.id}. ${hit.note}` : null,
    );
  };
  canvas.addEventListener("pointerdown", onPointerDown);
  canvas.addEventListener("pointerup", onPointerUp);
  canvas.addEventListener("wheel", interrupt, { passive: true });
  const onContextLost = (event: Event) => {
    event.preventDefault();
    publish({
      state: "error",
      detail: "Se perdió el contexto WebGL. Recargá la página para recuperar el globo.",
    });
  };
  canvas.addEventListener("webglcontextlost", onContextLost);
  removals.push(() => {
    canvas.removeEventListener("pointerdown", onPointerDown);
    canvas.removeEventListener("pointerup", onPointerUp);
    canvas.removeEventListener("wheel", interrupt);
    canvas.removeEventListener("webglcontextlost", onContextLost);
  });

  restoreView();
  scene.requestRender();

  const zoomBy = (direction: 1 | -1) => {
    if (destroyed || viewer.isDestroyed()) {
      return;
    }
    interrupt();
    const distance = camera.positionCartographic.height * 0.35;
    if (direction > 0) {
      camera.zoomIn(distance);
    } else {
      camera.zoomOut(distance);
    }
    scene.requestRender();
  };

  return {
    destroy() {
      if (destroyed) {
        return;
      }
      destroyed = true;
      for (const remove of removals) {
        remove();
      }
      if (!viewer.isDestroyed()) {
        viewer.destroy();
      }
    },
    zoomIn: () => zoomBy(1),
    zoomOut: () => zoomBy(-1),
    resize() {
      if (!destroyed && !viewer.isDestroyed()) {
        viewer.resize();
        publishOverlays();
        scene.requestRender();
      }
    },
    restoreView,
    focusRegion(extent: GeoExtent) {
      const framed = frameExtent(extent);
      if (framed.status === "framed") {
        flyToView(framed.view.longitude, framed.view.latitude, framed.view.heightMeters);
      }
      return framed;
    },
    addSignal(signal) {
      markers.set(signal.id, signal);
      scene.requestRender();
    },
    updateSignal(id, signal) {
      const current = markers.get(id);
      if (!current) {
        return;
      }
      markers.set(id, { ...current, ...signal, id });
      scene.requestRender();
    },
    removeSignal(id) {
      markers.delete(id);
      scene.requestRender();
    },
    setOverlayListener(listener) {
      overlayListener = listener;
      publishOverlays();
    },
    setStatusListener(listener) {
      statusListener = listener;
      listener?.(latestStatus);
    },
    setSelectionListener(listener) {
      selectionListener = listener;
    },
    selectMarker(id) {
      const marker = id ? markers.get(id) : undefined;
      selectionListener?.(marker ? `${marker.id}. ${marker.note}` : null);
    },
  };
}

function hasWebGl(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}
