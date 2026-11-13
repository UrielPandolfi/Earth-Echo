/* Este archivo se genera desde los modelos Pydantic. No lo edites a mano. */

export interface AssetRecord {
  schema_version: "1.0";
  id: string;
  data_mode: "real" | "demo";
  source_id: string;
  collection_id: string;
  product_version: string | null;
  variable_id: string;
  native_unit: string | null;
  spatial: SpatialSupport;
  observed: InstantSpan | IntervalSpan;
  issued_at: string | null;
  availability: AvailabilityKnown | AvailabilityUnknown;
  ingested_at: string;
  quality: Quality;
  checksum_sha256: string | null;
  byte_size?: number | null;
  original_locator: string;
  science_file_retrieved: boolean;
  provenance: Provenance;
}

export interface AvailabilityKnown {
  status: "known";
  at: string;
}

export interface AvailabilityUnknown {
  status: "unknown";
}

export interface CatalogSourceView {
  id: string;
  name: string;
  url: string;
  variables: string;
  coverage: string;
  cadence: string;
  access: string;
  limits: string;
  verification: string;
  integration_status: "documented" | "credential_required" | "sample_retrieved" | "connected" | "blocked";
}

export interface CatalogValidationReport {
  schema_version: "1.0";
  reference_path: string;
  reference_sha256: string;
  pinned_sha256: string | null;
  reference_integrity: "match" | "mismatch" | "pin_missing";
  specification_integrity: "match" | "mismatch" | "pin_missing";
  image_integrity: "match" | "mismatch" | "pin_missing";
  source_count: number;
  variable_count: number;
  phenomenon_count: number;
  duplicate_ids: string[];
  dangling_references: ReferenceMention[];
  unreferenced_source_ids: string[];
  descriptive_source_notes: DescriptiveNote[];
  capability_counts: StatusCount[];
  recorded_http_checks: RecordedHttpCheck[];
  recorded_http_checks_note: string;
}

export interface CatalogVariable {
  id: string;
  name: string;
  units: string;
  source_ids: string[];
  source_notes: string;
  processing_notes: string;
}

export interface DescriptiveNote {
  variable_id: string;
  remainder: string;
}

export interface ForecastRecord {
  schema_version: "1.0";
  id: string;
  data_mode: "real" | "demo";
  phenomenon_id: string;
  model_id: string;
  model_version: string | null;
  run_id: string | null;
  initialization_time: string;
  issued_at: string;
  valid: IntervalSpan;
  lead_time_hours?: number | null;
  variable_id: string | null;
  measurement: MissingValue | PresentValue;
  probability: ProbabilityAbsent | ProbabilityDefined;
  uncertainty?: Uncertainty | null;
  spatial: SpatialSupport;
  availability: AvailabilityKnown | AvailabilityUnknown;
  ingested_at: string;
  quality: Quality;
  provenance: Provenance;
  validation_reference: string | null;
  capability_status: "specified" | "source_connected" | "historical_ready" | "experimental" | "validated_for_scope";
}

export interface GeoLineString {
  type: "LineString";
  coordinates: number[][];
}

export interface GeoMultiLineString {
  type: "MultiLineString";
  coordinates: number[][][];
}

export interface GeoMultiPoint {
  type: "MultiPoint";
  coordinates: number[][];
}

export interface GeoMultiPolygon {
  type: "MultiPolygon";
  coordinates: number[][][][];
}

export interface GeoPoint {
  type: "Point";
  coordinates: number[];
}

export interface GeoPolygon {
  type: "Polygon";
  coordinates: number[][][];
}

export interface GeographicExtent {
  west: number;
  south: number;
  east: number;
  north: number;
  crosses_antimeridian: boolean;
  crs?: "EPSG:4326";
}

export interface HealthResponse {
  schema_version: "1.0";
  status: "ok";
  service: "earth-echo-api";
  time: string;
  checks: "process"[];
}

export interface InstantSpan {
  kind: "instant";
  start: string;
}

export interface IntervalSpan {
  kind: "interval";
  start: string;
  end: string;
  bounds: "start_inclusive_end_exclusive";
}

export interface MissingValue {
  status: "missing";
  value?: null;
  unit?: null;
}

export interface ObservationRecord {
  schema_version: "1.0";
  id: string;
  data_mode: "real" | "demo";
  asset_id: string;
  variable_id: string;
  phenomenon_id: string | null;
  measurement: MissingValue | PresentValue;
  spatial: SpatialSupport;
  observed: InstantSpan | IntervalSpan;
  issued_at: string | null;
  availability: AvailabilityKnown | AvailabilityUnknown;
  ingested_at: string;
  quality: Quality;
  product_version: string | null;
  provenance: Provenance;
}

export interface PhenomenonList {
  schema_version: "1.0";
  total: number;
  returned: number;
  phenomena: PhenomenonView[];
}

