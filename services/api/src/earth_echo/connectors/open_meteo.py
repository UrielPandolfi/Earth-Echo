"""Transport representation helpers, without choosing products or scientific meaning."""
import csv
import io
import math

LICENSE = 'https://open-meteo.com/en/licence'


def number(value):
    if value is None or value in ('', 'NaN', 'nan'):
        return None
    if isinstance(value, bool):
        raise ValueError('Boolean is not a scientific numeric value')
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Nonfinite value; explicit missing required')
    return result


def csv_sections(raw):
    blocks = raw.decode('utf-8').strip().replace('\r\n', '\n').split('\n\n')
    if len(blocks) != 2:
        raise ValueError('Independent CSV structure changed')
    return [list(csv.DictReader(io.StringIO(block))) for block in blocks]
