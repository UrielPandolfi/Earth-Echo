/* Este archivo se genera desde los modelos Pydantic. No lo edites a mano. */

export interface AftershockBin {
  magnitude: number;
  probability: number;
  median_count?: number | null;
  p95_minimum?: number | null;
  p95_maximum?: number | null;
}

export interface AftershockEvent {
  event_id: string;
  magnitude?: number | null;
  latitude?: number | null;
  longitude?: number | null;
  depth_km?: null;
  origin_time?: null;
  model_name: string;
  region_type?: string | null;
  region_radius?: number | null;
  region_radius_unit?: null;
  geometry?: "epicenter_only";
  geometry_note: string;
  issued_at: string;
  product_version: string;
  retrieved_at: string;
  checksum_sha256: string;
  original_url: string;
  windows: AftershockWindow[];
}

export interface AftershockForecasts {
  data_mode?: "real";
  status: "available" | "no_coverage" | "missing_input" | "expired" | "not_implemented";
  reason?: string | null;
  events: AftershockEvent[];
  limitation: string;
  update?: RefreshJob | null;
  update_pending?: boolean;
}

export interface AftershockWindow {
  label: string;
  valid_from: string;
  valid_to: string;
  temporal_state: "future" | "in_progress" | "expired" | "unknown";
  bins: AftershockBin[];
}

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

export interface AssistantAction {
  type: "open-section";
  section: "explorar" | "tendencias" | "historico";
}

export interface AssistantContext {
  data_mode: "real" | "demo";
  replay_issue?: string | null;
  replay_revealed?: boolean;
}

export interface AssistantReply {
  schema_version: "1.0";
  provider: "unavailable" | "not_used" | "mock" | "openai-compatible";
  model: string | null;
  answer_kind: "tool_template" | "model_paraphrase";
  text: string;
  tools: Array<Record<string, unknown>>;
  documents: RetrievedDocument[];
  actions: AssistantAction[];
  limitations: string[];
  asked_at: string;
}

export interface AssistantRequest {
  question: string;
  context: AssistantContext;
}

export interface AssociationPairView {
  id: string;
  title: string;
  status: "evaluated" | "not_evaluable";
  reason: string | null;
  x_name: string;
  y_name: string;
  x_unit: string;
  y_unit: string;
  x_scope: string;
  y_scope: string;
  n_pairs: number;
  missing_pairs: number;
  raw_r: number | null;
  residual_r: number | null;
  slope_x_per_year: number | null;
  slope_y_per_year: number | null;
  intervals: BlockInterval[];
  points: AssociationPoint[];
  inputs: CalculationInput[];
  warnings: string[];
}

export interface AssociationPoint {
  year: number;
  quarter: number;
  start: string;
  end: string;
  x: number | null;
  y: number | null;
  residual_x: number | null;
  residual_y: number | null;
}

export interface AssociationView {
  data_mode?: "real";
  status: "evaluated" | "not_evaluable" | "unavailable";
  reason?: string | null;
  method_version: string;
  execution_id: string;
  computed_at: string | null;
  causal_attribution?: "not_identified";
  predictive_validation?: "not_a_forecast";
  parameters: Record<string, number>;
  references: string[];
  stale_inputs?: string[];
  verification: string;
  pairs: AssociationPairView[];
}

export interface AvailabilityKnown {
  status: "known";
  at: string;
}

export interface AvailabilityUnknown {
  status: "unknown";
}

export interface BlockInterval {
  block_quarters: number;
  low: number | null;
  high: number | null;
  valid_draws: number;
  draws: number;
}

export interface CalculationInput {
  product_id: string;
  variable: string;
  unit: string;
  checksum_sha256: string;
}