export interface PhenomenonView {
  id: string;
  name: string;
  family: string;
  global_scope: string;
  output_type: string;
  required_inputs: string;
  proposed_method: string;
  horizon: string;
  missing_or_local_data: string;
  validation: string;
  source_ids: string[];
  implementation_priority: string;
  implementation_status: string;
  capability_status: "specified" | "source_connected" | "historical_ready" | "experimental" | "validated_for_scope";
}

export interface PresentValue {
  status: "present";
  value: number;
  unit: string;
}

export interface ProbabilityAbsent {
  state: "absent";
  value?: null;
  definition?: null;
}

export interface ProbabilityDefined {
  state: "defined";
  value: number;
  definition: string;
}

export interface Provenance {
  source_ids: string[];
  asset_ids?: string[];
  collection_id?: string | null;
  product_version?: string | null;
  license_url?: string | null;
  native_unit?: string | null;
  retrieval?: "viability_sample" | "demo_fixture" | "live" | null;
  note?: string | null;
}

export interface ProviderReport {
  schema_version: "1.0";
  checked_at: string;
  live_probe: "not_performed" | "performed";
  note: string;
  providers: ProviderStatus[];
}

export interface ProviderStatus {
  source_id: string;
  name: string;
  integration_status: "documented" | "credential_required" | "sample_retrieved" | "connected" | "blocked";
  sample_kind: string | null;
  live_status: "not_probed" | "reachable" | "unreachable";
  detail: string;
}

export interface Quality {
  flags?: string[];
  summary?: string | null;
}

export interface ReadyResponse {
  schema_version: "1.0";
  process: "ok";
  query_stores: "ready" | "incomplete";
  providers_updated: "not_checked";
  assistant: "unavailable" | "configured";
  stores: StoreCheck[];
  note: string;
}

export interface RecordedHttpCheck {
  source: string;
  url: string;
  status: number;
  byte_count: number;
  json_keys: string[];
  tested: string;
  reexecuted: false;
}

export interface ReferenceMention {
  owner_type: "variable" | "module";
  owner_id: string;
  source_id: string;
}

export interface SignalQueryResult {
  schema_version: "1.0";
  requested_data_mode: "real" | "demo";
  phenomenon_id: string;
  status: "available" | "unavailable";
  signals: SignalRecord[];
  forecasts: ForecastRecord[];
  unavailable: UnavailableResult | null;
}

export interface SignalRecord {
  schema_version: "1.0";
  id: string;
  data_mode: "real" | "demo";
  phenomenon_id: string;
  output_class: "observation" | "diagnosis" | "trend" | "hazard" | "risk" | "nowcast" | "forecast" | "research_signal";
  title: string;
  summary: string;
  variable_id: string | null;
  measurement: MissingValue | PresentValue;
  spatial: SpatialSupport;
  observed: InstantSpan | IntervalSpan | null;
  valid: InstantSpan | IntervalSpan | null;
  issued_at: string | null;
  availability: AvailabilityKnown | AvailabilityUnknown;
  ingested_at: string;
  quality: Quality;
  provenance: Provenance;
  capability_status: "specified" | "source_connected" | "historical_ready" | "experimental" | "validated_for_scope";
  probability: ProbabilityAbsent | ProbabilityDefined;
}

export interface SourceList {
  schema_version: "1.0";
  total: number;
  returned: number;
  sources: CatalogSourceView[];
}

export interface SpatialSupport {
  role: "observation_location" | "grid_cell" | "gridded_product" | "area" | "track" | "region_anchor";
  region_id?: string | null;
  grid_id?: string | null;
  extent?: GeographicExtent | null;
  geometry?: GeoPoint | GeoMultiPoint | GeoLineString | GeoMultiLineString | GeoPolygon | GeoMultiPolygon | null;
  vertical?: VerticalPosition | null;
  resolution_note?: string | null;
}

export interface StatusCount {
  status: string;
  count: number;
}

export interface StoreCheck {
  name: string;
  path: string;
  present: boolean;
}

export interface UnavailableResult {
  schema_version: "1.0";
  status: "unavailable";
  requested_data_mode: "real" | "demo";
  reason_code: "insufficient_data" | "source_unreachable" | "not_implemented" | "credential_required" | "outside_coverage" | "quality_rejected" | "no_demo_fixture";
  reason: string;
  phenomenon_id: string | null;
  variable_id: string | null;
  source_ids: string[];
  as_of: string;
}

export interface Uncertainty {
  description: string;
  low?: number | null;
  high?: number | null;
  unit?: string | null;
}

export interface VariableList {
  schema_version: "1.0";
  total: number;
  returned: number;
  variables: CatalogVariable[];
}

export interface VerticalPosition {
  value: number;
  unit: string;
  datum: string;
  direction: "down" | "up";
}

export interface ContractBundle {
  health: HealthResponse;
  ready: ReadyResponse;
  providers: ProviderReport;
  sources: SourceList;
  phenomena: PhenomenonList;
  variables: VariableList;
  validation: CatalogValidationReport;
  observation: ObservationRecord;
  asset: AssetRecord;
  signal_query: SignalQueryResult;
  forecast: ForecastRecord;
}
