import os
import json
import sys

# Simple StatsBomb events summarizer.
# Usage: place the cloned statsbomb open-data repo at ./statsbomb_open (or clone it),
# then run: python statsbomb_demo.py

BASE_DIR = 'statsbomb_open/data'
if not os.path.isdir(BASE_DIR):
    # try the repository top-level if named differently
    if os.path.isdir('open-data/data'):
        BASE_DIR = 'open-data/data'

if not os.path.isdir(BASE_DIR):
    print('StatsBomb data directory not found. Please clone https://github.com/statsbomb/open-data.git into \n  ./statsbomb_open\nthen re-run this script.')
    sys.exit(1)

# find event JSON files
events_files = []
for root, dirs, files in os.walk(BASE_DIR):
    if os.path.basename(root).lower().startswith('events') or 'events' in root.lower().split(os.sep):
        for f in files:
            if f.endswith('.json'):
                events_files.append(os.path.join(root, f))

# fallback: any json under data/events-like paths
if not events_files:
    for root, dirs, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith('.json') and 'event' in f.lower():
                events_files.append(os.path.join(root, f))

if not events_files:
    print('No events JSON files found under', BASE_DIR)
    sys.exit(1)

# pick the first events file
events_file = events_files[0]
print('Using events file:', events_file)

with open(events_file, 'r', encoding='utf8') as fh:
    events = json.load(fh)

print('Total events in file:', len(events))

# aggregate counts
total_counts = {}
by_team = {}
for e in events:
    tname = (e.get('team') or {}).get('name', 'Unknown')
    typ = (e.get('type') or {}).get('name', 'Unknown')
    total_counts[typ] = total_counts.get(typ, 0) + 1
    if tname not in by_team:
        by_team[tname] = {}
    by_team[tname][typ] = by_team[tname].get(typ, 0) + 1

print('\nTop event types overall:')
for k, v in sorted(total_counts.items(), key=lambda x: -x[1])[:10]:
    print(f'  {k}: {v}')

print('\nPer-team top events:')
for team, d in by_team.items():
    print('\n', team)
    for k, v in sorted(d.items(), key=lambda x: -x[1])[:10]:
        print(f'  {k}: {v}')

# write a summary JSON
summary = {'events_file': events_file, 'total_events': len(events), 'top_event_types': sorted(total_counts.items(), key=lambda x:-x[1])[:20], 'by_team': by_team}
with open('statsbomb_summary.json', 'w', encoding='utf8') as out:
    json.dump(summary, out, indent=2, ensure_ascii=False)

print('\nSummary written to statsbomb_summary.json')
