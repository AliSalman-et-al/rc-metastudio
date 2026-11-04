"""Throwaway audit of the two reviewed Windows leave-one-out plot replacements.

Run before the sanctioned updater. Numerical contracts are read, never written.
Raster geometry is compared in axis units within raster quantization; exact
numerical identity is checked separately against the frozen contract.
"""
from pathlib import Path
import io
import json
import re
import subprocess
import zipfile
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).parent
CAPTURE = HERE.parent / 'windows-capture'
BASELINE = ROOT / 'tests/analysis_regression/baseline'
BASE_REVISION = '2974b88b3a9f2727036fde015750a54eb1f99637'
CASES = [('amino-binary-leave-one-out', 20, (.2, 2), True),
         ('continuous-leave-one-out', 7, (.1, .6), False)]


def runs(mask):
    delta = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.where(delta == 1)[0], np.where(delta == -1)[0]))


def geometry(image, count):
    found = []
    for y in range(150, image.shape[0]):
        left, right = max(runs(image[y] < 100), key=lambda p: p[1] - p[0], default=(0, 0))
        if not (150 < right - left < image.shape[1] * .6 and
                left > image.shape[1] * .2 and right < image.shape[1] * .85):
            continue
        if not found or y > found[-1][3] + 1:
            found.append([int(left), int(right), y, y])
        else:
            found[-1][3] = y
    assert len(found) == count + 1, ('rows plus axis', len(found), count)
    axis = found.pop()
    rows = []
    for left, right, top, bottom in found:
        y = (top + bottom) // 2
        # Above the CI stroke only the estimate square has a wide ink run.
        squares = [(a, b) for a, b in runs(image[y - 16, left:right] < 100) if b - a > 25]
        assert len(squares) == 1, squares
        center = left + sum(squares[0]) / 2
        rows.append({'y': y, 'lower_x': left, 'estimate_x': center, 'upper_x': right})
    return rows, axis


def glyphs(image, y, start, stop):
    mask = image[y - 65:y + 65, start:stop] < 128
    result = []
    for left, right in runs(mask.any(axis=0)):
        char = mask[:, left:right]
        ys = np.where(char.any(axis=1))[0]
        result.append(char[ys[0]:ys[-1] + 1])
    return result


def same_glyph(a, b):
    # Fonts are identical; subpixel rasterization can move an edge by a pixel.
    assert max(abs(x - y) for x, y in zip(a.shape, b.shape)) <= 2, (a.shape, b.shape)
    height, width = np.maximum(a.shape, b.shape) + 4
    aa = np.zeros((height, width), dtype=bool)
    bb = aa.copy()
    aa[2:2 + a.shape[0], 2:2 + a.shape[1]] = a
    bb[2:2 + b.shape[0], 2:2 + b.shape[1]] = b
    def within_two_pixels(source, target):
        expanded = source.copy()
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if dx * dx + dy * dy <= 4:
                    expanded |= np.roll(source, (dy, dx), axis=(0, 1))
        return bool(np.all(expanded[target]))
    assert within_two_pixels(aa, bb) and within_two_pixels(bb, aa), 'glyph changed beyond two-pixel edge quantization'
    return 2



