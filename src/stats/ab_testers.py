# -*- coding: utf-8 -*-
"""
ab_testers.py
Hypothesis testing calculations for A/B tests (Z-test, T-test, Mann-Whitney U, Chi-Square).
"""
import numpy as np
import scipy.stats as stats

def run_proportion_z_test(x_a, n_a, x_b, n_b, alpha=0.05, alternative="two-sided"):
    """
    Two-Sample Z-Test for Proportions (A/B testing conversion rates).
    """
    p_a = x_a / n_a
    p_b = x_b / n_b
    
    p_pooled = (x_a + x_b) / (n_a + n_b)
    se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_a + 1/n_b))
    
    z_stat = (p_b - p_a) / se if se > 0 else 0.0
    
    if alternative == "two-sided":
        p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    elif alternative == "greater":
        p_val = 1 - stats.norm.cdf(z_stat)
    else:
        p_val = stats.norm.cdf(z_stat)
        
    # Confidence Interval for difference (p_b - p_a)
    z_crit = stats.norm.ppf(1 - alpha/2)
    diff = p_b - p_a
    se_diff = np.sqrt((p_a*(1-p_a)/n_a) + (p_b*(1-p_b)/n_b))
    margin_error = z_crit * se_diff
    ci_lower = diff - margin_error
    ci_upper = diff + margin_error
    odds_a = x_a / (n_a - x_a) if (n_a - x_a) > 0 else np.inf
    odds_b = x_b / (n_b - x_b) if (n_b - x_b) > 0 else np.inf
    odds_ratio = odds_b / odds_a if odds_a not in [0, np.inf] else np.inf
    
    reject_h0 = p_val < alpha
    
    return {
        "test_name": "Two-Sample Z-Test for Proportions",
        "group_a": {"n": n_a, "successes": x_a, "rate": p_a},
        "group_b": {"n": n_b, "successes": x_b, "rate": p_b},
        "difference": diff,
        "risk_difference": diff,
        "odds_ratio": odds_ratio,
        "effect_size_label": "Risk difference",
        "effect_size_value": diff,
        "effect_size_note": f"Odds ratio = {odds_ratio:.4f}",
        "statistic": z_stat,
        "p_value": p_val,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "reject_h0": reject_h0,
        "alternative": alternative,
        "alpha": alpha,
        "formulas": {
            "hypothesis": r"H_0: p_A = p_B \quad H_a: p_A \neq p_B",
            "pooled_prop": r"p_{pooled} = \frac{x_A + x_B}{n_A + n_B} = " + f"{p_pooled:.4f}",
            "se": r"SE = \sqrt{p_{pooled}(1-p_{pooled})(\frac{1}{n_A} + \frac{1}{n_B})} = " + f"{se:.4f}",
            "z_stat": r"Z = \frac{\hat{p}_B - \hat{p}_A}{SE} = " + f"{z_stat:.4f}",
            "ci": r"CI = (\hat{p}_B - \hat{p}_A) \pm Z_{crit} \times SE_{diff} = " + f"({ci_lower:.4f}, {ci_upper:.4f})"
        }
    }

