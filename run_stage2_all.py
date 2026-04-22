import json, csv, sys, os
from pathlib import Path
from statistics import mean
sys.path.insert(0, 'src')
from nda_eml_poc.agent import NDAStage2Agent
from nda_eml_poc.run_ablation import VARIANTS, summarize, write_csv, write_report

out=Path('results/stage2'); out.mkdir(parents=True, exist_ok=True)
runs=[]
for v in ['nda_full','no_freeze','no_gate6','no_rlcr','random_tree','gradient_only']:
    for seed in [0,1,2]:
        print('RUN',v,seed,flush=True)
        run=NDAStage2Agent(VARIANTS[v], seed=seed).run()
        runs.append(run)
        (out/f'run_{v}_seed{seed}.json').write_text(json.dumps(run.to_jsonable(), ensure_ascii=False, indent=2), encoding='utf-8')
        print('DONE',v,seed,flush=True)
summary=summarize(runs)
target_rows=[tr.__dict__ for run in runs for tr in run.results]
write_csv(out/'summary_metrics.csv', summary)
write_csv(out/'target_results.csv', target_rows)
(out/'summary_metrics.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
write_report(out/'REPORT.md', summary)
print('ALL_DONE',flush=True)
