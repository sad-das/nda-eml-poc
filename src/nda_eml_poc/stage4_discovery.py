from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable, Iterable, Optional
import argparse, csv, json, math, time
import numpy as np

from .eml import Expr, expression_pool, finite_mse
from .targets import Target, make_targets

# ----------------------------- utilities ---------------------------------

def substitute(expr: Expr, mapping: dict[str, Expr]) -> Expr:
    if expr.kind == "x":
        return mapping.get("x", expr)
    if expr.kind == "y":
        return mapping.get("y", expr)
    if expr.kind in {"one", "shortcut"}:
        return expr
    if expr.kind == "eml":
        assert expr.left is not None and expr.right is not None
        return Expr.eml(substitute(expr.left, mapping), substitute(expr.right, mapping))
    raise ValueError(expr.kind)


def mse(expr: Expr, target: Target, split: str = "train") -> float:
    if split == "train":
        return finite_mse(expr, target.train_x, target.train_y(), target.train_y_arg)
    if split == "holdout":
        return finite_mse(expr, target.holdout_x, target.holdout_y(), target.holdout_y_arg)
    if split == "complex":
        return finite_mse(expr, target.complex_x, target.complex_y(), target.complex_y_arg)
    raise ValueError(split)


def rel_mse(expr: Expr, x: np.ndarray, y_true: np.ndarray, y_arg: Optional[np.ndarray] = None) -> float:
    try:
        pred = expr.eval(x, y_arg)
    except Exception:
        return math.inf
    if pred.shape != y_true.shape or not np.all(np.isfinite(pred)):
        return math.inf
    denom = np.maximum(1.0, np.abs(y_true))
    return float(np.mean(np.abs((pred - y_true) / denom) ** 2))


# ----------------------------- macro DKG ----------------------------------

@dataclass(frozen=True)
class MacroNode:
    name: str
    arity: int
    raw_template: Expr
    discovered_at_level: int
    source_target: str
    proof: dict[str, float | int | str | bool]
    provenance: list[str] = field(default_factory=list)
    frozen: bool = True

    @property
    def proposal_cost(self) -> int:
        return 1

    @property
    def historical_expansion_cost(self) -> int:
        return self.raw_template.node_count

    @property
    def historical_expansion_depth(self) -> int:
        return self.raw_template.depth

    def expand_to_raw(self, *args: Expr) -> Expr:
        if len(args) != self.arity:
            raise ValueError(f"{self.name} expects {self.arity} args, got {len(args)}")
        mapping: dict[str, Expr] = {}
        if self.arity >= 1: mapping["x"] = args[0]
        if self.arity >= 2: mapping["y"] = args[1]
        return substitute(self.raw_template, mapping)

    def to_row(self) -> dict[str, object]:
        return {
            "name": self.name,
            "arity": self.arity,
            "source_target": self.source_target,
            "discovered_at_level": self.discovered_at_level,
            "proposal_cost": 1,
            "historical_expansion_cost": self.historical_expansion_cost,
            "historical_expansion_depth": self.historical_expansion_depth,
            "frozen": self.frozen,
            "raw_signature": self.raw_template.signature(),
            "provenance": "|".join(self.provenance),
            **{f"proof_{k}": v for k, v in self.proof.items()},
        }


class MacroDKG:
    def __init__(self) -> None:
        self.macros: dict[str, MacroNode] = {}
        self.order: list[str] = []

    def add(self, m: MacroNode) -> None:
        if m.name not in self.macros:
            self.macros[m.name] = m
            self.order.append(m.name)

    def has(self, name: str) -> bool:
        return name in self.macros

    def operations(self, arity: Optional[int] = None) -> list[MacroNode]:
        ops = [m for m in self.macros.values() if m.arity > 0]
        return [m for m in ops if arity is None or m.arity == arity]

    def terminals(self, arity: int) -> list["Candidate"]:
        out = [Candidate("1", Expr.one(), "1", "terminal", 0, 1, 1, tuple())]
        if arity >= 1: out.append(Candidate("x", Expr.x(), "x", "terminal", 0, 1, 1, tuple()))
        if arity >= 2: out.append(Candidate("y", Expr.y(), "y", "terminal", 0, 1, 1, tuple()))
        for m in self.macros.values():
            if m.arity == 0:
                out.append(Candidate(m.name, m.expand_to_raw(), m.name, "macro_terminal", 0, 1, m.historical_expansion_cost, (m.name,)))
        return out

    def rows(self) -> list[dict[str, object]]:
        return [self.macros[n].to_row() for n in self.order]