def run_means_t_test(group_a, group_b, alpha=0.05, equal_var=True, alternative="two-sided"):
    """
    Two-Sample T-Test for Means (A/B testing revenue, session duration).
    """
    n_a = len(group_a)
    n_b = len(group_b)
    
    mean_a = np.mean(group_a)
    mean_b = np.mean(group_b)
    
    var_a = np.var(group_a, ddof=1)
    var_b = np.var(group_b, ddof=1)
    
    # Run test (Note: stats.ttest_ind accepts group_a, group_b. We will test group_b - group_a)
    t_stat, p_val = stats.ttest_ind(group_b, group_a, equal_var=equal_var, alternative=alternative)
    
    diff = mean_b - mean_a
    pooled_sd_for_effect = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    cohens_d = diff / pooled_sd_for_effect if pooled_sd_for_effect > 0 else 0.0
    if equal_var:
        df = n_a + n_b - 2
        s_pooled = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / df)
        se = s_pooled * np.sqrt(1/n_a + 1/n_b)
    else:
        se = np.sqrt(var_a/n_a + var_b/n_b)
        numerator = (var_a/n_a + var_b/n_b)**2
        denominator = ((var_a/n_a)**2 / (n_a - 1)) + ((var_b/n_b)**2 / (n_b - 1))
        df = numerator / denominator if denominator > 0 else 1.0
        
    t_crit = stats.t.ppf(1 - alpha/2, df)
    margin_error = t_crit * se
    ci_lower = diff - margin_error
    ci_upper = diff + margin_error
    
    reject_h0 = p_val < alpha
    
    # Construct LaTeX formulas
    if equal_var:
        se_formula = r"s_{pooled} = \sqrt{\frac{(n_A-1)s_A^2 + (n_B-1)s_B^2}{n_A+n_B-2}} = " + f"{s_pooled:.4f}" + r"\quad SE = s_{pooled}\sqrt{\frac{1}{n_A} + \frac{1}{n_B}} = " + f"{se:.4f}"
    else:
        se_formula = r"SE = \sqrt{\frac{s_A^2}{n_A} + \frac{s_B^2}{n_B}} = " + f"{se:.4f}"

    return {
        "test_name": "Student's T-Test (Equal Variances)" if equal_var else "Welch's T-Test (Unequal Variances)",
        "group_a": {"n": n_a, "mean": mean_a, "variance": var_a, "std_dev": np.sqrt(var_a)},
        "group_b": {"n": n_b, "mean": mean_b, "variance": var_b, "std_dev": np.sqrt(var_b)},
        "difference": diff,
        "effect_size_label": "Cohen's d",
        "effect_size_value": cohens_d,
        "effect_size_note": "Standardized mean difference: Group B - Group A",
        "statistic": t_stat,
        "p_value": p_val,
        "degrees_of_freedom": df,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "reject_h0": reject_h0,
        "alternative": alternative,
        "alpha": alpha,
        "formulas": {
            "hypothesis": r"H_0: \mu_A = \mu_B \quad H_a: \mu_A \neq \mu_B",
            "se": se_formula,
            "t_stat": r"t = \frac{\bar{x}_B - \bar{x}_A}{SE} = " + f"{t_stat:.4f}",
            "df": f"df = {df:.2f}",
            "ci": r"CI = (\bar{x}_B - \bar{x}_A) \pm t_{crit} \times SE = " + f"({ci_lower:.4f}, {ci_upper:.4f})"
        }
    }

def run_mann_whitney_u_test(group_a, group_b, alpha=0.05, alternative="two-sided"):
    """
    Non-parametric alternative to Two-Sample T-test.
    """
    u_stat, p_val = stats.mannwhitneyu(group_b, group_a, alternative=alternative)
    
    n_a = len(group_a)
    n_b = len(group_b)
    
    median_a = np.median(group_a)
    median_b = np.median(group_b)
    rank_biserial = (2 * u_stat / (n_a * n_b)) - 1
    
    reject_h0 = p_val < alpha
    
    return {
        "test_name": "Mann-Whitney U Test (Non-parametric)",
        "group_a": {"n": n_a, "median": median_a},
        "group_b": {"n": n_b, "median": median_b},
        "difference": median_b - median_a,
        "effect_size_label": "Rank-biserial correlation",
        "effect_size_value": rank_biserial,
        "effect_size_note": "Non-parametric effect size based on the Mann-Whitney U statistic",
        "statistic": u_stat,
        "p_value": p_val,
        "reject_h0": reject_h0,
        "alternative": alternative,
        "alpha": alpha,
        "formulas": {
            "hypothesis": r"H_0: F_A(x) = F_B(x) \quad H_a: F_A(x) \neq F_B(x)",
            "u_stat": f"U_{{statistic}} = {u_stat:.1f}"
        }
    }

