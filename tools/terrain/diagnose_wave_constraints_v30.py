"""Read-only linear feasibility certificate for the rejected shore profile."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

import deepen_wave_margins_v30 as author
from v30_common import tri_sample


def main():
    old = np.load(author.SOURCE)['heights'].astype(float)
    first = Path('E:/DayZ-Baltic-Build/v30-wave-margin/terrain_v30.npz')
    desired = old - np.load(first)['heights'].astype(float)
    points = [p for p in json.loads(author.REFERENCE.read_text())['points']
              if p['role'] == 'frozen_shallow_failure']
    result_path = first.parent/'constrained-feasibility.json'
    assert not result_path.exists()

    def inspect(_fun, _x0, **kwargs):
        linear, slopes = kwargs['constraints']
        count = len(points)
        matrix = np.asarray(linear.A)
        target = kwargs['bounds'].ub
        # Maximise a common achievable nominal depth, while keeping all the
        # frozen dry clearances and original edit bounds. Face limits are
        # omitted, so this is an optimistic upper bound, never acceptance.
        wet = np.column_stack((-matrix[:count], np.ones(count)))
        dry = np.column_stack((matrix[count:], np.zeros(len(matrix)-count)))
        depths = np.array([p['pond_plane_m']-float(tri_sample(old,p['x'],p['z'])) for p in points])
        fit = linprog(np.r_[np.zeros(len(target)), -1.],
                      A_ub=np.vstack((wet,dry)), b_ub=np.r_[depths,linear.ub[count:]],
                      bounds=[(0,float(v)) for v in target]+[(None,None)], method='highs')
        report = dict(status='DIAGNOSTIC_ONLY', success=bool(fit.success), message=fit.message,
                      source_sha256=author.sha(author.SOURCE), first_candidate_sha256=author.sha(first),
                      solver_failure='Positive directional derivative for linesearch',
                      limit='Optimistic linear bound; face constraints omitted; no terrain emitted.')
        if fit.success:
            report.update(maximum_common_depth_m=float(fit.x[-1]),
                          slope_minimum_margin_at_linear_solution=float(slopes['fun'](fit.x[:-1]).min()),
                          wet=[dict(id=p['id'], depth_m=float(depths[i]+matrix[i]@fit.x[:-1]),
                                    dual=float(fit.ineqlin.marginals[i])) for i,p in enumerate(points)],
                          binding_dry_rows=[dict(row=count+i,slack_m=float(s),dual=float(fit.ineqlin.marginals[count+i]))
                                            for i,s in enumerate(fit.ineqlin.residual[count:]) if s<1e-7])
        result_path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,indent=2))
        raise StopIteration

    author.minimize = inspect
    try:
        author.retain_dry_and_face_constraints(old,desired,points)
    except StopIteration:
        pass


if __name__ == '__main__':
    main()