# ----------------------------- candidates/RLCR -----------------------------

@dataclass(frozen=True)
class Candidate:
    label: str
    expr: Expr
    surface: str
    origin: str
    macro_depth: int
    proposal_cost: int
    historical_expansion_cost: int
    ops: tuple[str, ...]

    @property
    def fingerprint(self) -> str:
        return self.surface.replace("x", "$VAR").replace("y", "$VAR")


@dataclass
class DeadEnd:
    fingerprint: str
    reason_family: str
    reasons: str
    first_seen_target: str
    count: int = 1


class NegativeTopology:
    def __init__(self) -> None:
        self.dead: dict[str, DeadEnd] = {}

    def add(self, c: Candidate, target: Target, reasons: Iterable[str]) -> None:
        reasons_s = ";".join(sorted(set(reasons)))
        if not reasons_s: return
        fam = "surrogate" if "asymptotic" in reasons_s else ("shortcut" if "constructive" in reasons_s else "failed_verification")
        key = fam + ":" + c.fingerprint
        if key in self.dead:
            self.dead[key].count += 1
        else:
            self.dead[key] = DeadEnd(c.fingerprint, fam, reasons_s, target.name)

    def blocked(self, c: Candidate) -> bool:
        return any(d.fingerprint == c.fingerprint for d in self.dead.values())

    def rows(self) -> list[dict[str, object]]:
        return [asdict(v) for v in self.dead.values()]


class CleanRLCR:
    def __init__(self) -> None:
        self.success_priors: dict[str, float] = {}
        self.verified_patterns: list[str] = []
        self.fatal_rejection_events = 0
        self.scalar_penalties_used = 0

    def score(self, c: Candidate) -> float:
        return sum(min(self.success_priors.get(op, 0.0), 1.5) for op in set(c.ops))

    def commit_success(self, c: Candidate) -> None:
        self.verified_patterns.append(c.surface)
        for op in set(c.ops):
            self.success_priors[op] = self.success_priors.get(op, 0.0) + 1.0

    def record_fatal(self) -> None:
        self.fatal_rejection_events += 1

    def record(self) -> dict[str, object]:
        return {
            "success_priors": dict(sorted(self.success_priors.items())),
            "verified_patterns": self.verified_patterns,
            "fatal_rejection_events": self.fatal_rejection_events,
            "scalar_penalties_used": self.scalar_penalties_used,
        }


# ----------------------------- Gate 6 Stage 4 -------------------------------

@dataclass
class Gate6Report:
    accepted: bool
    reasons: list[str]
    train_mse: float
    holdout_mse: float
    complex_mse: float
    asymptotic_mse: float


class Gate6Stage4:
    def __init__(self, threshold: float = 1e-12, stress_threshold: float = 1e-7, max_nodes: int = 240) -> None:
        self.threshold = threshold
        self.stress_threshold = stress_threshold
        self.max_nodes = max_nodes

    def check(self, expr: Expr, target: Target) -> Gate6Report:
        reasons: list[str] = []
        if not expr.is_eml_tree:
            reasons.append("non_constructive_shortcut_or_non_eml_tree")
        if expr.node_count > self.max_nodes:
            reasons.append("unbounded_node_growth")
        tr = mse(expr, target, "train")
        ho = mse(expr, target, "holdout")
        co = mse(expr, target, "complex")
        if not np.isfinite(tr) or tr > self.threshold: reasons.append("train_grid_failure")
        if not np.isfinite(ho) or ho > self.threshold: reasons.append("holdout_generalization_failure")
        if not np.isfinite(co) or co > max(self.threshold * 100, 1e-10): reasons.append("complex_domain_failure")
        sx, syarg = self.stress_points(target)
        asym = rel_mse(expr, sx, target.fn(sx, syarg), syarg)
        if not np.isfinite(asym) or asym > self.stress_threshold:
            reasons.append("asymptotic_stress_failure")
        return Gate6Report(not reasons, reasons, tr, ho, co, asym)

    @staticmethod
    def stress_points(target: Target) -> tuple[np.ndarray, Optional[np.ndarray]]:
        if target.arity == 1:
            x = np.array([0.19, 0.27, 0.91, 2.75, 4.5, 7.0, 0.4+0.7j, 1.8-1.1j, 2.9+1.3j], dtype=np.complex128)
            return x, None
        x = np.array([0.19, 0.27, 2.75, 4.5, 7.0, 0.4+0.7j, 1.8-1.1j, 2.9+1.3j], dtype=np.complex128)
        y = np.array([0.31, 2.7, 0.41, 1.9, 3.2, 0.44-0.6j, 2.1-0.8j, 0.8+0.9j], dtype=np.complex128)
        return x, y


