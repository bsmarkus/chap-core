from pathlib import Path
import yaml
from chap_core.assessment.evaluation import Evaluation
from chap_core.assessment.metrics.crps_norm import CRPSNormMetric
from chap_core.assessment.metrics.percentile_coverage import Coverage25_75Metric
from chap_core.external.model_configuration import ModelTemplateConfigV2
from chap_core.assessment.metrics import compute_all_aggregated_metrics_from_backtest
from chap_core.plotting.evaluation_plot import MetricByTimePeriodV2Mean, make_plot_from_backtest_object
from chap_core.assessment.metrics.rmse import RMSEMetric
from chap_core.models.model_template import ModelTemplate

try:
    from chap_core import __version__ as CHAP_VERSION
except ImportError:
    CHAP_VERSION = "unknown"



def generate_modelcard2(evaluation: Evaluation, config: ModelTemplateConfigV2, output_file: Path):
    """
    Generates a modelcard based on available information and produces a pdf.
    """

    """ model_name = ds.attrs.get("model_name")
 """
    
    
    # Is this the same as?
    """ model_config = ds.attrs.get("model_configuration") """



    """ model_source_url = ds.attrs.get("source_url") """ # Was this even available in v1?

    output_dir = output_file.parent

    chap_version = CHAP_VERSION

    org_units = evaluation.get_org_units()
 
    split_periods = evaluation.get_split_periods()
    
    historical_context_periods = evaluation._historical_context_periods

    
    created_date = evaluation._backtest.created # same ase ds.attrs.get("created_date")???

    model_version = config.version
    
    meta_data = config.meta_data


    supported_period_type = config.supported_period_type

    required_covariates = config.required_covariates

    allow_free_covs = config.allow_free_additional_continuous_covariates


    backTest = evaluation._backtest
    


    detailedRMSE_plot = make_plot_from_backtest_object(backTest, MetricByTimePeriodV2Mean, RMSEMetric()).plot(title="RMSE")
    detailedRMSE_plot.save(f"{output_dir}/detailedRMSE_plot.png", scale_factor=2.0)

    IsWithin25th75thDetailed_plot = make_plot_from_backtest_object(backTest, MetricByTimePeriodV2Mean, Coverage25_75Metric()).plot(title="Within 25-75 Percentile")
    IsWithin25th75thDetailed_plot.save(f"{output_dir}/isWithin25th75hDetailed_plot.png", scale_factor=2.0)


    detailedCRPSNorm_plot = make_plot_from_backtest_object(backTest, MetricByTimePeriodV2Mean, CRPSNormMetric()).plot(title="Detailed CRPSE Normalized")
    detailedCRPSNorm_plot.save(f"{output_dir}/detailedCRPSNorm_plot.png", scale_factor=2.0)

    all_aggregated_metrics = compute_all_aggregated_metrics_from_backtest(backTest)


    results_summary = "\n".join(
        [   f"Ratio above truth: {(all_aggregated_metrics.get('ratio_above_truth'))}\n",
            f"CRPS: {all_aggregated_metrics.get('crps')}\n",
            f"CRPS Normalized: {all_aggregated_metrics.get('crps_norm')}\n",
            f"Example metric: {(all_aggregated_metrics.get('example_metric'))}\n",
            f"RMSE (aggregate): {(all_aggregated_metrics.get('rmse'))}\n",
            f"MAE (aggregate): {all_aggregated_metrics.get('mae')}\n",
            f"Coverage within 10-90%: {all_aggregated_metrics.get('coverage_10_90')}\n",
            f"Coverage within 25-75%: {all_aggregated_metrics.get('coverage_25_75')}\n",
            f"Sample count: {all_aggregated_metrics.get('sample_count')}\n",
        ]
    )


    output_path = output_file.with_suffix(".modelcard.md")
    
    #TODO add markdown comments as per huggingface modelcardtemplate?

    md: list[str] = []
    md.append(f"# Model card for: {meta_data.display_name or meta_data.display_name}")
    md.append("")
    if(meta_data.author_note):
        md.append(meta_data.author_note)

    md.append("## Model details")
    md.append("")

    md.append("### Model description")
    md.append("")
    if(meta_data.description):
        md.append(meta_data.description)
    md.append(f"- **Developed by:** {(meta_data.author or meta_data.organization) or 'More Information Needed'}".rstrip())
    md.append(f"- **Funded by [optional]:** More Information Needed".rstrip())
    md.append(f"- **Shared by [optional]:** More Information Needed".rstrip())
    md.append(f"- **Model type:** More Information Needed")
    md.append(f"- **License:** More Information Needed")
    md.append(f"- **Finetuned from model: [optional]** More information needed")

    md.append("### Model Sources [optional]")
    md.append("")
    md.append("- **Repository:** More information Needed")
    md.append("- **Paper [optional]:** More information Needed")
    md.append("- **Demo[optional]:** More information Needed")

    # find somewhere to put this?
    if chap_version:
        md.append(f"- **CHAP version:** `{chap_version}`")

    md.append("")
    md.append("## Uses")
    md.append("")
    md.append("### Direct use: ")
    md.append("### Downstream use (optional): ")
    md.append("### Out-of-scope use: ")
    md.append("")

    md.append("## Bias, Risks and Limitations")
    md.append("")
    md.append("### Recommendations: ")
    md.append("")

    md.append("## Training details")
    md.append("")
    md.append("### Training data")
    md.append("")
    md.append(f"- Created date: {created_date}")
    md.append(f"- Number of organization units: {len(org_units)}")
    md.append(f"- Supported period type: `{supported_period_type.value}`")
    md.append(f"- Required covariates: {', '.join(required_covariates)}")
    md.append(f"- Allow free additional covariates: `{allow_free_covs}`")
    md.append("")
    md.append("### Training procedure")
    md.append("")
    md.append("#### Preprocessing [optional]")
    md.append("- Splitting historical data into multiple train/test sets using rolling-origin backtesting")
    md.append(f"- Split periods: {', '.join(map(str, split_periods))}")
    md.append(f"- Historical context periods: {historical_context_periods}")
    md.append("")
    md.append("#### Training Hyperparameters")
    md.append("- **Training regime:**")
    md.append("#### Speeds, Sizes, Times [optional]")


    md.append("## Evaluation")
    md.append("")
    md.append("### Testing Data, Factors & Metrics")
    md.append("")
    md.append("#### Testing Data")
    md.append("")
    md.append("#### Factors")
    md.append("")
    md.append("#### Metrics")
    md.append("")
    md.append(results_summary)
    md.append("")
    md.append(f"#### RMSE by time period\n\n![RMSE by time](detailedRMSE_plot.png)\n")
    md.append(f"#### Coverage within 25–75% by time period\n\n![Coverage 25–75](isWithin25th75hDetailed_plot.png)\n")
    md.append(f"#### CRPS Normalized by time period\n\n![CRPS normalized](detailedCRPSNorm_plot.png)\n")
    md.append("### Results")
    md.append("")
    md.append("#### Summary")

    md.append("## Model examination [optional]")

    md.append("## Environmental Impact")
    md.append("")
    md.append("Carbon emissions can be estimated using the [Machine Learning Impact calculator](https://mlco2.github.io/impact#compute) presented in [Lacoste et al. (2019)](https://arxiv.org/abs/1910.09700).")
    md.append("- **Hardware Tpye:**")
    md.append("- **Hours used:**")
    md.append("- **Cloud Provider:**")
    md.append("- **Compute Region:**")
    md.append("- **Carbon Emitted:**")

    md.append("## Technical Specifications [optional]")
    md.append("")
    md.append("### Model Architecture and Objective")
    md.append("### Compute Infrastructure")
    md.append("#### Hardware")
    md.append("#### Software")
    
   
  




    md.append("## Citation [optional]")
    md.append("")
    md.append("**BibTeX:**")
    md.append("")
    md.append("**APA:**")
    md.append("")
    if meta_data.citation_info:
        md.append(meta_data.citation_info)

    md.append("## Glossary [optional]")
    md.append("")

    md.append("## More information [optional]")
    md.append("")

    md.append("## Model Card Authors [optional]")
    md.append("")

    md.append("## Model card contact")
    md.append("")
    if meta_data.contact_email:
        md.append(f"- Contact email: {meta_data.contact_email}")
    else:
        md.append("- Contact email: ")

    output_path.write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")

def generate_modelcard_from_path(eval_path: Path, run_path: Path):


    
    config = ModelTemplateConfigV2.model_validate(yaml.safe_load(open(f"{run_path}/MLproject" ).read()))
    
    generate_modelcard2(Evaluation.from_file(eval_path), config, eval_path)

def register_commands(app):
    app.command()(generate_modelcard_from_path)

