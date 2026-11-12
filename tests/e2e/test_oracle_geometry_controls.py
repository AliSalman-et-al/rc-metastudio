"""Deliberate malformed rendered-output controls; no statistical backend stand-in."""
import pytest
from tests.e2e.plot_geometry_checks import check_interval_caps
from tests.e2e.axis_conventions import check_endpoints
from tests.e2e.header_geometry import check_headers


def svg(tmp_path, body):
    path = tmp_path / 'control.svg'
    path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">' + body + '</svg>')
    return path


def test_caps_require_rows_and_reject_crossing(tmp_path):
    def rows(count, height):
        return ''.join(f'<line x1="20" x2="80" y1="{y}" y2="{y}"/><line x1="20" x2="20" y1="{y-height/2}" y2="{y+height/2}"/>' for y in range(30, 30+count*20, 20))
    check_interval_caps(svg(tmp_path, rows(3, 4)))
    for count in (0, 1, 2):
        with pytest.raises(AssertionError, match='at least three'):
            check_interval_caps(svg(tmp_path, rows(count, 4)))
    with pytest.raises(AssertionError, match='cross row bands'):
        check_interval_caps(svg(tmp_path, rows(3, 15)))


def test_intervals_cannot_reuse_another_study_row(tmp_path):
    body = '<text x="0" y="33">A</text><text x="0" y="53">B</text><line x1="20" x2="80" y1="30" y2="30"/>'
    geometry = {'labels': ['A', 'B'], 'fitted': {'lower': [.2, .2], 'upper': [.8, .8], 'pooled': None}}
    check_endpoints(svg(tmp_path, body + '<line x1="20" x2="80" y1="50" y2="50"/>'), [(0, 0), (1, 100)], geometry, False, False)
    with pytest.raises(AssertionError, match='at study row'):
        check_endpoints(svg(tmp_path, body), [(0, 0), (1, 100)], geometry, False, False)


def test_header_device_clipping(tmp_path):
    def body(x):
        return f'<g><text x="{x}" y="20" style="font-size:10px" textLength="70">Comparison: X</text><text x="50" y="45" style="font-size:10px" textLength="30">Drug</text><text x="0" y="80">Fixture 1</text></g>'
    check_headers(svg(tmp_path, body(10)), ['Drug'])
    for x in (-1, 150):
        with pytest.raises(AssertionError, match='horizontally'):
            check_headers(svg(tmp_path, body(x)), ['Drug'])