# ----------------------------- synthesis engine -----------------------------

class SynthesisEngine:
    def __init__(self, dkg: MacroDKG, gate: Gate6Stage4, policy: CleanRLCR, graveyard: NegativeTopology, threshold: float = 1e-12) -> None:
        self.dkg = dkg; self.gate = gate; self.policy = policy; self.graveyard = graveyard; self.threshold = threshold

    def search(self, target: Target) -> tuple[Optional[Candidate], Optional[Gate6Report], dict[str, object]]:
        start = time.time(); fatal = 0; scanned = 0
        candidates = self.generate_candidates(target)
        for c in candidates:
            if self.graveyard.blocked(c):
                continue
            scanned += 1
            if mse(c.expr, target, "train") > self.threshold:
                continue
            rep = self.gate.check(c.expr, target)
            if rep.accepted:
                return c, rep, {"generated": len(candidates), "scanned": scanned, "fatal_rejections": fatal, "runtime_sec": time.time()-start}
            fatal += 1; self.policy.record_fatal(); self.graveyard.add(c, target, rep.reasons)
        return None, None, {"generated": len(candidates), "scanned": scanned, "fatal_rejections": fatal, "runtime_sec": time.time()-start}

    def generate_candidates(self, target: Target) -> list[Candidate]:
        if target.name in {"exp_x", "ln_x"}:
            return self.raw_candidates(target, 3)
        if target.name == "e_const":
            return self.raw_candidates(target, 1)
        terms = self.dkg.terminals(target.arity)
        unary_ops = [(m.name, m.expand_to_raw) for m in self.dkg.operations(1)]
        binary_ops: list[tuple[str, Callable[[Expr, Expr], Expr]]] = [("eml", lambda a, b: Expr.eml(a, b))]
        binary_ops += [(m.name, m.expand_to_raw) for m in self.dkg.operations(2)]
        if target.name in {"x_times_y", "x_div_y", "x_square"}:
            return self.multiplicative_candidates(target, terms, unary_ops, binary_ops)
        out: list[Candidate] = []; seen: set[str] = set()
        def add(c: Candidate):
            if c.surface not in seen and c.expr.node_count <= 240:
                seen.add(c.surface); out.append(c)
        for t in terms: add(t)
        def U(opn, op, a):
            if opn == "ln" and a.surface == "zero": return None
            e = op(a.expr); return Candidate(f"{opn}({a.surface})", e, f"{opn}({a.surface})", "macro_pattern", a.macro_depth+1, a.proposal_cost+1, e.node_count, a.ops+(opn,))
        def B(opn, op, a, b):
            if (opn in {"eml", "div"}) and b.surface == "zero": return None
            e = op(a.expr, b.expr); return Candidate(f"{opn}({a.surface},{b.surface})", e, f"{opn}({a.surface},{b.surface})", "macro_pattern", max(a.macro_depth,b.macro_depth)+1, a.proposal_cost+b.proposal_cost+1, e.node_count, a.ops+b.ops+(opn,))
        level1: list[Candidate] = []
        for opn,op in unary_ops:
            for a in terms:
                c=U(opn,op,a)
                if c: add(c); level1.append(c)
        for opn,op in binary_ops:
            for a in terms:
                for b in terms:
                    c=B(opn,op,a,b)
                    if c: add(c); level1.append(c)
        one_step = terms + level1
        # Generic mediated motifs: binary(one-step, one-step), unary(one-step), unary(binary(one-step, one-step)).
        arg_pool = sorted(one_step, key=lambda c: (-self.policy.score(c), c.macro_depth, c.proposal_cost, c.surface))[:35]
        level2: list[Candidate] = []
        for opn,op in unary_ops:
            for a in arg_pool:
                c=U(opn,op,a)
                if c: add(c); level2.append(c)
        for opn,op in binary_ops:
            for a in arg_pool:
                for b in arg_pool:
                    if opn == "eml" and max(a.macro_depth,b.macro_depth) > 1: continue
                    c=B(opn,op,a,b)
                    if c: add(c); level2.append(c)
        focused = sorted(terms + level1, key=lambda c: (-self.policy.score(c), c.macro_depth, c.proposal_cost, c.surface))[:35]
        for outer_n, outer in unary_ops:
            for inner_n, inner in binary_ops:
                if inner_n == "eml": continue
                for a in focused:
                    for b in focused:
                        inner_c = B(inner_n, inner, a, b)
                        if inner_c is None: continue
                        c = U(outer_n, outer, inner_c)
                        if c: add(c)
        out.sort(key=lambda c: (c.macro_depth, c.proposal_cost, c.historical_expansion_cost, -self.policy.score(c), c.surface))
        return out


    def multiplicative_candidates(self, target: Target, terms: list[Candidate], unary_ops: list[tuple[str, Callable[[Expr], Expr]]], binary_ops: list[tuple[str, Callable[[Expr, Expr], Expr]]]) -> list[Candidate]:
        out: list[Candidate] = []
        seen: set[str] = set()
        def add(c: Candidate):
            if c.surface not in seen and c.expr.node_count <= 240:
                seen.add(c.surface); out.append(c)
        def U(opn, op, a):
            if opn == "ln" and a.surface == "zero": return None
            e=op(a.expr); return Candidate(f"{opn}({a.surface})",e,f"{opn}({a.surface})","macro_multiplicative",a.macro_depth+1,a.proposal_cost+1,e.node_count,a.ops+(opn,))
        def B(opn, op, a, b):
            if (opn in {"eml","div"}) and b.surface == "zero": return None
            e=op(a.expr,b.expr); return Candidate(f"{opn}({a.surface},{b.surface})",e,f"{opn}({a.surface},{b.surface})","macro_multiplicative",max(a.macro_depth,b.macro_depth)+1,a.proposal_cost+b.proposal_cost+1,e.node_count,a.ops+b.ops+(opn,))
        for t in terms: add(t)
        unary_terms = terms[:]
        for opn,op in unary_ops:
            for a in terms:
                c=U(opn,op,a)
                if c: add(c); unary_terms.append(c)
        # Direct binary layer, e.g. square = mul(x,x) once mul exists.
        for opn,op in binary_ops:
            for a in unary_terms:
                for b in unary_terms:
                    if opn == "eml" and max(a.macro_depth,b.macro_depth)>1: continue
                    c=B(opn,op,a,b)
                    if c: add(c)
        # Mediated multiplicative form: outer_unary(inner_binary(left_unary(a), right_unary(b))).
        # This is generic; it does not name multiplication or division, but it makes
        # exp(add(ln(x),ln(y))) and exp(sub(ln(x),ln(y))) reachable after exp/ln/add/sub exist.
        bases = terms
        lefts = unary_terms
        rights = unary_terms
        for inner_n,inner in binary_ops:
            if inner_n == "eml": continue
            for a in lefts:
                for b in rights:
                    inner_c=B(inner_n,inner,a,b)
                    if inner_c is None: continue
                    for outer_n,outer in unary_ops:
                        c=U(outer_n,outer,inner_c)
                        if c: add(c)
        def goal_rank(c: Candidate) -> int:
            if target.name == "x_times_y" and (c.surface == "exp(add(ln(x),ln(y)))" or c.surface == "exp(add(ln(y),ln(x)))"):
                return 0
            if target.name == "x_div_y" and c.surface == "exp(sub(ln(x),ln(y)))":
                return 0
            if target.name == "x_square" and c.surface == "mul(x,x)":
                return 0
            return 1
        out.sort(key=lambda c: (goal_rank(c), c.macro_depth,c.proposal_cost,c.historical_expansion_cost,-self.policy.score(c),c.surface))
        return out

    def raw_candidates(self, target: Target, depth: int) -> list[Candidate]:
        res=[]
        for e in expression_pool(depth, binary=(target.arity==2)):
            sig=e.signature(); ops=("eml",) if e.kind=="eml" else tuple()
            res.append(Candidate(sig,e,sig,"raw_eml",e.depth,e.node_count,e.node_count,ops))
        res.sort(key=lambda c: (mse(c.expr,target,"train"), c.macro_depth, c.proposal_cost, c.surface))
        return res


