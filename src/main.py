from afadl_26 import (
    align_raters,
    pairwise_kappas,
    class_distribution_summary,
    three_rater_agreement_summary,
    group_summary_by_field,
    plot_class_distribution,
    plot_unanimous_agreement_by_class,
    plot_agreement_patterns,
    make_pair_weight_matrix
)



def main():
    
    labels = [1, 2, 3, 4]
    
    custom_weights = make_pair_weight_matrix(
    labels=labels,
    penalties={
        (1, 3): 0.25,
        (2, 4): 0.25,
    },
    default_penalty=1.0,
    )
    
    aligned = align_raters(
    {
        "human_1": "src/data/AFADL_EXP_ACH.csv",
        "human_2": "src/data/AFADL_EXP_DTA.csv",
        "llm_rater": "src/data/AFADL_EXP_GPT.csv",
    },
    delimiter=";",
    has_header=True,
    
    )

    print("Common items:", aligned["n_common"])

    # Pairwise kappas
    pairwise = pairwise_kappas(aligned, labels=labels, weight_scheme="quadratic", weight_matrix=custom_weights)
    for pair, result in pairwise.items():
        print(f"{pair}: kappa={result['kappa']:.4f}")

    # Agreement summary
    summary = three_rater_agreement_summary(aligned)
    print("All 3 agree:", summary["all_agree_count"])
    print("All 3 agree by class:", summary["all_agree_by_class"])
    print("Exactly 2 agree:", summary["exactly_two_agree_count"])
    print("All different:", summary["all_different_count"])

    print("When humans agree:", summary["human_human_agree_total"])
    print("  LLM matches them:", summary["human_agree_llm_matches_total"])
    print("  LLM disagrees:", summary["human_agree_llm_disagrees_total"])

    print("When humans disagree:", summary["human_human_disagree_total"])
    print("  LLM sides with human_1:", summary["human_disagree_llm_sides_h1_total"])
    print("  LLM sides with human_2:", summary["human_disagree_llm_sides_h2_total"])
    print("  LLM sides with neither:", summary["human_disagree_llm_sides_neither_total"])

    # Distribution summary
    dist = class_distribution_summary(aligned)
    print("Class counts per rater:")
    for rater, counts in dist["counts"].items():
        print(rater, counts)

    # By model
    by_model = group_summary_by_field(aligned, field="model")
    print("\nAgreement by model:")
    for model, stats in by_model.items():
        print(model, stats["all_agree_count"], stats["all_agree_rate"])
        
    # By requirement/specification
    by_spec = group_summary_by_field(aligned, field="specification")
    print("\nAgreement by specification:")
    for spec, stats in by_spec.items():
        print(spec, stats["all_agree_count"], stats["all_agree_rate"])
    # Plots
    plot_class_distribution(aligned, normalize=False, save_path="class_distribution_counts.png")
    plot_class_distribution(aligned, normalize=True, save_path="class_distribution_props.png")
    plot_unanimous_agreement_by_class(aligned, save_path="all3_agree_by_class.png")
    plot_agreement_patterns(aligned, save_path="agreement_patterns.png")


if __name__ == "__main__":
    main()