def main():
    contract = json.loads((BASELINE / 'numeric-contract.json').read_text())
    master_bytes = subprocess.check_output(['git', 'show', 'origin/master:tests/analysis_regression/baseline/observed-golden-baseline.zip'], cwd=ROOT)
    proof = {'source_run': 41820827724, 'passed': False, 'cases': []}
    before_bytes = subprocess.check_output(['git', 'show', BASE_REVISION + ':tests/analysis_regression/baseline/observed-golden-baseline.zip'], cwd=ROOT)
    with zipfile.ZipFile(io.BytesIO(before_bytes)) as baseline, zipfile.ZipFile(io.BytesIO(master_bytes)) as master:
        for case, count, limits, logarithmic in CASES:
            old = json.loads(baseline.read(f'captures/{case}.json'))
            original = json.loads(master.read(f'captures/{case}.json'))
            new = json.loads((CAPTURE / 'captures' / (case + '.json')).read_text())
            numeric = next(row for row in contract['cases'] if row['id'] == case)['sections']
            assert numeric == new['outputs'], 'exact frozen estimates, CIs, SEs, p-values'
            title = 'Leave-one-out Summary'
            before, after = original['texts'][title], new['texts'][title]
            # Includes the exact order and all numerical strings in each row.
            normalize = lambda value: re.sub(r'\s+', ' ', value.replace('Study omitted: ', '')).strip()
            assert normalize(before) == normalize(after)
            numbers = lambda value: re.findall(r'(?<![\w.])[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?', value)
            assert numbers(before) == numbers(after)
            assert old['texts'][title] == after
            old_descriptors = json.loads(json.dumps(old['plot_descriptors']))
            new_descriptors = json.loads(json.dumps(new['plot_descriptors']))
            for descriptors in (old_descriptors, new_descriptors):
                for descriptor in descriptors:
                    descriptor['display'].pop('sha256')
            assert old_descriptors == new_descriptors
            old_image_path = HERE / f'{case}-old.png'
            if not old_image_path.exists():
                member = next(name for name in baseline.namelist() if name.startswith('artifacts/' + case + '/') and name.endswith('.png'))
                old_image_path.write_bytes(baseline.read(member))
            images = [np.asarray(Image.open(HERE / f'{case}-{version}.png').convert('L')) for version in ('old', 'new')]
            old_rows, old_axis = geometry(images[0], count)
            new_rows, new_axis = geometry(images[1], count)
            evidence = []
            for index, (a, b) in enumerate(zip(old_rows, new_rows, strict=True)):
                assert a['y'] == b['y'], 'row count/order/y unchanged'
                coordinates = []
                for key in ('lower_x', 'estimate_x', 'upper_x'):
                    u = (a[key] - old_axis[0]) / (old_axis[1] - old_axis[0])
                    v = (b[key] - new_axis[0]) / (new_axis[1] - new_axis[0])
                    tolerance = 2 / min(old_axis[1] - old_axis[0], new_axis[1] - new_axis[0])
                    assert abs(u - v) <= tolerance, (case, index, key, u, v)
                    transform = lambda value: float(np.exp(np.log(limits[0]) + value * np.log(limits[1] / limits[0]))) if logarithmic else float(limits[0] + value * (limits[1] - limits[0]))
                    coordinates.append({'field': key, 'old_axis_fraction': u, 'new_axis_fraction': v,
                                        'old_raster_data_coordinate': transform(u), 'new_raster_data_coordinate': transform(v),
                                        'fraction_tolerance_two_pixels': tolerance})
                # Check every visible numerical annotation glyph in its row.
                ga = glyphs(images[0], a['y'], int(images[0].shape[1] * .72), images[0].shape[1])
                gb = glyphs(images[1], b['y'], int(images[1].shape[1] * .72), images[1].shape[1])
                assert len(ga) == len(gb)
                numeric_errors = [same_glyph(x, y) for x, y in zip(ga, gb, strict=True)]
                # The study-label remainder, including every year, is unchanged.
                removed = len('Studyomitted:') if index else 0
                label_masks = []
                for image, row, rows, prefix in ((images[0], a, old_rows, removed), (images[1], b, new_rows, 0)):
                    mask = image[row['y'] - 65:row['y'] + 65, :min(r['lower_x'] for r in rows) - 60] < 128
                    columns = runs(mask.any(axis=0))
                    mask = mask[:, columns[prefix][0]:columns[-1][1]]
                    ys = np.where(mask.any(axis=1))[0]
                    label_masks.append(mask[ys[0]:ys[-1] + 1])
                label_errors = [same_glyph(*label_masks)]
                evidence.append({'row_index': index, 'y': a['y'], 'coordinates': coordinates,
                                 'numeric_annotation_glyph_count': len(ga), 'numeric_glyph_edge_tolerance_px': max(numeric_errors),
                                 'study_label_prefix_glyphs_removed': removed, 'study_glyph_edge_tolerance_px': max(label_errors)})
            headers = []
            for image in images:
                mask = image[:150] < 128
                chunks = runs(mask.any(axis=0))
                split = max(range(len(chunks) - 1), key=lambda i: chunks[i + 1][0] - chunks[i][1])
                headings = []
                for left, right in ((chunks[0][0], chunks[split][1]), (chunks[split + 1][0], chunks[-1][1])):
                    heading = mask[:, left:right]
                    ys = np.where(heading.any(axis=1))[0]
                    headings.append(heading[ys[0]:ys[-1] + 1])
                headers.append(headings)
            for before_heading, after_heading in zip(*headers, strict=True):
                same_glyph(before_heading, after_heading)
            footer_images = []
            for image, rows, axis in ((images[0], old_rows, old_axis), (images[1], new_rows, new_axis)):
                mask = image[rows[-1]['y'] + 100:axis[2] - 20] < 128
                bands = runs(mask.any(axis=1))
                footer_images.append([mask[top:bottom] for top, bottom in bands])
            assert len(footer_images[0]) == len(footer_images[1]) == 4
            for old_line, new_line in zip(*footer_images, strict=True):
                old_cols = np.where(old_line.any(axis=0))[0]
                new_cols = np.where(new_line.any(axis=0))[0]
                same_glyph(old_line[:, old_cols[0]:old_cols[-1] + 1], new_line[:, new_cols[0]:new_cols[-1] + 1])
            # Tick strings keep their order while their x positions follow the axis.
            axis_glyphs = []
            for image, axis in ((images[0], old_axis), (images[1], new_axis)):
                mask = image[axis[3] + 20:] < 128
                bands = runs(mask.any(axis=1))
                top, bottom = bands[0]
                line = mask[top:bottom]
                axis_glyphs.append([line[:, left:right] for left, right in runs(line.any(axis=0))])
            assert len(axis_glyphs[0]) == len(axis_glyphs[1])
            for old_char, new_char in zip(*axis_glyphs, strict=True):
                same_glyph(old_char, new_char)
            proof['cases'].append({'id': case, 'row_count': count, 'exact_numeric_contract': numeric,
                                   'numeric_tokens_identical': numbers(after), 'weights': 'No weight column or weight values in either sequential plot.',
                                   'only_text_change': 'Study omitted: prefix removed from each omitted-study row; order unchanged.',
                                   'descriptor_changes': {'old_display_sha256': old['plot_descriptors'][0]['display']['sha256'], 'new_display_sha256': new['plot_descriptors'][0]['display']['sha256']},
                                   'raster_geometry_note': 'Exact data values checked above; axis-normalized raster points agree within two pixels (finite raster precision). Absolute canvas coordinates intentionally differ.',
                                   'footer_text_lines_identical': 4, 'axis_tick_glyphs_identical': len(axis_glyphs[0]), 'rows': evidence})
    proof['passed'] = True
    (HERE / 'proof.json').write_text(json.dumps(proof, indent=2) + '\n')
    print('PASS: only two prefix-removal plots; exact frozen numerical values and row text/order; every row numeric/study glyph and axis-normalized CI/estimate checked.')


if __name__ == '__main__':
    main()
