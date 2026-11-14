import {
  BillboardCollection,
  Cartesian2,
  Cartesian3,
  Color,
  Credit,
  EllipsoidalOccluder,
  EllipsoidTerrainProvider,
  ImageryLayer,
  Material,
  PolylineCollection,
  PolygonHierarchy,
  Entity,
  Math as CesiumMath,
  Rectangle,
  SceneTransforms,
  SingleTileImageryProvider,
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
  type GeoExtent,
  type PlacedMarker,
} from "./geography";
import type { GlobeHandle, GlobeMarker } from "./lifecycle";
import { visibleSymbols } from './screen-symbols';
import type { FieldGrid } from "../demo/explore";

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
  const markers = new Map<string, GlobeMarker>();
  let selectedId: string | null = null;
  let fieldLayer: ImageryLayer | null = null;
  let cameraListener: ((heightMeters: number) => void) | null = null;
  const symbolImages = {
    observation: paintShape("circle"),
    risk: paintShape("triangle"),
    forecast: paintShape("diamond"),
  };
  const clusterImages = new Map<number, HTMLCanvasElement>();

  const publish = (status: GlobeStatus) => {
    latestStatus = status;
    statusListener?.(status);
  };

  const scene = viewer.scene;
  const billboards = new BillboardCollection({ scene });
  scene.primitives.add(billboards);
  const paths = new PolylineCollection();
  scene.primitives.add(paths);
  const regionEntities: Entity[]=[];
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
        width: marker.symbol==='cluster' ? 48 : 12,
        height: marker.symbol==='cluster' ? 32 : 12,
      };
    });
    const visible=visibleSymbols(projected,width,height,selectedId);
    for(let index=0;index<billboards.length;index++){
      const billboard=billboards.get(index);
      billboard.show=visible.has(String(billboard.id));
    }
    overlayListener?.(placeMarkers(projected.filter(p=>p.id===selectedId), width, height));
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
    const picked = scene.pick(new Cartesian2(x, y)) as { id?: unknown } | undefined;
    const id = typeof picked?.id === "string" ? picked.id : picked?.id instanceof Entity ? picked.id.id : null;
    if (!id) {
      return;
    }
    if (id.startsWith("cluster:")) {
      const cluster = markers.get(id);
      if (cluster) {
        const framed = frameExtent({
          west: ((cluster.longitude - 3 + 540) % 360) - 180,
          south: Math.max(-90, cluster.latitude - 3),
          east: ((cluster.longitude + 3 + 540) % 360) - 180,
          north: Math.min(90, cluster.latitude + 3),
          crossesAntimeridian: cluster.longitude - 3 < -180 || cluster.longitude + 3 > 180,
        });
        if (framed.status === "framed") {
          flyToView(framed.view.longitude, framed.view.latitude, framed.view.heightMeters);
        }
      }
      return;
    }
    selectedId = id;
    selectionListener?.(id);
    publishOverlays();
    scene.requestRender();
  };
  camera.percentageChanged = 0.05;
  const onCamera = () => cameraListener?.(camera.positionCartographic.height);
  camera.changed.addEventListener(onCamera);
  removals.push(() => camera.changed.removeEventListener(onCamera));

  const drawSignals = (signals: GlobeMarker[]) => {
    markers.clear();
    billboards.removeAll();
    for (const signal of signals) {
      markers.set(signal.id, signal);
      const cluster = signal.symbol === "cluster";
      billboards.add({
        position: Cartesian3.fromDegrees(signal.longitude, signal.latitude, 0, globe.ellipsoid),
        image: cluster ? clusterCanvas(clusterImages, signal.count ?? 0) : symbolImages[signal.symbol === "risk" || signal.symbol === "forecast" ? signal.symbol : "observation"],
        color: cluster ? Color.WHITE : Color.fromCssColorString(symbolColor(signal.symbol)),
        id: signal.id,
        disableDepthTestDistance: 0,
        scale: cluster ? 1 : 0.8,
      });
    }
    publishOverlays();
    scene.requestRender();
  };

  const paintField = (field: FieldGrid | null, credit: string) => {
    if (fieldLayer) {
      viewer.imageryLayers.remove(fieldLayer, true);
      fieldLayer = null;
    }
    if (!field) {
      scene.requestRender();
      return;
    }
    const canvasField = document.createElement("canvas");
    canvasField.width = field.width;
    canvasField.height = field.height;
    const context = canvasField.getContext("2d");
    if (!context) {
      return;
    }
    context.putImageData(new ImageData(new Uint8ClampedArray(field.rgba), field.width, field.height), 0, 0);
    try {
      const provider = new SingleTileImageryProvider({
        url: canvasField.toDataURL("image/png"),
        tileWidth: field.width,
        tileHeight: field.height,
        rectangle: Rectangle.fromDegrees(field.west, field.south, field.east, field.north),
        credit,
      });
      fieldLayer = viewer.imageryLayers.addImageryProvider(provider);
      fieldLayer.alpha = 0.62;
    } catch {
      publish({
        state: "error",
        detail: "No se pudo dibujar la capa ilustrativa. El globo y las señales siguen disponibles.",
      });
    }
    scene.requestRender();
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
      drawSignals([...markers.values(), signal]);
    },
    updateSignal(id, signal) {
      const current = markers.get(id);
      if (!current) {
        return;
      }
      drawSignals([...markers.values()].map((item) => (item.id === id ? { ...current, ...signal, id } : item)));
    },
    removeSignal(id) {
      drawSignals([...markers.values()].filter((item) => item.id !== id));
    },
    setSignals(signals) {
      drawSignals(signals);
    },
    setField(field, credit) {
      paintField(field, credit ?? "Campo ilustrativo DEMO");
    },
    setTracks(tracks) {
      paths.removeAll();
      for (const track of tracks) {
        for (const part of track.geometry.coordinates) {
          paths.add({positions: part.map(p=>Cartesian3.fromDegrees(p[0],p[1],2000)),width:3,
            material:Material.fromType('Color',{color:Color.fromCssColorString('#e7bf74')}),
            id:`product-point:${track.sample_ids[track.sample_ids.length-1]}`});
        }
      }
      scene.requestRender();
    },
    setRegions(regions) {
      for (const entity of regionEntities) viewer.entities.remove(entity);
      regionEntities.length=0;
      for (const region of regions) {
        region.geometry.coordinates.forEach((rings,index)=>{
          const ring=(positions:number[][])=>positions.map(p=>Cartesian3.fromDegrees(p[0],p[1]));
          regionEntities.push(viewer.entities.add({id:`product-point:${region.sample_id}:area:${region.id}:${index}`,
            polygon:{hierarchy:new PolygonHierarchy(ring(rings[0]),rings.slice(1).map(h=>new PolygonHierarchy(ring(h)))),
              material:Color.fromCssColorString('#e7bf74').withAlpha(.23),outline:true,outlineColor:Color.fromCssColorString('#e7bf74'),height:1000}}));
        });
      }
      scene.requestRender();
    },
    setCameraListener(listener) {
      cameraListener = listener;
      listener?.(camera.positionCartographic.height);
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
      selectedId = id;
      selectionListener?.(id);
      publishOverlays();
      scene.requestRender();
    },
  };
}

