# -*- coding: utf-8 -*-
"""
assumptions_checker.py
Pre-flight diagnostics for statistical tests: normality & homogeneity of variance.
"""
import numpy as np
import scipy.stats as stats

def check_normality(data, alpha=0.05):
    """
    Performs Shapiro-Wilk test for normality.
    If sample size is large (n >= 30), CLT applies, making parametric tests robust.
    """
    n = len(data)
    if n < 3:
        return {
            "normal": True,
            "shapiro_normal": True,
            "p_value": 1.0,
            "statistic": 1.0,
            "note": "Sample size too small to test normality (n < 3); assuming normal."
        }
    
    stat, p = stats.shapiro(data)
    is_normal = p >= alpha
    
    note = "Normally distributed (p = {:.4f} >= alpha)." if is_normal else "Normality assumption rejected (p = {:.4f} < alpha)."
    note = note.format(p)
    if n >= 30:
        note += f" However, sample size n = {n} >= 30, so Central Limit Theorem (CLT) applies."
        
    return {
        "normal": is_normal or (n >= 30),
        "shapiro_normal": is_normal,
        "p_value": p,
        "statistic": stat,
        "note": note
    }

def check_homogeneity(group_a, group_b, alpha=0.05):
    """
    Performs Levene's test for equality of variances.
    """
    stat, p = stats.levene(group_a, group_b)
    equal_var = p >= alpha
    note = "Equal variances (p = {:.4f} >= alpha)." if equal_var else "Variances are significantly different (p = {:.4f} < alpha)."
    
    return {
        "equal_var": equal_var,
        "p_value": p,
        "statistic": stat,
        "note": note.format(p)
    }

def analyze_assumptions(group_a, group_b, alpha=0.05):
    """
    Comprehensive diagnostics checker. Recommends the appropriate test based on results.
    """
    norm_a = check_normality(group_a, alpha)
    norm_b = check_normality(group_b, alpha)
    homo = check_homogeneity(group_a, group_b, alpha)
    
    norm_ok = norm_a["normal"] and norm_b["normal"]
    
    if norm_ok:
        if homo["equal_var"]:
            recommended_test = "Student's T-test (Equal Variances)"
        else:
            recommended_test = "Welch's T-test (Unequal Variances)"
    else:
        recommended_test = "Mann-Whitney U Test (Non-parametric alternative)"
        
    return {
        "group_a_normality": norm_a,
        "group_b_normality": norm_b,
        "variance_equality": homo,
        "recommended_test": recommended_test
    }
