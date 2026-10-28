"""Resolve CPI cells by expanded period/sector headers, never cell position."""
import calendar
import re

MONTHS = {name.lower(): i for i in range(1, 13)
          for name in (calendar.month_name[i], calendar.month_abbr[i])}
DATE = re.compile(r'\b(' + '|'.join(sorted(MONTHS, key=len, reverse=True))
                  + r')\.?\s*,?\s*(20\d{2})\b', re.I)
SECTORS = {'rural': 'Rural', 'urban': 'Urban', 'combd': 'Combined', 'combined': 'Combined'}


def normal(cell):
    return ' '.join(' '.join(cell.itertext()).split())


def shifted(month, offset):
    year, number = map(int, month.split('-'))
    index = year * 12 + number - 1 + offset
    return f'{index // 12}-{index % 12 + 1:02d}'


def expanded_grid(table):
    """Expand HTML spans so every physical column keeps its header ancestry."""
    rows = table.xpath('./tr|./thead/tr|./tbody/tr|./tfoot/tr')
    grid = [{} for _ in rows]
    for i, row in enumerate(rows):
        column = 0
        for cell in row.xpath('./td|./th'):
            while column in grid[i]:
                column += 1
            try:
                down, across = int(cell.get('rowspan', '1')), int(cell.get('colspan', '1'))
            except ValueError as error:
                raise ValueError('Invalid table span') from error
            if not 1 <= down <= len(rows) - i or not 1 <= across <= 100:
                raise ValueError('Unsupported table span')
            for r in range(i, i + down):
                for c in range(column, column + across):
                    if c in grid[r]:
                        raise ValueError('Overlapping table spans')
                    grid[r][c] = cell
            column += across
    return rows, grid


def ordered_cells(table, target_row, numeric_cells, reference_month=None):
    """Return current/previous/prior-year x Rural/Urban/Combined cells.

    Permutations are supported by semantic mapping; missing, duplicate,
    contradictory or ambiguous headers fail closed. The prior-year heading
    may explicitly say Final; its month distinguishes it from lag one.
    """
    rows, grid = expanded_grid(table)
    row_index = rows.index(target_row)
    mapping, current = {}, set()
    for cell in numeric_cells:
        columns = [column for column, value in grid[row_index].items() if value is cell]
        if len(columns) != 1:
            raise ValueError('Numeric CPI cell must occupy exactly one column')
        column = columns[0]
        ancestors = {grid[r][column] for r in range(row_index) if column in grid[r]}
        periods, sectors = set(), set()
        for ancestor in ancestors:
            label = normal(ancestor)
            sector = SECTORS.get(re.sub(r'[^a-z]', '', label.lower()))
            if sector:
                sectors.add(sector)
            matches = list(DATE.finditer(label))
            if len(matches) > 1:
                raise ValueError('Ambiguous multi-period header')
            if matches:
                match = matches[0]
                month = f'{match.group(2)}-{MONTHS[match.group(1).lower()]:02d}'
                provisional = bool(re.search(r'\bprov(?:isional)?\b', label, re.I))
                final = bool(re.search(r'\bfinal\b', label, re.I))
                if provisional and final:
                    raise ValueError('Conflicting provisional/final header')
                status = 'provisional' if provisional else 'final' if final else 'reference'
                periods.add((month, status))
        if len(periods) != 1 or len(sectors) != 1:
            raise ValueError('Missing or conflicting CPI period/sector header')
        month, status = next(iter(periods))
        sector = next(iter(sectors))
        if status == 'provisional':
            current.add(month)
        key = (month, sector)
        if key in mapping:
            raise ValueError('Duplicate CPI period/sector column')
        mapping[key] = (cell, status)
    if len(current) != 1:
        raise ValueError('Exactly one provisional CPI period required')
    current_month = next(iter(current))
    if reference_month is not None and current_month != reference_month:
        raise ValueError('Header reference month differs from release identity')
    periods = (current_month, shifted(current_month, -1), shifted(current_month, -12))
    expected = [(month, sector) for month in periods for sector in ('Rural', 'Urban', 'Combined')]
    if set(mapping) != set(expected):
        raise ValueError('CPI period/sector matrix is incomplete or unexpected')
    for month, sector in expected:
        status = mapping[(month, sector)][1]
        allowed = {'provisional'} if month == periods[0] else {'final'} if month == periods[1] else {'reference', 'final'}
        if status not in allowed:
            raise ValueError('CPI status inconsistent with reference period')
    return [mapping[key][0] for key in expected]
