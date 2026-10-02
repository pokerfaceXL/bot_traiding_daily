#!/usr/bin/env python3
"""
F006 shared-losing-months diagnostic (H-CATALOG5-SHARED-LOSING-MONTHS-01).

Tests whether Train-1 losing months are common across FREEZE catalog5 names
(basket regime) or idiosyncratic per name/symbol. Reads existing autopsy monthly
tables, applies pre-declared falsification criteria.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.stats import pearsonr
from itertools import combinations


def load_monthly_data():
    """Load monthly tables for all catalog5 names."""
    base = Path("output")
    
    files = {
        "BB_20_25_EMA200": base / "f006_catalog5_dual_autopsy/monthly/BB_20_25_EMA200_monthly.csv",
        "EMA_50_200": base / "f006_catalog5_dual_autopsy/monthly/EMA_50_200_monthly.csv",
        "EMA3_21_50_200": base / "f006_catalog5_trio_autopsy/monthly/EMA3_21_50_200_monthly.csv",
        "EMA3_13_50_200": base / "f006_catalog5_trio_autopsy/monthly/EMA3_13_50_200_monthly.csv",
        "BB_20_2_EMA200": base / "f006_catalog5_trio_autopsy/monthly/BB_20_2_EMA200_monthly.csv",
    }
    
    data = {}
    for name, filepath in files.items():
        df = pd.read_csv(filepath)
        df['month'] = pd.to_datetime(df['month'])
        data[name] = df
    
    return data


def load_donchian_monthly():
    """Load optional Donchian panel."""
    filepath = Path("output/f006_donchian_autopsy/donchian55_notrail_monthly.csv")
    df = pd.read_csv(filepath)
    df['month'] = pd.to_datetime(df['month'])
    return df


def build_loss_matrix(monthly_data):
    """Build month × name binary loss matrix L[m,n] = 1 iff net < 0."""
    # Get all months (should be 12 for Train-1)
    all_months = sorted(set().union(*[set(df['month']) for df in monthly_data.values()]))
    
    names = list(monthly_data.keys())
    loss_matrix = pd.DataFrame(index=all_months, columns=names, dtype=int)
    net_matrix = pd.DataFrame(index=all_months, columns=names, dtype=float)
    
    for name, df in monthly_data.items():
        for _, row in df.iterrows():
            month = row['month']
            loss_matrix.loc[month, name] = 1 if row['loss_m'] else 0
            net_matrix.loc[month, name] = row['net']
    
    return loss_matrix, net_matrix


def compute_cooccurrence(loss_matrix):
    """Count months with ≥k/5 names losing for k in {3,4,5}."""
    # Sum across names for each month
    losses_per_month = loss_matrix.sum(axis=1)
    
    results = {}
    for k in [3, 4, 5]:
        months_with_k_or_more = (losses_per_month >= k).sum()
        months_list = loss_matrix.index[losses_per_month >= k].tolist()
        results[f"ge_{k}_of_5"] = {
            "count": int(months_with_k_or_more),
            "months": [m.strftime('%Y-%m') for m in months_list]
        }
    
    return results, losses_per_month


def compute_pairwise_correlation(net_matrix):
    """Compute pairwise Pearson correlation of month-net across names."""
    names = list(net_matrix.columns)
    pairs = list(combinations(names, 2))
    
    correlations = []
    for name1, name2 in pairs:
        r, _ = pearsonr(net_matrix[name1], net_matrix[name2])
        correlations.append({
            "pair": f"{name1} vs {name2}",
            "correlation": float(r)
        })
    
    mean_corr = np.mean([c['correlation'] for c in correlations])
    return correlations, float(mean_corr)


def compute_phi_coefficient(loss_matrix):
    """Compute pairwise phi coefficient of loss flags."""
    names = list(loss_matrix.columns)
    pairs = list(combinations(names, 2))
    
    phi_values = []
    for name1, name2 in pairs:
        # 2x2 contingency table
        both_loss = ((loss_matrix[name1] == 1) & (loss_matrix[name2] == 1)).sum()
        n1_only = ((loss_matrix[name1] == 1) & (loss_matrix[name2] == 0)).sum()
        n2_only = ((loss_matrix[name1] == 0) & (loss_matrix[name2] == 1)).sum()
        neither = ((loss_matrix[name1] == 0) & (loss_matrix[name2] == 0)).sum()
        
        # Phi = (ad - bc) / sqrt((a+b)(c+d)(a+c)(b+d))
        a, b, c, d = both_loss, n1_only, n2_only, neither
        numerator = a * d - b * c
        denominator = np.sqrt((a + b) * (c + d) * (a + c) * (b + d))
        
        if denominator == 0:
            phi = 0.0
        else:
            phi = numerator / denominator
        
        phi_values.append({
            "pair": f"{name1} vs {name2}",
            "phi": float(phi)
        })
    
    mean_phi = np.mean([p['phi'] for p in phi_values])
    return phi_values, float(mean_phi)


def compute_jaccard_similarity(loss_matrix):
    """Compute pairwise Jaccard similarity of losing-month sets."""
    names = list(loss_matrix.columns)
    pairs = list(combinations(names, 2))
    
    jaccard_values = []
    for name1, name2 in pairs:
        losing_months_1 = set(loss_matrix.index[loss_matrix[name1] == 1])
        losing_months_2 = set(loss_matrix.index[loss_matrix[name2] == 1])
        
        intersection = len(losing_months_1 & losing_months_2)
        union = len(losing_months_1 | losing_months_2)
        
        if union == 0:
            jaccard = 0.0
        else:
            jaccard = intersection / union
        
        jaccard_values.append({
            "pair": f"{name1} vs {name2}",
            "jaccard": float(jaccard)
        })
    
    mean_jaccard = np.mean([j['jaccard'] for j in jaccard_values])
    return jaccard_values, float(mean_jaccard)


def compute_chance_baseline(loss_matrix, n_simulations=10000):
    """
    Compute chance baseline: expected #months with ≥4/5 names losing
    under independent names with each name's empirical p_loss.
    """
    names = list(loss_matrix.columns)
    n_months = len(loss_matrix)
    
    # Empirical loss probabilities
    p_loss = {name: (loss_matrix[name] == 1).sum() / n_months for name in names}
    
    # Monte Carlo simulation
    rng = np.random.RandomState(42)
    months_ge4_counts = []
    
    for _ in range(n_simulations):
        simulated_matrix = pd.DataFrame(index=loss_matrix.index, columns=names, dtype=int)
        for name in names:
            simulated_matrix[name] = rng.binomial(1, p_loss[name], n_months)
        
        losses_per_month = simulated_matrix.sum(axis=1)
        months_ge4_counts.append((losses_per_month >= 4).sum())
    
    expected_ge4 = np.mean(months_ge4_counts)
    std_ge4 = np.std(months_ge4_counts)
    
    return {
        "p_loss": {name: float(p) for name, p in p_loss.items()},
        "expected_months_ge4": float(expected_ge4),
        "std_months_ge4": float(std_ge4),
        "n_simulations": n_simulations
    }


def analyze_donchian(donchian_df, loss_matrix, losses_per_month):
    """Analyze Donchian correlation with catalog5 majority-loss months."""
    # Get months where ≥3 catalog5 names lost
    majority_loss_months = loss_matrix.index[losses_per_month >= 3]
    
    # Match with Donchian
    donchian_loss = donchian_df.set_index('month')['loss_m']
    
    overlap = []
    for month in majority_loss_months:
        if month in donchian_loss.index:
            donchian_lost = donchian_loss.loc[month]
            overlap.append(int(donchian_lost))
    
    agreement_rate = np.mean(overlap) if overlap else 0.0
    
    return {
        "catalog5_majority_loss_months": len(majority_loss_months),
        "donchian_also_lost": sum(overlap),
        "agreement_rate": float(agreement_rate)
    }


def apply_falsification_criteria(observed_ge4, expected_ge4, mean_phi, mean_net_corr, mean_jaccard):
    """Apply pre-declared falsification criteria (a)(b)(c)."""
    criteria = {}
    
    # (a) observed ≤ expected (observed - expected ≤ 0)
    criteria['a_months_above_chance'] = {
        "observed_ge4": observed_ge4,
        "expected_ge4": expected_ge4,
        "observed_minus_expected": observed_ge4 - expected_ge4,
        "tripped": (observed_ge4 - expected_ge4) <= 0
    }
    
    # (b) mean phi ≤ 0.10 AND mean corr ≤ 0.20
    criteria['b_low_association'] = {
        "mean_phi": mean_phi,
        "mean_net_corr": mean_net_corr,
        "tripped": (mean_phi <= 0.10 and mean_net_corr <= 0.20)
    }
    
    # (c) mean Jaccard ≤ 0.35
    criteria['c_low_jaccard'] = {
        "mean_jaccard": mean_jaccard,
        "tripped": mean_jaccard <= 0.35
    }
    
    any_tripped = any(c['tripped'] for c in criteria.values())
    verdict = "FALSIFIED" if any_tripped else "CONFIRMED"
    
    return criteria, verdict


def main():
    # Setup
    output_dir = Path("output/f006_shared_losing_months")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading monthly data...")
    monthly_data = load_monthly_data()
    donchian_df = load_donchian_monthly()
    
    # Build matrices
    print("Building loss matrix...")
    loss_matrix, net_matrix = build_loss_matrix(monthly_data)
    
    # Save matrices
    loss_matrix.to_csv(output_dir / "loss_matrix.csv")
    net_matrix.to_csv(output_dir / "net_matrix.csv")
    
    # Compute metrics
    print("Computing co-occurrence...")
    cooccurrence, losses_per_month = compute_cooccurrence(loss_matrix)
    
    print("Computing pairwise correlations...")
    net_correlations, mean_net_corr = compute_pairwise_correlation(net_matrix)
    
    print("Computing phi coefficients...")
    phi_values, mean_phi = compute_phi_coefficient(loss_matrix)
    
    print("Computing Jaccard similarities...")
    jaccard_values, mean_jaccard = compute_jaccard_similarity(loss_matrix)
    
    print("Computing chance baseline...")
    chance_baseline = compute_chance_baseline(loss_matrix)
    
    print("Analyzing Donchian panel...")
    donchian_analysis = analyze_donchian(donchian_df, loss_matrix, losses_per_month)
    
    # Apply falsification
    observed_ge4 = cooccurrence['ge_4_of_5']['count']
    expected_ge4 = chance_baseline['expected_months_ge4']
    
    criteria, verdict = apply_falsification_criteria(
        observed_ge4, expected_ge4, mean_phi, mean_net_corr, mean_jaccard
    )
    
    # Compile results
    results = {
        "train_period": "2024-03 to 2025-02 (12 months)",
        "catalog5_names": list(monthly_data.keys()),
        "cooccurrence": cooccurrence,
        "pairwise_net_correlations": {
            "mean": mean_net_corr,
            "values": net_correlations
        },
        "pairwise_phi_coefficients": {
            "mean": mean_phi,
            "values": phi_values
        },
        "pairwise_jaccard_similarity": {
            "mean": mean_jaccard,
            "values": jaccard_values
        },
        "chance_baseline": chance_baseline,
        "donchian_panel": donchian_analysis,
        "falsification_criteria": criteria,
        "verdict": verdict
    }
    
    # Save results
    with open(output_dir / "summary.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n" + "=" * 60)
    print("F006 SHARED-LOSING-MONTHS DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print(f"\nVerdict: {verdict}")
    print(f"\nObserved months with ≥4/5 names losing: {observed_ge4}")
    print(f"Expected (chance baseline): {expected_ge4:.2f}")
    print(f"Observed - Expected: {observed_ge4 - expected_ge4:.2f}")
    print(f"\nMean pairwise phi (loss flags): {mean_phi:.4f}")
    print(f"Mean pairwise Pearson r (month-net): {mean_net_corr:.4f}")
    print(f"Mean Jaccard (losing-month sets): {mean_jaccard:.4f}")
    print(f"\nFalsification criteria:")
    print(f"  (a) months ≤ chance: {criteria['a_months_above_chance']['tripped']}")
    print(f"  (b) low association: {criteria['b_low_association']['tripped']}")
    print(f"  (c) low Jaccard: {criteria['c_low_jaccard']['tripped']}")
    print(f"\nOutputs written to: {output_dir}")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()