function symbolColor(symbol: GlobeMarker["symbol"]): string {
  if (symbol === 'context') return '#acb5c3';
  if (symbol === "risk") {
    return "#e07a62";
  }
  if (symbol === "forecast") {
    return "#7eb6e0";
  }
  return "#3ee0cf";
}

function paintShape(kind: "circle" | "triangle" | "diamond"): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = 32;
  canvas.height = 32;
  const context = canvas.getContext("2d");
  if (!context) {
    return canvas;
  }
  context.translate(16, 16);
  context.fillStyle = "#ffffff";
  context.beginPath();
  if (kind === "triangle") {
    context.moveTo(0, -9);
    context.lineTo(8, 7);
    context.lineTo(-8, 7);
  } else if (kind === "diamond") {
    context.moveTo(0, -9);
    context.lineTo(7, 0);
    context.lineTo(0, 9);
    context.lineTo(-7, 0);
  } else {
    context.arc(0, 0, 7, 0, Math.PI * 2);
  }
  context.closePath();
  context.fill();
  return canvas;
}

function clusterCanvas(cache: Map<number, HTMLCanvasElement>, count: number): HTMLCanvasElement {
  const cached = cache.get(count);
  if (cached) {
    return cached;
  }
  const canvas = document.createElement("canvas");
  canvas.width = 48;
  canvas.height = 32;
  const context = canvas.getContext("2d");
  if (!context) {
    return canvas;
  }
  context.fillStyle = "#101826";
  context.strokeStyle = "#3ee0cf";
  context.lineWidth = 2;
  context.beginPath();
  context.roundRect(1, 1, 46, 30, 8);
  context.fill();
  context.stroke();
  context.fillStyle = "#e8eef3";
  context.font = "700 14px sans-serif";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(count > 99 ? "99+" : String(count), 24, 16);
  cache.set(count, canvas);
  return canvas;
}

function hasWebGl(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"));
  } catch {
    return false;
  }
}