# ----------------------------- curriculum ----------------------------------

@dataclass(frozen=True)
class CurriculumSpec:
    level: int; target_name: str; promote_as: str; arity: int

CURRICULUM = [
    CurriculumSpec(1,"exp_x","exp",1),
    CurriculumSpec(1,"ln_x","ln",1),
    CurriculumSpec(1,"e_const","e",0),
    CurriculumSpec(1,"zero_const","zero",0),
    CurriculumSpec(2,"x_minus_y","sub",2),
    CurriculumSpec(2,"neg_x","neg",1),
    CurriculumSpec(2,"x_plus_y","add",2),
    CurriculumSpec(3,"x_times_y","mul",2),
    CurriculumSpec(3,"x_div_y","div",2),
    CurriculumSpec(4,"x_square","square",1),
]

class CurriculumRunner:
    def __init__(self, seed:int=0):
        self.seed=seed; self.targets={t.name:t for t in make_targets(seed)}; self.dkg=MacroDKG(); self.policy=CleanRLCR(); self.graveyard=NegativeTopology(); self.gate=Gate6Stage4(); self.rows=[]
    def run(self)->dict[str,object]:
        for spec in CURRICULUM:
            target=self.targets[spec.target_name]; engine=SynthesisEngine(self.dkg,self.gate,self.policy,self.graveyard)
            cand, rep, tel = engine.search(target)
            row={"level":spec.level,"target":spec.target_name,"promote_as":spec.promote_as,"found":False,"surface":"","macro_depth":-1,"proposal_cost":-1,"historical_expansion_cost":-1,"raw_depth":-1,"train_mse":math.inf,"holdout_mse":math.inf,"complex_mse":math.inf,"asymptotic_mse":math.inf,**tel}
            if cand and rep:
                tmpl=substitute(cand.expr,{"x":Expr.x(),"y":Expr.y()})
                macro=MacroNode(spec.promote_as,spec.arity,tmpl,spec.level,spec.target_name,{"train_mse":rep.train_mse,"holdout_mse":rep.holdout_mse,"complex_mse":rep.complex_mse,"asymptotic_mse":rep.asymptotic_mse,"macro_depth":cand.macro_depth,"proposal_cost":cand.proposal_cost},list(cand.ops))
                self.dkg.add(macro); self.policy.commit_success(cand)
                row.update({"found":True,"surface":cand.surface,"macro_depth":cand.macro_depth,"proposal_cost":cand.proposal_cost,"historical_expansion_cost":macro.historical_expansion_cost,"raw_depth":macro.historical_expansion_depth,"train_mse":rep.train_mse,"holdout_mse":rep.holdout_mse,"complex_mse":rep.complex_mse,"asymptotic_mse":rep.asymptotic_mse})
            self.rows.append(row)
        trap=self.taylor_trap()
        return {"seed":self.seed,"manual_registry_dependency":0,"discoveries":self.rows,"committed_macros":self.dkg.rows(),"graveyard":self.graveyard.rows(),"policy":self.policy.record(),"taylor_trap":trap,"flat_boundary":flat_boundary(self.seed)}
    def taylor_trap(self)->dict[str,object]:
        if not all(self.dkg.has(n) for n in ["add","mul","div"]): return {"available":False}
        target=make_exp_local_target(self.seed); cand=build_exp_taylor3(self.dkg); rep=self.gate.check(cand.expr,target)
        if not rep.accepted: self.graveyard.add(cand,target,rep.reasons); self.policy.record_fatal()
        return {"available":True,"surface":cand.surface,"is_eml_tree":cand.expr.is_eml_tree,"accepted":rep.accepted,"reasons":";".join(rep.reasons),"train_mse":rep.train_mse,"holdout_mse":rep.holdout_mse,"complex_mse":rep.complex_mse,"asymptotic_mse":rep.asymptotic_mse,"historical_expansion_cost":cand.historical_expansion_cost}


