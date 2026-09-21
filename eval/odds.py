import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportion_confint

# Load data
df = pd.read_csv("output/eval/pmi/by_source_mobility_v2_cluster.csv")
df[["source", "formality", "cluster"]] = df.feature_value.str.split(" / ", n=2, expand=True)

# Remove LinCE data 
df.loc[df.source == "glowbe", "formality"] = "unknown (web)"

# Compute filtered and not-filtered values
def generate_response_labels(df):
    df["filtered"] = df["joint_count"]
    df["not_filtered"] = df["marginal_count"] - df["joint_count"]
    return


generate_response_labels(df)

# ---------- Flag separation / near-zero-cell issues ----------
print("=== Cells with 0 or near-0 in either filtered/not_filtered (unreliable OR) ===")
flagged = df[(df["filtered"] == 0) | (df["not_filtered"] == 0)]
print(flagged.to_string(index=False))

df = df.loc[(df["filtered"] != 0) | (df["not_filtered"] != 0)]


df.to_csv("output/eval/odds/or_input.csv")


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

def rate_ci(filtered, not_filtered, method="wilson", alpha=0.05):
    n = filtered + not_filtered
    p_hat = not_filtered / n 
    p_low, p_high = proportion_confint(count=not_filtered, nobs=n, alpha=alpha, method=method)
    ci_low = p_hat - p_low 
    ci_high = p_high - p_hat
    return p_hat, ci_low, ci_high 

def cluster_vs_rest(df, val):
    cluster_rows = df[df["cluster"] == val]
    rest_rows = df[df["cluster"] != val]

    a = cluster_rows["filtered"].sum()
    b = cluster_rows["not_filtered"].sum()
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
    retention_p, lo, hi = rate_ci(result[f"cluster_{comp}_filtered"], result[f"cluster_{comp}_not_filtered"])
    print(f"retention={retention_p:.4f}  95% CI=[{lo:.4f}, {hi:.4f}]")
    print()

cluster_agg = df.groupby("cluster")[["filtered", "not_filtered"]].sum()
table_dt = cluster_agg.values.tolist()
print("Framework A contingency table:")
print(cluster_agg)
v_dt, chi2_dt, p_dt, dof_dt = cramers_v(table_dt)
# print(
#     f"Cramér's V (A): {v_dt:.4f}, chi2: {chi2_dt:.2f}, dof: {dof_dt}, p: {p_dt:.2e}\n"
# )


# ---------- FRAMEWORK B: source vs rest, formality vs rest ----------
def or_table(
    df, cols, total_filtered=total_filtered, total_not_filtered=total_not_filtered
):
    results = []
    variable = " x ".join(cols)

    for _, row in df.iterrows():
        a, b = row["filtered"], row["not_filtered"]
        p1, lo1, hi1 = rate_ci(a, b)
        p2, lo2, hi2 = rate_ci(b, a)

        c = total_filtered - a
        d = total_not_filtered - b

        level = "/".join([str(row[c]) for c in cols])

        results.append(
            {
                "variable": variable,
                "level": level,
                "n": a + b,
                "odds_ratio": odds_ratio(a, b, c, d),
                "retention_p_hat": p1,
                "retention_low": lo1,
                "retention_high": hi1,
                "rejection_p_hat": p2,
                "rejection_low": lo2,
                "rejection_high": hi2
                # "pmi": row["pmi"]
            }
        )
    return results

formality_agg = df.groupby("formality")[["filtered", "not_filtered"]].sum()

results_b = (or_table(formality_agg.reset_index(), ["formality"]))

framework_b_ors = pd.DataFrame(results_b).sort_values(by="retention_p_hat")
print("=== Framework B: formality vs rest ===")
print(framework_b_ors.to_string(index=False))
framework_b_ors.to_csv("output/eval/odds/b_ors.csv", index=False)

table_lm = formality_agg.values.tolist()
# v_lm, chi2_lm, p_lm, dof_lm = cramers_v(table_lm)

print("Framework B contingency table:")
print(formality_agg)
# print(
#     f"Cramér's V (B): {v_lm:.4f}, chi2: {chi2_lm:.2f}, dof: {dof_lm}, p: {p_lm:.2e}\n"
# )
print()

# ---------- Combined odds ratios ----------
joint_agg = df.groupby(["source", "formality", "cluster"])[
    ["filtered", "not_filtered"]
].sum()

results_joint = or_table(joint_agg.reset_index(), ["source", "formality", "cluster"])
joint_ors = pd.DataFrame(results_joint).sort_values(by="level")
print("=== Joint: cluster x formality vs rest ===")
print(joint_ors.to_string(index=False))
joint_ors.to_csv("output/eval/odds/joint_ors.csv", index=False)
table_lm = joint_agg.values.tolist()
# v_lm, chi2_lm, p_lm, dof_lm = cramers_v(table_lm)
# print(
#     f"Cramér's V (Joint): {v_lm:.4f}, chi2: {chi2_lm:.2f}, dof: {dof_lm}, p: {p_lm:.2e}\n"
# )
print()


