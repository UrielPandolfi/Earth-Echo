"""Read only queries against retained, verified scientific products."""
from earth_echo.contracts.products import ProductList
from earth_echo.storage.products import all_products
from earth_echo.catalog.load import load_catalog
from earth_echo.queries.layers import quake_layer, kp_layer

def product_list(summaries: bool = False) -> ProductList:
    products = all_products()
    quakes = quake_layer()
    kp = kp_layer()
    sources = {p.source_id for p in products}
    if quakes.retrieved_at:
        sources.add('D21')
    if kp.retrieved_at:
        sources.add('D28')
    return ProductList(connected_sources=len(sources), field_products=sum(p.grid is not None for p in products),
        observation_records=quakes.count + kp.count + sum(len(p.samples) for p in products if p.kind in {'observation', 'historical'}),
        calculated_signals=0, catalog_phenomena=len(load_catalog().modules), products=[p.model_copy(update={'grid':None,'samples':[]}) for p in products] if summaries else products)
