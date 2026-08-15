import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency

# Load data
df = pd.read_csv("output/eval/pmi/by_source_genre_cluster_english.csv")
df["features"] = df.feature_value.str.split(" / ")


def map_nested_features(row):
    row["cluster"] = row["features"][-1]
    if row["features"][0] != "ice":
        row["scale"] = "high"
        if row["features"][0] == "lince":
            row["mobility"] = "low"
        else:
            row["mobility"] = "high"
    else:
        row["scale"] = "low"
        if row["features"][1] == "spoken":
            row["mobility"] = "low"
        else:
            row["mobility"] = "high"

    return row


df = df.apply(map_nested_features, axis=1)[
    [
        "scale",
        "mobility",
        "cluster",
        "joint_count",
        "marginal_count",
        "cumulative_retention",
    ]
]
# df = df.loc[df.cluster != 5]


# Compute filtered and not-filtered values
def generate_response_labels(df):
    df["filtered"] = df["joint_count"]
    df["not_filtered"] = df["marginal_count"] - df["joint_count"]
    return


generate_response_labels(df)
df.to_csv("temp.csv")


def prime(n):
    return n + 0.5


def odds_ratio(a, b, c, d):
    """a=filtered in group, b=not_filtered in group, c=filtered outside, d=not_filtered outside"""
    # if b == 0 or c == 0:
    #     return np.inf  # flag rather than silently divide by near-zero
    return (prime(a) * prime(d)) / (prime(b) * prime(c))


total_filtered = df["filtered"].sum()
total_not_filtered = df["not_filtered"].sum()


def cramers_v(table):
    table = np.array(table)
    chi2, p, dof, _ = chi2_contingency(table)
    n = table.sum()
    r, k = table.shape
    v = np.sqrt(chi2 / (n * (min(r, k) - 1)))
    return v, chi2, p, dof


def cluster_vs_rest(df, val):
    cluster_1_rows = df[df["cluster"] == val]
    rest_rows = df[df["cluster"] != val]

    a = cluster_1_rows["filtered"].sum()
    b = cluster_1_rows["not_filtered"].sum()
    c = rest_rows["filtered"].sum()
    d = rest_rows["not_filtered"].sum()

    or_val = (a * d) / (b * c)
    return {
        f"cluster_{val}_filtered": a,
        f"cluster_{val}_not_filtered": b,
        "rest_filtered": c,
        "rest_not_filtered": d,
        "odds_ratio": or_val,
    }


for comp in df.cluster.unique():
    result = cluster_vs_rest(df, comp)
    print(f"=== Framework A: {comp} vs rest of world ===")
    for k, v in result.items():
        print(f"{k}: {v}")
    print()

cluster_agg = df.groupby("cluster")[["filtered", "not_filtered"]].sum()
table_dt = cluster_agg.values.tolist()
print("Framework A contingency table:")
print(cluster_agg)
v_dt, chi2_dt, p_dt, dof_dt = cramers_v(table_dt)
print(
    f"Cramér's V (A): {v_dt:.4f}, chi2: {chi2_dt:.2f}, dof: {dof_dt}, p: {p_dt:.2e}\n"
)


# ---------- FRAMEWORK B: source vs rest, mobility vs rest ----------
def or_table(
    df, cols, total_filtered=total_filtered, total_not_filtered=total_not_filtered
):
    results = []
    variable = " x ".join(cols)

    for _, row in df.iterrows():
        a, b = row["filtered"], row["not_filtered"]
        c = total_filtered - a
        d = total_not_filtered - b

        level = "/".join([str(row[c]) for c in cols])

        results.append(
            {
                "variable": variable,
                "level": level,
                "n": a + b,
                "odds_ratio": odds_ratio(a, b, c, d),
            }
        )
    return results


local_agg = df.groupby("scale")[["filtered", "not_filtered"]].sum().reset_index()

results_b = or_table(local_agg, ["scale"])

mobility_agg = df.groupby("mobility")[["filtered", "not_filtered"]].sum()

results_b.extend(or_table(mobility_agg.reset_index(), ["mobility"]))

# also the four scale x mobility cells directly, since that's where your interaction lives
combo_agg = df.groupby(["scale", "mobility"])[["filtered", "not_filtered"]].sum()
results_b.extend(or_table(combo_agg.reset_index(), ["scale", "mobility"]))


framework_b_ors = pd.DataFrame(results_b)
print("=== Framework B: scale, mobility, and scale x mobility vs rest ===")
print(framework_b_ors.to_string(index=False))
table_lm = combo_agg.values.tolist()
v_lm, chi2_lm, p_lm, dof_lm = cramers_v(table_lm)

print("Framework B contingency table:")
print(combo_agg)
print(
    f"Cramér's V (B): {v_lm:.4f}, chi2: {chi2_lm:.2f}, dof: {dof_lm}, p: {p_lm:.2e}\n"
)
print()

# ---------- Combined odds ratios ----------
joint_agg = df.groupby(["scale", "mobility", "cluster"])[
    ["filtered", "not_filtered"]
].sum()

results_joint = or_table(joint_agg.reset_index(), ["scale", "mobility", "cluster"])
joint_ors = pd.DataFrame(results_joint)
print("=== Joint: scale, mobility, and scale x mobility vs rest ===")
print(joint_ors.to_string(index=False))

table_lm = joint_agg.values.tolist()
v_lm, chi2_lm, p_lm, dof_lm = cramers_v(table_lm)
print(
    f"Cramér's V (Joint): {v_lm:.4f}, chi2: {chi2_lm:.2f}, dof: {dof_lm}, p: {p_lm:.2e}\n"
)
print()
# ---------- Flag separation / near-zero-cell issues ----------
print("=== Cells with 0 or near-0 in either filtered/not_filtered (unreliable OR) ===")
flagged = df[(df["filtered"] == 0) | (df["not_filtered"] == 0)]
print(flagged.to_string(index=False))