def run_chi_square_test(observed, alpha=0.05):
    """
    Chi-Square Test of Independence for categorical data.
    observed: 2D list or numpy array
    """
    chi2_stat, p_val, df, expected = stats.chi2_contingency(observed)
    observed_arr = np.asarray(observed)
    n = observed_arr.sum()
    min_dim = min(observed_arr.shape) - 1
    cramers_v = np.sqrt(chi2_stat / (n * min_dim)) if n > 0 and min_dim > 0 else 0.0
    
    reject_h0 = p_val < alpha
    
    return {
        "test_name": "Chi-Square Test of Independence",
        "observed": observed,
        "expected": expected.tolist(),
        "statistic": chi2_stat,
        "effect_size_label": "Cramer's V",
        "effect_size_value": cramers_v,
        "effect_size_note": "Association strength for categorical variables",
        "p_value": p_val,
        "degrees_of_freedom": df,
        "reject_h0": reject_h0,
        "alpha": alpha,
        "formulas": {
            "hypothesis": r"H_0: \text{Variables are independent} \quad H_a: \text{Variables are dependent}",
            "chi2_stat": r"\chi^2 = \sum \frac{(O - E)^2}{E} = " + f"{chi2_stat:.4f}",
            "df": f"df = {df}"
        }
    }

def run_one_way_anova(groups, group_names, alpha=0.05):
    """
    One-way ANOVA for comparing means across 3+ groups.
    groups: list of numeric arrays
    group_names: labels matching the groups list
    """
    f_stat, p_val = stats.f_oneway(*groups)
    all_values = np.concatenate(groups)
    grand_mean = np.mean(all_values)

    ss_between = sum(len(group) * (np.mean(group) - grand_mean) ** 2 for group in groups)
    ss_total = sum((value - grand_mean) ** 2 for value in all_values)
    eta_squared = ss_between / ss_total if ss_total > 0 else 0.0

    group_summaries = []
    for name, group in zip(group_names, groups):
        group_summaries.append({
            "name": name,
            "n": len(group),
            "mean": np.mean(group),
            "std_dev": np.std(group, ddof=1) if len(group) > 1 else 0.0,
            "variance": np.var(group, ddof=1) if len(group) > 1 else 0.0,
        })

    tukey_results = []
    try:
        from statsmodels.stats.multicomp import pairwise_tukeyhsd

        labels = np.concatenate([[name] * len(group) for name, group in zip(group_names, groups)])
        tukey = pairwise_tukeyhsd(endog=all_values, groups=labels, alpha=alpha)
        for row in tukey.summary().data[1:]:
            tukey_results.append({
                "group1": str(row[0]),
                "group2": str(row[1]),
                "mean_diff": float(row[2]),
                "p_adj": float(row[3]),
                "lower": float(row[4]),
                "upper": float(row[5]),
                "reject": bool(row[6]),
            })
    except Exception:
        tukey_results = []

    return {
        "test_name": "One-Way ANOVA",
        "group_summaries": group_summaries,
        "difference": max(summary["mean"] for summary in group_summaries) - min(summary["mean"] for summary in group_summaries),
        "statistic": f_stat,
        "p_value": p_val,
        "degrees_of_freedom": len(groups) - 1,
        "reject_h0": p_val < alpha,
        "alpha": alpha,
        "effect_size_label": "Eta-squared",
        "effect_size_value": eta_squared,
        "effect_size_note": "Proportion of outcome variance explained by group membership",
        "post_hoc": tukey_results,
        "formulas": {
            "hypothesis": r"H_0: \mu_1 = \mu_2 = \cdots = \mu_k \quad H_a: \text{At least one group mean differs}",
            "f_stat": f"F = {f_stat:.4f}",
            "eta_squared": r"\eta^2 = \frac{SS_{between}}{SS_{total}} = " + f"{eta_squared:.4f}",
        }
    }