export interface CalculationResult {
  label: string;
  value: number;
  unit: string;
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

export interface EnsoObservation {
  season_id: string;
  valid_from: string;
  valid_to: string;
  roni_c: number;
  season_phase: "La Niña" | "Neutral" | "El Niño";
  note: string;
}

export interface EnsoOutlook {
  data_mode?: "real";
  status: "available" | "no_coverage" | "missing_input" | "expired" | "not_implemented";
  reason?: string | null;
  edition?: string | null;
  issued_at?: null;
  issue_time_basis: string;
  retrieved_at?: string | null;
  ingested_at?: string | null;
  source_url: string;
  discussion_url: string;
  checksum_sha256?: string | null;
  phases: EnsoPhase[];
  observation?: EnsoObservation | null;
  region: ProductRegion;
  meaning: string;
  limitation: string;
  update?: RefreshJob | null;
  update_pending?: boolean;
}

export interface EnsoPhase {
  season: string;
  order: number;
  valid_from: string;
  valid_to: string;
  temporal_state: "future" | "in_progress" | "expired" | "unknown";
  la_nina_percent: number;
  neutral_percent: number;
  el_nino_percent: number;
  roni_p50_c?: number | null;
}

export interface ForecastCatalog {
  data_mode?: "real";
  as_of: string;
  forecasts: ForecastDescriptor[];
  default_d16_id: string | null;
  future_fields: number;
  current_fields: number;
  archived_fields: number;
  own_experiments: number;
  note: string;
}

export interface ForecastCell {
  id: string;
  row: number;
  column: number;
  longitude: number;
  latitude: number;
  extent: GeographicExtent;
  geometry: GeoMultiPolygon;
  support_note: string;
}

export interface ForecastDescriptor {
  id: string;
  product_id: string;
  source_id: string;
  phenomenon_id?: string | null;
  title: string;
  provider: string;
  result_type: "imported_probability" | "imported_value" | "derived_indicator" | "own_experiment";
  spatial_support: "field" | "published_region" | "regional_series" | "planetary" | "table";
  queryable: boolean;
  availability: "available" | "missing_input" | "not_implemented";
  temporal_state: "future" | "in_progress" | "expired" | "unknown";
  variable: string;
  unit: string;
  native_unit: string;
  event_definition: string;
  scientific_threshold?: string | null;
  reference_period?: string | null;
  trend_treatment?: string | null;
  method: string;
  adapter_version: string;
  provider_version: string;
  identity_basis: string;
  initialized_at?: string | null;
  issued_at?: string | null;
  retrieved_at: string;
  processed_at: string;
  first_seen_at: string;
  first_seen_basis: string;
  valid_from?: string | null;
  valid_to?: string | null;
  temporal_semantics: "monthly_interval" | "instant" | "accumulation_interval" | "published_interval" | "three_hour_windows" | "unknown";
  coverage: string;
  resolution?: string | null;
  quality_mask?: string | null;
  sampling?: string | null;
  calculation?: ScientificCalculation | null;
  original_url: string;
  original_sha256: string;
  original_download: string;
  metadata_download: string;
  reference_url: string;
  limitation: string;
  experimental: boolean;
  validated_for_use?: false;
  skill?: null;
  skill_note?: string;
  update?: RefreshJob | null;
  update_pending: boolean;
}

export interface ForecastField {
  status: "available" | "no_coverage" | "missing_input" | "expired" | "not_implemented";
  reason?: string | null;
  forecast?: ForecastDescriptor | null;
  grid?: ScientificGrid | null;
}

export interface ForecastHighlight {
  id: string;
  cell_count: number;
  probability_min: number;
  probability_max: number;
  representative: ForecastPoint;
}

export interface ForecastHighlights {
  status: "available" | "no_coverage" | "missing_input" | "expired" | "not_implemented";
  reason?: string | null;
  forecast_id: string;
  probability_filter: number;
  rule: string;
  matching_cells: number | null;
  total_areas: number | null;
  returned_areas: number | null;
  limit: number;
  areas: ForecastHighlight[];
}

export interface ForecastPoint {
  data_mode?: "real";
  status: "available" | "no_coverage" | "missing_input" | "expired" | "not_implemented";
  reason?: string | null;
  forecast?: ForecastDescriptor | null;
  requested_longitude: number;
  requested_latitude: number;
  cell?: ForecastCell | null;
  value?: number | null;
  probability?: number | null;
  unit?: string | null;
  uncertainty?: null;
  selection_rule: string;
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

export interface LinePoint {
  year: number;
  month: number;
  anomaly_c: number;
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

export interface PlanetaryForecast {
  data_mode?: "real";
  status: "available" | "no_coverage" | "missing_input" | "expired" | "not_implemented";
  reason?: string | null;
  forecast?: ForecastDescriptor | null;
  windows: PlanetaryWindow[];
  probability?: null;
  note: string;
}

export interface PlanetaryWindow {
  valid_from: string;
  valid_to: string;
  value: number;
  provider_type?: "predicted";
  temporal_state: "future" | "in_progress" | "expired" | "unknown";
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

export interface ProductList {
  data_mode?: "real";
  connected_sources: number;
  field_products: number;
  calculated_field_products?: number;
  calculated_indicator_products?: number;
  observation_records: number;
  historical_records?: number;
  imported_indicator_records?: number;
  calculated_signals: number;
  evaluated_signal_phenomena?: number;
  signal_count_definition?: string;
  catalog_phenomena: number;
  products: ScientificProduct[];
}

export interface ProductRegion {
  id: string;
  name: string;
  sample_id: string;
  geometry: GeoMultiPolygon;
  extent: GeographicExtent;
  quality: string;
}

export interface ProductSample {
  id: string;
  map_eligible?: boolean;
  time?: string | null;
  valid_to?: string | null;
  longitude?: number | null;
  latitude?: number | null;
  value?: number | null;
  category?: string | null;
  probability?: number | null;
  probability_definition?: string | null;
  quality: string;
  attributes?: Record<string, string | null>;
}

export interface ProductTrack {
  id: string;
  name: string;
  geometry: GeoMultiLineString;
  extent: GeographicExtent;
  sample_ids: string[];
  quality: string;
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

export interface RefreshJob {
  status: "running" | "stored" | "unchanged" | "failed";
  last_attempt_at: string;
  next_attempt_at: string;
  last_success_at?: string | null;
  last_change_at?: string | null;
  error?: string | null;
  kept_previous?: boolean;
  attempted_input_revisions?: Record<string, string>;
  successful_input_revisions?: Record<string, string>;
}

export interface RefreshStatus {
  enabled: boolean;
  recent_scan: boolean;
  last_scan_at?: string | null;
  worker_pid?: number | null;
  heartbeat_at?: string | null;
  jobs?: Record<string, RefreshJob>;
  note: string;
}

export interface RetrievedDocument {
  id: string;
  role: "documentation";
  applied_as_instruction: false;
}

export interface SSTAnomalyView {
  data_mode?: "real";
  status: "evaluated" | "not_evaluable" | "unavailable";
  reason?: string | null;
  assessment_period?: string;
  assessed_months?: number;
  flagged_months?: number;
  warm_months?: number;
  cold_months?: number;
  missing_months?: number;
  stale_input?: boolean;
  product?: ScientificProduct | null;
  current_daily_anomaly_id?: string | null;
  current_daily_anomaly_at?: string | null;
}

export interface ScientificCalculation {
  method_version: string;
  formula: string;
  parameters: Record<string, number>;
  inputs: CalculationInput[];
  reference_url: string;
  reference_period: string;
  applicability: string;
  result?: CalculationResult | null;
}

export interface ScientificGrid {
  width: number;
  height: number;
  west: number;
  east: number;
  south: number;
  north: number;
  crosses_antimeridian?: false;
  longitudes: number[];
  latitudes: number[];
  values: Array<number | null>;
  minimum: number | null;
  maximum: number | null;
  missing_cells: number;
  resolution: string;
  sampling: string;
  quality_mask: string;
  color_scale?: "linear" | "log10";
  reverse_colors?: boolean;
  color_center?: number | null;
  quality_values?: Array<number | null> | null;
  quality_legend?: Record<string, string>;
}

export interface ScientificProduct {
  schema_version?: "1.0";
  data_mode?: "real";
  id: string;
  source_id: string;
  title: string;
  collection_id: string;
  product_version: string;
  variable: string;
  unit: string;
  native_unit: string;
  kind: "observation" | "indicator" | "forecast" | "historical" | "static_context" | "orbital_assessment";
  representation: "field" | "points" | "planetary" | "table" | "regions" | "tracks" | "time_series";
  observed_at?: string | null;
  observation_end?: string | null;
  initialized_at?: string | null;
  issued_at?: string | null;
  issue_time_basis?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
  retrieved_at: string;
  ingested_at: string;
  original_url: string;
  license_url: string;
  attribution: string;
  checksum_sha256: string;
  scientific_checksum_sha256?: string | null;
  byte_size: number;
  raw_file: string;
  coverage: string;
  extent?: GeographicExtent | null;
  cadence_seconds: number;
  method_version: string;
  limitation: string;
  probability?: null;
  validated_for_use?: false;
  grid?: ScientificGrid | null;
  samples?: ProductSample[];
  tracks?: ProductTrack[];
  regions?: ProductRegion[];
  calculation?: ScientificCalculation | null;
  verification: Verification;
}

export interface SentryAssessments {
  data_mode?: "real";
  status: "available" | "no_coverage" | "missing_input" | "expired" | "not_implemented";
  reason?: string | null;
  signature_version?: string | null;
  retrieved_at?: string | null;
  checksum_sha256?: string | null;
  source_url: string;
  objects: SentryObject[];
  removed: SentryObject[];
  limitation: string;
  meaning: string;
  update?: RefreshJob | null;
  update_pending?: boolean;
}

export interface SentryObject {
  designation: string;
  fullname: string;
  catalog_id?: string | null;
  status: "current" | "removed" | "not_listed";
  cumulative_probability?: number | null;
  cumulative_probability_text?: string | null;
  palermo_cumulative?: number | null;
  palermo_max?: number | null;
  torino_max?: number | null;
  diameter_km?: number | null;
  absolute_magnitude_h?: number | null;
  v_inf_km_s?: number | null;
  potential_impacts?: number | null;
  year_range?: string | null;
  last_observation?: string | null;
  removed_at?: string | null;
}

export interface SentryObjectDetail {
  designation: string;
  fullname: string;
  catalog_id?: string | null;
  status: "current" | "removed" | "not_listed";
  cumulative_probability?: number | null;
  cumulative_probability_text?: string | null;
  palermo_cumulative?: number | null;
  palermo_max?: number | null;
  torino_max?: number | null;
  diameter_km?: number | null;
  absolute_magnitude_h?: number | null;
  v_inf_km_s?: number | null;
  potential_impacts?: number | null;
  year_range?: string | null;
  last_observation?: string | null;
  removed_at?: string | null;
  scenarios: SentryScenario[];
  scenarios_status: "available" | "missing_input";
  scenarios_reason?: string | null;
}

export interface SentryScenario {
  date_text: string;
  date_utc?: string | null;
  probability: number;
  probability_text: string;
  palermo?: number | null;
  torino?: number | null;
  energy_mt?: string | null;
  method?: string | null;
  sigma_kind?: string | null;
  sigma_text?: string | null;
}

export interface SeriesPoint {
  year: number;
  month: number;
  sst_c: number | null;
  anomaly_c: number | null;
  present_days: number;
  expected_days: number;
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

export interface TrendView {
  schema_version: "1.0";
  execution_id: string;
  data_mode: "real";
  status: "evaluated" | "not_evaluable" | "unavailable";
  reason?: string | null;
  method_id: string;
  method_version: string;
  source_id: "D15";
  variable_id: "V15";
  region_id: string;
  unit: "°C";
  anomaly_kind: "absolute_celsius";
  aggregation: string;
  reference_start: string;
  reference_end: string;
  analysis_start: string;
  analysis_end: string;
  cutoff?: string | null;
  expected_months: number;
  present_months: number;
  missing_months: number;
  coverage: number | null;
  slope_c_per_year: number | null;
  interval_low_c_per_year: number | null;
  interval_high_c_per_year: number | null;
  includes_zero: boolean | null;
  practical_threshold_c_per_year: number;
  practical_threshold_exceeded: boolean | null;
  predictable: "not_a_forecast";
  cause: "not_identified";
  assumptions: string[];
  warnings: string[];
  asset_checksums: string[];
  narrative: string;
  series: SeriesPoint[];
  trend_line: LinePoint[];
  interval_low_line: LinePoint[];
  interval_high_line: LinePoint[];
  source_series_sha256?: string | null;
  region_extent?: GeographicExtent | null;
  bootstrap_block_months?: number;
  bootstrap_draws?: number;
  bootstrap_valid_draws?: number;
  sensitivity_block_months?: number;
  sensitivity_low_c_per_year?: number | null;
  sensitivity_high_c_per_year?: number | null;
  sensitivity_valid_draws?: number;
  residual_lag1_r?: number | null;
  conditional_interval?: true;
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

export interface Verification {
  method: string;
  original_url: string;
  checked_at: string;
  expected: string;
  actual: string;
  passed: true;
}

export interface VerticalPosition {
  value: number;
  unit: string;
  datum: string;
  direction: "down" | "up";
}

export interface ContractBundle {
  forecast_catalog: ForecastCatalog;
  forecast_field: ForecastField;
  forecast_point: ForecastPoint;
  forecast_highlights: ForecastHighlights;
  planetary_forecast: PlanetaryForecast;
  enso_outlook: EnsoOutlook;
  aftershock_forecasts: AftershockForecasts;
  sentry_assessments: SentryAssessments;
  sentry_object: SentryObjectDetail;
  assistant_request: AssistantRequest;
  assistant_reply: AssistantReply;
  sst_trend_analysis: TrendView;
  associations: AssociationView;
  sst_anomaly_analysis: SSTAnomalyView;
  refresh: RefreshStatus;
  scientific_products: ProductList;
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
