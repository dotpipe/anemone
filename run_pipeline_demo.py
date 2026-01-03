import importlib
import json
import taxonomic_grammar as tg
importlib.reload(tg)

res = tg.pipeline_response(
    "A fountain sprays while tigers stalk the water near the old bridge",
    settings={'variations_steps':4,'temperature':0.6,'minimal_templates':False,'reverse':True,'verbosity':'long'}
)
print(json.dumps({
    'text_response': res.get('text_response'),
    'topic_file': res.get('topic_file'),
    'main_taxon_variable': res.get('main_taxon', {}).get('variable') if res.get('main_taxon') else None,
    'related_count': len(res.get('related', []))
}, indent=2, ensure_ascii=False))

print('\n--- Fragment responses ---')
for f in res['fragments']:
    print('\nFragment:', f['fragment'])
    print('Verbs:', f['verbs'])
    print('Response fragment (summary):', f['response_fragment']['response'][:200])
