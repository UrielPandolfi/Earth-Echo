"""Scientific products shared by sources, without making raster cells into signals."""
import math
from typing import Literal
from pydantic import Field, model_validator
from earth_echo.contracts.types import ApiModel, CatalogSourceId, UtcDateTime
from earth_echo.contracts.geometry import GeoMultiLineString,GeoMultiPolygon,GeographicExtent

class ScientificGrid(ApiModel):
    width: int = Field(gt=0, le=4096)
    height: int = Field(gt=0, le=2048)
    west: float = Field(ge=-180, le=180)
    east: float = Field(ge=-180, le=180)
    south: float = Field(ge=-90, le=90)
    north: float = Field(ge=-90, le=90)
    crosses_antimeridian: Literal[False] = False
    longitudes: list[float]
    latitudes: list[float]
    values: list[float | None]
    minimum: float | None
    maximum: float | None
    missing_cells: int = Field(ge=0)
    resolution: str
    sampling: str
    quality_mask: str
    color_scale: Literal['linear','log10'] = 'linear'
    reverse_colors: bool = False
    color_center: float | None = Field(default=None,allow_inf_nan=False)
    quality_values: list[int | None] | None = None
    quality_legend: dict[str,str] = Field(default_factory=dict)

    @model_validator(mode='after')
    def check_grid(self):
        if self.color_center is not None and (self.color_scale!='linear' or self.reverse_colors):
            raise ValueError('Centered field colours require an unreversed linear scale')
        if len(self.values) != self.width * self.height or len(self.longitudes) != self.width or len(self.latitudes) != self.height:
            raise ValueError('Grid shape mismatch')
        if self.west >= self.east or self.south >= self.north:
            raise ValueError('Invalid WGS84 bounds')
        if any(a >= b for a, b in zip(self.longitudes, self.longitudes[1:])) or any(a <= b for a, b in zip(self.latitudes, self.latitudes[1:])):
            raise ValueError('Grid must be west-to-east and north-to-south')
        if any(v is not None and not math.isfinite(v) for v in self.values):
            raise ValueError('Nonfinite value must be missing')
        if self.missing_cells != self.values.count(None):
            raise ValueError('Invalid missing count')
        if self.quality_values is not None and len(self.quality_values)!=len(self.values):
            raise ValueError('Quality grid shape mismatch')
        if self.color_scale=='log10' and any(v is not None and v<=0 for v in self.values):
            raise ValueError('Log display requires positive scientific values; zero must not be silently masked')
        return self

class ProductSample(ApiModel):
    id: str
    map_eligible: bool = True
    time: UtcDateTime | None = None
    valid_to: UtcDateTime | None = None
    longitude: float | None = Field(default=None, ge=-180, le=180)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    value: float | None = None
    category: str | None = None
    probability: float | None = Field(default=None, ge=0, le=1)
    probability_definition: str | None = None
    quality: str
    attributes: dict[str, str | None] = Field(default_factory=dict)

    @model_validator(mode='after')
    def check_probability(self):
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError('Nonfinite sample must be missing')
        if (self.probability is None) != (self.probability_definition is None):
            raise ValueError('A probability needs its definition')
        return self

class ProductTrack(ApiModel):
    id: str
    name: str
    geometry: GeoMultiLineString
    extent: GeographicExtent
    sample_ids: list[str] = Field(min_length=2)
    quality: str

class ProductRegion(ApiModel):
    id: str
    name: str
    sample_id: str
    geometry: GeoMultiPolygon
    extent: GeographicExtent
    quality: str

class Verification(ApiModel):
    method: str
    original_url: str
    checked_at: UtcDateTime
    expected: str
    actual: str
    passed: Literal[True]

class CalculationInput(ApiModel):
    product_id: str
    variable: str
    unit: str
    checksum_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')

class CalculationResult(ApiModel):
    label: str
    value: float = Field(allow_inf_nan=False)
    unit: str

class ScientificCalculation(ApiModel):
    method_version: str
    formula: str
    parameters: dict[str,float]
    inputs: list[CalculationInput]
    reference_url: str
    reference_period: str
    applicability: str
    result: CalculationResult | None = None

class ScientificProduct(ApiModel):
    schema_version: Literal['1.0'] = '1.0'
    data_mode: Literal['real'] = 'real'
    id: str = Field(pattern=r'^[a-z0-9-]+$')
    source_id: CatalogSourceId
    title: str
    collection_id: str
    product_version: str
    variable: str
    unit: str
    native_unit: str
    kind: Literal['observation', 'indicator', 'forecast', 'historical', 'static_context', 'orbital_assessment']
    representation: Literal['field', 'points', 'planetary', 'table', 'regions', 'tracks', 'time_series']
    observed_at: UtcDateTime | None = None
    observation_end: UtcDateTime | None = None
    initialized_at: UtcDateTime | None = None
    issued_at: UtcDateTime | None = None
    issue_time_basis: str | None = None
    valid_from: UtcDateTime | None = None
    valid_to: UtcDateTime | None = None
    retrieved_at: UtcDateTime
    ingested_at: UtcDateTime
    original_url: str
    license_url: str
    attribution: str
    checksum_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    scientific_checksum_sha256: str | None = Field(default=None,pattern=r'^[0-9a-f]{64}$')
    byte_size: int = Field(gt=0)
    raw_file: str = Field(pattern=r'^(?:shared|[a-z0-9-]+/assets)/[0-9a-f]{64}\.[a-z0-9]+$')
    coverage: str
    extent: GeographicExtent | None = None
    cadence_seconds: int = Field(gt=0)
    method_version: str
    limitation: str
    probability: None = None
    validated_for_use: Literal[False] = False
    grid: ScientificGrid | None = None
    samples: list[ProductSample] = Field(default_factory=list)
    tracks: list[ProductTrack] = Field(default_factory=list)
    regions: list[ProductRegion] = Field(default_factory=list)
    calculation: ScientificCalculation | None = None
    verification: Verification

class ProductList(ApiModel):
    data_mode: Literal['real'] = 'real'
    connected_sources: int
    field_products: int
    calculated_field_products: int = 0
    calculated_indicator_products: int = 0
    observation_records: int
    historical_records: int = 0
    imported_indicator_records: int = 0
    calculated_signals: int
    catalog_phenomena: int
    products: list[ScientificProduct]
