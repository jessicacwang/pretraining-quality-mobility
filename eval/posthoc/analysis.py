import pandas as pd

df = pd.read_csv(
    "fineweb_output.csv", 
    dtype={
        "doc_id": "string",
        "language": "string",
        "language_score": "Float64",
        "filter_reason": "string",
        "result": "string",
        "stage_excluded": "Int64",
        "source": "string",
        "genre": "string",
        "component": "string",
        "cluster_id": "string",
        "mobility_v1": "string",
        "mobility_v2": "string"
    }
    )
for m in df.mobility_v2.unique().tolist():
    print(f"Mobility level: {m}")
    mdf = df.loc[df.mobility_v2 == m]
    for c in mdf.genre.unique().tolist():
        subset = mdf.loc[mdf.genre == c]
        retained = subset.filter_reason.isna().sum()
        print(f"{c} RR={retained / len(subset):.3f}, total={len(subset)}")

print("How many documents were excluded at each stage?")
print(df.stage_excluded.value_counts(dropna=False).sort_index()) 
print()

print("How many documents were excluded for each possible reason?")
print(df.filter_reason.value_counts())
print()

top_n_reasons = df.filter_reason.value_counts().head(5).index.tolist()
features = [
    # "source",
    # "cluster_id",
    # "mobility_v1",
    # "mobility_v2",
    # "component",
    "genre",
]

def check_filter_reason(reason):
    df2 = df.loc[df.filter_reason == reason]
    print(f"For documents excluded due to {reason}, how many came from each corpus?")
    print(df2.source.value_counts())
    print("-"*30)
    print(f"For documents excluded due to {reason}, what genres were involved?")
    print(df2.genre.value_counts())
    print("-"*30)
    print(f"For documents excluded due to {reason}, what components were involved?")
    print(df2.component.value_counts())
    return

def check_feature(feature, reason):
    print(f"Filter results aggregated by {feature} filtered because {reason}:")
    rdf = df.loc[df.filter_reason == reason]
    print("-"*30)
    print(rdf.value_counts([feature, "result"], dropna=False).sort_index())

    fvals = df[feature].unique().tolist()
    for v in fvals:
        print("-"*30)
        vdf = df.loc[df[feature] == v]
        v_total = len(vdf)
        if v_total:
            v_retained = len(vdf.loc[vdf.result == "survive"])
            print(f"RR={v_retained / v_total:.3f} of rows where {feature}={v}")
        else:
            print(f"RR=0 where {feature}={v}")

        v_exclude = vdf.loc[vdf.result == "exclude"]
        if len(v_exclude):
            v_reason = v_exclude.loc[v_exclude.filter_reason == reason]
            print(f"{len(v_reason)/len(v_exclude):.3f} of excluded docs due to {reason}")
        print()
    return

def joint_prob1(df, feature, reason):
    # GOAL: P(feature value | reason)
    rdf = df.loc[df.filter_reason == reason]
    r_total = len(rdf)

    fvals = rdf[feature].unique().tolist()
    for v in fvals:
        print("-"*30)
        vdf = rdf.loc[rdf[feature] == v]
        v_total = len(vdf)
        p_v = v_total / r_total
        print(f"P({feature}:{v} | {reason})={p_v:.3f}, P({feature}:{v})={v_total / d_total:.3f}")
    print()
    return

def joint_prob2(df, feature, reason):
    # GOAL: P(reason | feature value)

    fvals = df[feature].unique().tolist()
    for v in fvals:
        print("-"*30)
        vdf = df.loc[df[feature] == v]
        v_total = len(vdf)

        rdf = vdf.loc[vdf.filter_reason == reason]
        r_total = len(rdf)
        p_v = r_total / v_total
        print(f"P({reason} | {feature}:{v})={p_v:.3f}")
    print()
    return

d_total = len(df)
for r in top_n_reasons:
    print("="*30)
    print(f"comparing records dropped because {r} vs. all other outcomes".upper())
    print("-"*30)
    print(f"P({r}): {len(df.loc[df.filter_reason == r]) / d_total:.3f}")
    for f in features:
        joint_prob1(df, f, r)
        joint_prob2(df, f, r)
    print()