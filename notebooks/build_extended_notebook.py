"""Build the standalone Colab export notebook from the two SQL files."""

import json
from pathlib import Path


def cell(kind, source):
    result = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True)}
    if kind == 'code':
        result.update({'execution_count': None, 'outputs': []})
    return result


def build():
    root = Path(__file__).resolve().parents[1]
    names = ['ad_reward_candidates', 'quickplay_candidates']
    queries = {name: (root / 'sql' / (name + '.sql')).read_text(encoding='utf-8') for name in names}
    cells = [
        cell('markdown', '''# Flood-It! — gameplay and ad-reward export

We already finished the retention experiment. This notebook gets the data for the next two questions: can we predict a future recorded ad reward, and can we predict the result of a quickplay attempt from the player's prior gameplay? It does not measure ad acceptance, revenue or the effect of changing difficulty.

Use your existing BigQuery sandbox project. Run each cell. We check the estimated scan first and cap the total at 25 GiB. Do not enable billing. Keep the player-level export out of GitHub.
'''),
        cell('code', '''from google.colab import auth
from google.cloud import bigquery

auth.authenticate_user()
project_id = input('Enter your Google Cloud project ID: ').strip()
if not project_id:
    raise ValueError('Enter your own BigQuery project ID.')
client = bigquery.Client(project=project_id)
'''),
        cell('code', 'queries = ' + repr(queries) + '''

GIB = 1024 ** 3
TOTAL_LIMIT = 25 * GIB
estimates = {}
for name, sql in queries.items():
    config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
    job = client.query(sql, job_config=config)
    estimates[name] = job.total_bytes_processed
    if estimates[name] is None:
        raise RuntimeError('BigQuery did not report an estimate.')
    print(f'{name}: {estimates[name] / GIB:.3f} GiB')

print(f'Total estimated scan: {sum(estimates.values()) / GIB:.3f} GiB')
if sum(estimates.values()) > TOTAL_LIMIT:
    raise RuntimeError('The estimated scan exceeds 25 GiB. Stop here.')
'''),
        cell('code', '''import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import mkdtemp
from zipfile import ZipFile, ZIP_DEFLATED
from google.colab import files

if input('Check the free quota. Type RUN to export: ').strip() != 'RUN':
    raise RuntimeError('Export cancelled.')

folder = Path(mkdtemp(prefix='flood_it_extended_'))
remaining = TOTAL_LIMIT
manifest = {'exported_utc': datetime.now(timezone.utc).isoformat(), 'queries': []}
for name, sql in queries.items():
    if estimates[name] > remaining or remaining <= 0:
        raise RuntimeError('Remaining query cap is too small.')
    config = bigquery.QueryJobConfig(maximum_bytes_billed=remaining)
    job = client.query(sql, job_config=config)
    rows = job.result()
    columns = [field.name for field in rows.schema]
    count = 0
    with (folder / f'{name}.csv').open('w', newline='', encoding='utf-8') as output:
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([row[column] for column in columns])
            count += 1
    billed = job.total_bytes_billed
    if billed is None:
        raise RuntimeError('BigQuery did not report billed bytes; stop and review.')
    remaining -= max(billed, estimates[name])
    manifest['queries'].append({'name': name, 'rows': count, 'job_id': job.job_id,
                                'estimated_bytes': estimates[name], 'billed_bytes': billed, 'sql': sql})
    print(f'{name}: {count:,} rows saved')

(folder / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
archive = folder / 'flood_it_extended.zip'
with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as bundle:
    for path in sorted(folder.iterdir()):
        if path.suffix in ('.csv', '.json'):
            bundle.write(path, arcname=path.name)
files.download(str(archive))
'''),
        cell('markdown', 'Upload `flood_it_extended.zip` to our project chat. We will check how many usable observations and positive labels we have before training either model.\n'),
    ]
    notebook = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
                'language_info': {'name': 'python'}, 'colab': {'provenance': []}}, 'nbformat': 4, 'nbformat_minor': 4}
    path = root / 'notebooks' / 'flood_it_extended_export.ipynb'
    path.write_text(json.dumps(notebook, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    build()