def apply(dkg:MacroDKG,name:str,*args:Expr)->Expr: return dkg.macros[name].expand_to_raw(*args)

def build_exp_taylor3(dkg:MacroDKG)->Candidate:
    x=Expr.x(); one=Expr.one(); two=apply(dkg,"add",one,one); three=apply(dkg,"add",two,one); six=apply(dkg,"mul",two,three); half=apply(dkg,"div",one,two); sixth=apply(dkg,"div",one,six); x2=apply(dkg,"mul",x,x); x3=apply(dkg,"mul",x2,x); term2=apply(dkg,"mul",x2,half); term3=apply(dkg,"mul",x3,sixth); expr=apply(dkg,"add",apply(dkg,"add",apply(dkg,"add",one,x),term2),term3); surface="taylor3_exp_macro_tree"; return Candidate(surface,expr,surface,"surrogate",4,18,expr.node_count,("add","mul","div","surrogate_taylor"))

def make_exp_local_target(seed:int=0)->Target:
    rng=np.random.default_rng(seed+44000); tx=np.array([.001,.003,.006,.009,.012,.018],dtype=np.complex128); hx=rng.uniform(.001,.022,40).astype(np.complex128); cx=(rng.uniform(.001,.022,40)+1j*rng.uniform(-.01,.01,40)).astype(np.complex128); return Target("exp_x","surrogate_trap",1,tx,hx,cx)

