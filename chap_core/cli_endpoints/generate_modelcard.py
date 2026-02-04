import json
from pathlib import Path
from typing import Annotated

import yaml
from cyclopts import Parameter


from chap_core.assessment.evaluation import Evaluation
from chap_core.assessment.metrics.crps_norm import DetailedCRPSNorm
from chap_core.assessment.metrics.percentile_coverage import IsWithin25th75thDetailed

from chap_core.external.model_configuration import ModelTemplateConfigV2

import xarray as xr
from fpdf import FPDF
from chap_core.assessment.metrics import compute_all_aggregated_metrics_from_backtest
from chap_core.plotting.evaluation_plot import MetricByTimePeriodV2Mean, make_plot_from_backtest_object
from chap_core.assessment.metrics.rmse import DetailedRMSE



def generate_modelcard(evaluation_path: Annotated[
        Path,
        Parameter(
            help="Path to NetCDF file containing evaluation"
        ),
    ],run_path: Annotated[
        Path,
        Parameter(
            help="Path to folder containing information about run"
        ),
    ],
    
    
    ):
    """
    Generates a modelcard based on available information and produces a pdf.
    """

    ds = xr.open_dataset(evaluation_path)

    model_name = ds.attrs.get("model_name")
    if model_name is None:
        model_name = input("Enter the name of the model: ")

    

    model_config = ds.attrs.get("model_configuration")

    print(model_config)

    model_version = ds.attrs.get("model_version")

    model_source_url = ds.attrs.get("source_url")

    chap_version = ds.attrs.get("chap_version")

    org_units_json = json.loads(ds.attrs.get("org_units"))
    split_periods = json.loads(ds.attrs.get("split_periods"))
    historical_context_periods = ds.attrs.get("historical_context_periods")
    created_date = ds.attrs.get("created_date")





    eval = Evaluation.from_file(evaluation_path)


    
    config = ModelTemplateConfigV2.model_validate(yaml.safe_load(open(run_path / "MLproject" ).read()))
    
    meta_data = config.meta_data


    supported_period_type = config.supported_period_type

    required_covariates = config.required_covariates

    allow_free_covs = config.allow_free_additional_continuous_covariates


    backTest = eval._backtest
    


    detailedRMSE_plot = make_plot_from_backtest_object(backTest, MetricByTimePeriodV2Mean, DetailedRMSE()).plot(title="RMSE")
    detailedRMSE_plot.save("detailedRMSE_plot.png", scale_factor=2.0)

    IsWithin25th75thDetailed_plot = make_plot_from_backtest_object(backTest, MetricByTimePeriodV2Mean, IsWithin25th75thDetailed()).plot(title="Within 25-75 Percentile")
    IsWithin25th75thDetailed_plot.save("isWithin25th75hDetailed_plot.png", scale_factor=2.0)

    detailedCRPSNorm_plot = make_plot_from_backtest_object(backTest, MetricByTimePeriodV2Mean, DetailedCRPSNorm()).plot(title="Detailed CRPSE Normalized")
    detailedCRPSNorm_plot.save("detailedCRPSNorm.png", scale_factor=2.0)

    all_aggregated_metrics = compute_all_aggregated_metrics_from_backtest(backTest)


    results_summary = "\n".join(
        [
            f"RMSE (aggregate): {(all_aggregated_metrics.get('rmse_aggregate'))}",
            f"MAE (aggregate): {all_aggregated_metrics.get('mae_aggregate')}",
            f"CRPS: {all_aggregated_metrics.get('crps')}",
            f"Coverage within 10-90%: {all_aggregated_metrics.get('ratio_within_10th_90th')}",
            f"Coverage within 25-75%: {all_aggregated_metrics.get('ratio_within_25th_75th')}",
            f"Test sample count: {all_aggregated_metrics.get('test_sample_count')}",
        ]
    )
    

    class PDF(FPDF):

        def footer(self):
            # Position cursor at 1.5 cm from bottom:
            self.set_y(-15)
            # Setting font: helvetica italic 8
            self.set_font("helvetica", style="I", size=8)
            # Printing page number:
            self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


        
    
    pdf = PDF()
    pdf.add_page()

    pdf.set_font('helvetica', size=20)
    pdf.cell(text=f"Model card for: {meta_data.display_name}", new_x="LMARGIN", new_y="NEXT", center=True)
    pdf.ln(h=10)
  
    pdf.start_section("Model details", level=0)
    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Model details", new_x="LMARGIN", new_y="NEXT", w=0)
    pdf.ln(h=5)
    pdf.set_left_margin(pdf.l_margin + 10)

    pdf.set_font('helvetica', size=15)
    pdf.cell(text="Model Description", new_x="LMARGIN", new_y="NEXT")
    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=12)

    #Model version not in huggingface template, but i believe it´s useful for version comparison as according to originial modelcard paper.
    pdf.multi_cell(text=f"""Developed by: {meta_data.author}
    \nFunded by [optional]:
    \nShared by [optional]: 
    \nModel type: 
    \nModel version: {model_version} 
    \nLicense: 
    \nFinetuned from model [optional]: \n"""
    , new_x="LMARGIN"
    , new_y="NEXT"
    , w=0)
    

    pdf.set_font('helvetica', size=15)
    pdf.set_left_margin(pdf.l_margin - 10)
    pdf.cell(text="Model Sources [optional]", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', size=12)
    pdf.set_left_margin(pdf.l_margin + 10)

    pdf.multi_cell(text=f"""\nRepository: {model_source_url}
    \nPaper [optional]: 
    \nDemo [optional]: \n"""
    , new_x="LMARGIN"
    , new_y="NEXT"
    , w=0)
    pdf.set_left_margin(pdf.l_margin - 20)

    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Uses", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=12)
    pdf.multi_cell(text="""\nDirect Use: 
    \nDownstream Use [optional]: 
    \nOut-of-scope Use: \n"""
    , new_x="LMARGIN"
    , new_y="NEXT"
    , w=0)

    pdf.set_left_margin(pdf.l_margin - 10)

    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Bias, Risks and Limitations", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=12)
    pdf.multi_cell(text="\nRecommendations: \n", new_x="LMARGIN", new_y="NEXT", w=0)

    #Should be a "How to get started with the model" section here according to HuggingFace template, but this is probably unnecessary since this is covered previously?
    pdf.set_left_margin(pdf.l_margin - 10)
    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Training details", new_x="LMARGIN", new_y="NEXT")
    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=15)
    pdf.cell(text="Training data: ", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', size=12)
    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.multi_cell(
        text=(
            f"Created date: {created_date}\n"
            f"Number of Organization units: {len(org_units_json)}\n"
            f"Supported period type: {supported_period_type._value_}\n"
            f"Required covariates: {', '.join(required_covariates)}\n"
            f"Allow free additional covariates: {allow_free_covs}\n"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
        w=0,
        align="L",
    )


    pdf.set_left_margin(pdf.l_margin - 10)
    pdf.set_font('helvetica', size=15)
    pdf.cell(text="Training procedure: ", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('helvetica', size=12)
    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.multi_cell(
        text=(
            f"Splitting historical data into multiple train/test sets using rolling-origin backtesting\n"
            f"Split periods: {', '.join(split_periods)}\n"
            f"Historical context periods: {historical_context_periods}\n"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
        w=0,
        align="L",
    )
    pdf.cell(text="Preprocessing [optional]: ", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Training Hyperparameters: ", new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(text="* Training regime: ", new_x="LMARGIN", new_y="NEXT", w=0, align="L")
    pdf.cell(text="Speeds, Sizes, Times [optional]: ", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin - 20)
    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Evaluation", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=15)
    pdf.cell(text="Testing Data, Factors & Metrics", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=12)
    pdf.cell(text="Testing Data: ", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Factors: ", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Metrics: ", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="RMSE", new_x="LMARGIN", new_y="NEXT")
    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.cell(text=f"RMSE aggregate value: {all_aggregated_metrics.get("rmse_aggregate")}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text=f"Detailed RMSE plot", new_x="LMARGIN", new_y="NEXT")
    pdf.image("detailedRMSE_plot.png", w=125)

    pdf.cell(text=f"Within 25-75 Percentile", new_x="LMARGIN", new_y="NEXT")
    pdf.image("isWithin25th75hDetailed_plot.png", w=125)

    pdf.cell(text=f"Detailed CRPS Normalized", new_x="LMARGIN", new_y="NEXT")
    pdf.image("detailedCRPSNorm.png", w=125)

    pdf.set_left_margin(pdf.l_margin - 20)
    pdf.set_font('helvetica', size=15)
    pdf.cell(text="Results: ", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=12)
    pdf.cell(text="Summary: ", new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(
        text=results_summary,
        new_x="LMARGIN",
        new_y="NEXT",
        w=0,
        align="L",
    )
    

    pdf.set_left_margin(pdf.l_margin - 20)
    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Model examination [optional]: ", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Environmental impact: ", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=12)
    pdf.cell(text="Hardware type: ", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Hours used: ", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Cloud Provider: ", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Compute Region: ", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Carbon emitteds: ", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin - 10)
    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Technical specifications [optional]", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=15)
    pdf.cell(text="Model Architecture and Objective", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(text="Compute Infrastructure", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=12)
    pdf.multi_cell(text=(
        f"Hardware: \n"
        f"Software: \n"
        )
    , new_x="LMARGIN"
    , new_y="NEXT"
    , w=0)
    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.cell(text=f"CHAP version: {chap_version}", new_x="LMARGIN", new_y="NEXT")


    pdf.set_left_margin(pdf.l_margin - 30)
    pdf.set_font('helvetica', size=20)
    pdf.cell(text="Citation [optional]", new_x="LMARGIN", new_y="NEXT")

    pdf.set_left_margin(pdf.l_margin + 10)
    pdf.set_font('helvetica', size=12)
    pdf.multi_cell(text=f"""BibTeX:
    \nAPA: \n"""
    , new_x="LMARGIN"
    , new_y="NEXT"
    , w=0)

    # Added based on metadata format:
    pdf.multi_cell(
        text=meta_data.citation_info,
        new_x="LMARGIN",
        new_y="NEXT",
        w=0,
        align="L",
    )
    

    pdf.set_left_margin(pdf.l_margin - 10)

    pdf.set_font('helvetica', size=20)
    pdf.multi_cell(text="Glossary [optional]\n", new_x="LMARGIN", new_y="NEXT", w=0)

    pdf.multi_cell(text="More information [optional]\n", new_x="LMARGIN", new_y="NEXT", w=0)

    pdf.multi_cell(text="Model Card Authors [optional]\n", new_x="LMARGIN", new_y="NEXT", w=0)

    pdf.multi_cell(text="Model Card Contact \n", new_x="LMARGIN", new_y="NEXT", w=0)
    pdf.set_font_size(12)
    pdf.cell(text=f"Contact email: {meta_data.contact_email}", new_x="LMARGIN", new_y="NEXT")
    pdf.output("modelcard_test.pdf")

def register_commands(app):
    """Register evaluate commands with the CLI app."""
    app.command()(generate_modelcard)