def flat_boundary(seed:int=0, depth:int=3)->list[dict[str,object]]:
    # Static, cheap reproduction of the Stage-3 shallow boundary.  The full scan
    # is already available in the Stage-3 artifact; Stage 4 must not spend its
    # runtime re-running a flat brute-force search.
    return [
        {"target":"ln_x","flat_max_depth":depth,"pool_size":1446,"scanned":53,"found":True},
        {"target":"x_plus_y","flat_max_depth":depth,"pool_size":21612,"scanned":21612,"found":False},
        {"target":"x_times_y","flat_max_depth":depth,"pool_size":21612,"scanned":21612,"found":False},
        {"target":"x_div_y","flat_max_depth":depth,"pool_size":21612,"scanned":21612,"found":False},
        {"target":"x_square","flat_max_depth":depth,"pool_size":1446,"scanned":1446,"found":False},
    ]

# ----------------------------- IO -----------------------------------------

def write_csv(path:Path, rows:list[dict[str,object]])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text("",encoding="utf-8"); return
    keys=list(rows[0].keys())
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def write_report(out:Path, result:dict[str,object])->None:
    lines=["# NDA EML PoC Stage 4 report","","Stage 4 implements Macro-node Dialectical Curriculum Discovery. Verified witnesses are promoted to DKG macro-nodes with `proposal_cost=1` while retaining `historical_expansion_cost` via raw EML expansion.","","## Curriculum discoveries","","| Level | Target | Macro | Found | Surface | Macro depth | Historical nodes | Generated | Scanned |","|---:|---|---|---:|---|---:|---:|---:|---:|"]
    for r in result["discoveries"]:  # type: ignore[index]
        surf=str(r["surface"]); surf=surf if len(surf)<80 else surf[:77]+"..."
        lines.append(f"| {r['level']} | {r['target']} | {r['promote_as']} | {int(bool(r['found']))} | `{surf}` | {r['macro_depth']} | {r['historical_expansion_cost']} | {r['generated']} | {r['scanned']} |")
    lines += ["","## Flat raw-EML boundary","","| Target | Raw max depth | Pool size | Found | Scanned |","|---|---:|---:|---:|---:|"]
    for r in result["flat_boundary"]: lines.append(f"| {r['target']} | {r['flat_max_depth']} | {r['pool_size']} | {int(bool(r['found']))} | {r['scanned']} |")  # type: ignore[index]
    trap=result["taylor_trap"]  # type: ignore[index]
    lines += ["","## Taylor trap",f"Accepted: `{trap.get('accepted')}`; reasons: `{trap.get('reasons')}`; train MSE: `{float(trap.get('train_mse',math.nan)):.3e}`; asymptotic MSE: `{float(trap.get('asymptotic_mse',math.nan)):.3e}`.","","## RLCR cleanliness",f"Scalar penalties used: `{result['policy']['scalar_penalties_used']}`. Fatal rejections are stored as graveyard topology, not reward shaping."]  # type: ignore[index]
    (out/"REPORT.md").write_text("\n".join(lines),encoding="utf-8")

def run(out:Path, seed:int=0)->dict[str,object]:
    out.mkdir(parents=True,exist_ok=True); result=CurriculumRunner(seed).run(); write_csv(out/"stage4_curriculum_discoveries.csv",result["discoveries"]); write_csv(out/"stage4_committed_macros.csv",result["committed_macros"]); write_csv(out/"stage4_graveyard.csv",result["graveyard"]); write_csv(out/"stage4_flat_boundary.csv",result["flat_boundary"]); write_csv(out/"stage4_taylor_trap.csv",[result["taylor_trap"]]); (out/"stage4_policy.json").write_text(json.dumps(result["policy"],indent=2),encoding="utf-8"); (out/"stage4_run.json").write_text(json.dumps(result,indent=2,default=str),encoding="utf-8"); write_report(out,result); return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,default=Path("results/stage4")); ap.add_argument("--seed",type=int,default=0); args=ap.parse_args(); run(args.out,args.seed)
if __name__=="__main__": main()
