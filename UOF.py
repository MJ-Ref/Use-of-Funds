import streamlit as st
import pandas as pd
import plotly.express as px
from collections import OrderedDict
from pathlib import Path
import yaml
from pydantic import BaseModel, ValidationError, field_validator

# --- Constants
INITIAL_RUNWAY_MONTHS = 15
TARGET_RAISE_USD = 1_200_000

# --- Budget Data Ingestion & Validation -------------------------------------------------

class OptionalCostModel(BaseModel):
    cost_type: str
    cost_value: float
    category: str

    @field_validator("cost_type")
    @classmethod
    def validate_type(cls, v):
        if v not in {"monthly", "annual", "one_time"}:
            raise ValueError("cost_type must be 'monthly', 'annual', or 'one_time'")
        return v

    @field_validator("cost_value")
    @classmethod
    def positive_value(cls, v):
        if v < 0:
            raise ValueError("cost_value must be positive")
        return v

class BudgetModel(BaseModel):
    fixed_costs: dict[str, float]
    monthly_costs: dict[str, float]
    optional_costs: dict[str, OptionalCostModel]

    @field_validator("fixed_costs", "monthly_costs")
    @classmethod
    def validate_amounts(cls, v):
        for name, amt in v.items():
            if amt < 0:
                raise ValueError(f"{name} must have a positive amount")
        return v

# Locate YAML next to this script
yaml_path = Path(__file__).with_name("budget_data.yaml")
if not yaml_path.exists():
    st.error("budget_data.yaml not found – cannot load budget.")
    st.stop()

with yaml_path.open("r") as f:
    raw_budget = yaml.safe_load(f)

try:
    budget_data = BudgetModel(**raw_budget)
except ValidationError as e:
    st.error(f"Budget validation failed:\n{e}")
    st.stop()

# Expose validated dicts in the same variable names used downstream
fixed_costs_details = budget_data.fixed_costs
monthly_costs_details = budget_data.monthly_costs
optional_add_back_costs = {k: v.model_dump() for k, v in budget_data.optional_costs.items()}

# Software tools list for categorization (unchanged)
software_op_ex_monthly = [
    "Slack",
    "Notion",
    "Google Workspace",
    "Figma",
    "HubSpot CRM",
    "Gusto Payroll",
    "QuickBooks Accounting",
    "1Password Teams",
    "Misc IT/Security SaaS (Avg)",
]

def categorize_costs(monthly_costs_for_runway, fixed_costs_for_runway, added_optional_costs):
    """Helper to categorize costs for display and charting."""
    categories = OrderedDict([
        ("Personnel Costs", 0),
        ("Product Dev & Tech Infrastructure", 0),
        ("Software, Tools & Equipment (OpEx + CapEx)", 0),
        ("Go-to-Market (Sales & Marketing)", 0),
        ("Professional Services & Admin", 0)
    ])

    # Sum any salary-related keys dynamically
    salary_total = sum(val for key, val in monthly_costs_for_runway.items() if "Salary" in key)
    categories["Personnel Costs"] += salary_total + monthly_costs_for_runway.get("Payroll Taxes (~10%)", 0)

    categories["Product Dev & Tech Infrastructure"] += monthly_costs_for_runway.get("Cloud Hosting (Avg)", 0) + \
                                                      monthly_costs_for_runway.get("AI Inference (Avg for Pilots)", 0) + \
                                                      monthly_costs_for_runway.get("Other Dev Tech Tools (Avg)", 0)

    for item in software_op_ex_monthly:
        categories["Software, Tools & Equipment (OpEx + CapEx)"] += monthly_costs_for_runway.get(item, 0)

    categories["Professional Services & Admin"] += monthly_costs_for_runway.get("Coworking/Flex Office", 0) + \
                                                   monthly_costs_for_runway.get("GL Insurance", 0) + \
                                                   monthly_costs_for_runway.get("Office Supplies", 0) + \
                                                   monthly_costs_for_runway.get("Legal - Ad Hoc Retainer (Avg)", 0) + \
                                                   monthly_costs_for_runway.get("E&O Insurance (Avg)", 0) + \
                                                   monthly_costs_for_runway.get("Misc Admin (Avg)", 0)
    # Assign fixed costs
    categories["Software, Tools & Equipment (OpEx + CapEx)"] += fixed_costs_for_runway.get("Hardware (5 Laptops)", 0)
    categories["Product Dev & Tech Infrastructure"] += fixed_costs_for_runway.get("SOC 2 Readiness Platform", 0)
    categories["Go-to-Market (Sales & Marketing)"] += fixed_costs_for_runway.get("Conferences & Events (Initial Plan)", 0) + \
                                                      fixed_costs_for_runway.get("Branding & Digital Presence (Initial Plan)", 0)
    categories["Professional Services & Admin"] += fixed_costs_for_runway.get("Legal - Initial Setup (MSA, Trademark)", 0) + \
                                                   fixed_costs_for_runway.get("Accounting - Tax Prep (1x)", 0) + \
                                                   fixed_costs_for_runway.get("Accounting - Frac CFO (Initial Consult)", 0)

    # Add optional costs to their respective categories
    for cost_name, cost_value in added_optional_costs.items():
        original_item_details = optional_add_back_costs[cost_name]
        category_to_add_to = original_item_details["category"]
        if category_to_add_to in categories:
            categories[category_to_add_to] += cost_value
        else: # Should not happen if categories are defined well
            st.error(f"Unknown category for optional item: {category_to_add_to}")

    return categories

def calculate_total_spend(runway_m, selected_optional_items_map):
    current_monthly_total = sum(monthly_costs_details.values())
    total_monthly_for_runway = current_monthly_total * runway_m

    total_fixed_for_runway = sum(fixed_costs_details.values()) # Fixed costs don't scale with runway in this model

    # Calculate costs for selected optional items
    total_optional_costs = 0
    added_optional_costs_summary = {} # For categorization
    for item_name, is_selected in selected_optional_items_map.items():
        if is_selected:
            item_details = optional_add_back_costs[item_name]
            cost_val = 0
            if item_details["cost_type"] == "monthly":
                cost_val = item_details["cost_value"] * runway_m
            elif item_details["cost_type"] == "annual":
                # Scale annual cost by number of years in runway
                cost_val = item_details["cost_value"] * (runway_m / 12)
            elif item_details["cost_type"] == "one_time":
                cost_val = item_details["cost_value"]
            total_optional_costs += cost_val
            added_optional_costs_summary[item_name] = cost_val


    core_spend = total_monthly_for_runway + total_fixed_for_runway + total_optional_costs

    # For detailed categorization, we need to break down the monthly and fixed sums
    monthly_breakdown_for_runway = {k: v * runway_m for k, v in monthly_costs_details.items()}
    # Fixed costs don't change with runway
    fixed_breakdown_for_runway = fixed_costs_details.copy()


    categorized_breakdown = categorize_costs(monthly_breakdown_for_runway, fixed_breakdown_for_runway, added_optional_costs_summary)

    return core_spend, categorized_breakdown, total_monthly_for_runway, total_fixed_for_runway, total_optional_costs, added_optional_costs_summary

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Opereta Use of Funds Dashboard")

st.title("Opereta: Pre-Seed Use of Funds Dashboard 🚀")
st.markdown("An interactive tool to explore Opereta's $1.2M pre-seed funding allocation and runway scenarios.")
st.markdown("---")

# --- Sidebar for Controls ---
st.sidebar.header("Scenario Adjustments")

target_raise_input = st.sidebar.number_input(
    "Target Raise Amount (USD)",
    min_value=500_000,
    max_value=2_500_000,
    value=TARGET_RAISE_USD,
    step=50_000,
    format="%d"
)

runway_months_slider = st.sidebar.slider(
    "Desired Runway (Months)",
    min_value=9,
    max_value=24,
    value=INITIAL_RUNWAY_MONTHS,
    step=1
)
st.sidebar.markdown("---")
st.sidebar.subheader("Toggle Optional Expenses:")
selected_optionals = {}
for item_name in optional_add_back_costs.keys():
    selected_optionals[item_name] = st.sidebar.checkbox(f"Include {item_name}", value=False)

# --- Advanced Cost Overrides -------------------------------------------------------
with st.sidebar.expander("🛠️ Advanced: Adjust Individual Costs", expanded=False):
    st.caption("Leave blank to keep default. All values in USD.")

    # Editable monthly costs
    if st.checkbox("Edit Monthly Costs", value=False):
        for key in sorted(monthly_costs_details.keys()):
            new_val = st.number_input(key, min_value=0, value=int(monthly_costs_details[key]), step=100, key=f"mc_{key}")
            monthly_costs_details[key] = new_val

    # Editable fixed costs
    if st.checkbox("Edit Fixed / One-time Costs", value=False):
        for key in sorted(fixed_costs_details.keys()):
            new_val = st.number_input(key, min_value=0, value=int(fixed_costs_details[key]), step=100, key=f"fc_{key}")
            fixed_costs_details[key] = new_val

    st.markdown("---")
    st.markdown("**➕ Add New Monthly Cost**")
    new_monthly_name = st.text_input("Name", key="new_monthly_name")
    new_monthly_amt = st.number_input("Amount (USD)", min_value=0, step=100, key="new_monthly_amt")
    if st.button("Add Monthly Cost"):
        if new_monthly_name and new_monthly_amt > 0:
            monthly_costs_details[new_monthly_name] = int(new_monthly_amt)

    st.markdown("**➕ Add New Fixed Cost**")
    new_fixed_name = st.text_input("Name ", key="new_fixed_name")
    new_fixed_amt = st.number_input("Amount (USD) ", min_value=0, step=100, key="new_fixed_amt")
    if st.button("Add Fixed Cost"):
        if new_fixed_name and new_fixed_amt > 0:
            fixed_costs_details[new_fixed_name] = int(new_fixed_amt)

# --- Calculations based on controls ---
calculated_core_spend, categorized_spend, monthly_spend_total_for_runway, fixed_spend_total_for_runway, optional_spend_total, added_optional_costs_for_display = calculate_total_spend(runway_months_slider, selected_optionals)
contingency_amount = target_raise_input - calculated_core_spend
contingency_percentage = (contingency_amount / target_raise_input) * 100 if target_raise_input > 0 else 0

# --- Main Page Display ---
st.header("Funding Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Target Raise", f"${target_raise_input:,.0f}")
col2.metric("Desired Runway", f"{runway_months_slider} Months")
col3.metric("Estimated Core Spend", f"${calculated_core_spend:,.0f}")
col4.metric("Contingency Buffer", f"${contingency_amount:,.0f} ({contingency_percentage:.1f}%)",
             delta=f"{contingency_percentage - 20:.1f}% vs 20% target", delta_color="normal" if contingency_percentage >=20 else "inverse")

st.markdown("---")

# --- Visualizations ---
st.header("Use of Funds Allocation")
df_categories = pd.DataFrame(list(categorized_spend.items()), columns=['Category', 'Amount'])
df_categories = df_categories[df_categories['Amount'] > 0] # Filter out zero-amount categories

fig_pie = px.pie(
    df_categories,
    values='Amount',
    names='Category',
    title='Budget Allocation by Major Category',
    color_discrete_sequence=px.colors.sequential.Tealgrn,
    hole=0.4  # slightly larger hole for readability
)
# Render only the percentage inside the slice; category name lives in the legend (avoids text overlap)
fig_pie.update_traces(
    textposition='inside',
    textinfo='percent',
    insidetextorientation='radial',
    hovertemplate='%{label}: %{percent} (%{value:$,.0f})<extra></extra>'
)
# Show legend for category names and give Plotly room for outside labels
fig_pie.update_layout(showlegend=True, legend_title_text='Category', margin=dict(t=60, b=20, l=0, r=0))

fig_bar = px.bar(df_categories, x='Category', y='Amount', title='Budget Breakdown by Category',
                 color='Amount', color_continuous_scale=px.colors.sequential.Tealgrn,
                 labels={'Amount': 'Estimated Spend (USD)'})
fig_bar.update_layout(xaxis_title="", yaxis_title="Estimated Spend (USD)")


col_chart1, col_chart2 = st.columns(2)
with col_chart1:
    st.plotly_chart(fig_pie, use_container_width=True)
with col_chart2:
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# --- Detailed Breakdown ---
st.header("Detailed Budget Breakdown")
st.info(f"The following breakdown is for the selected {runway_months_slider}-month runway with chosen optional expenses.")

with st.expander("Personnel Costs", expanded=False):
    st.metric("Total Personnel Costs", f"${categorized_spend.get('Personnel Costs', 0):,.0f}")
    # Break down salaries dynamically
    for key in sorted([k for k in monthly_costs_details if "Salary" in k]):
        st.write(f"- {key}: ${monthly_costs_details[key] * runway_months_slider:,.0f}")
    st.write(f"- Payroll Taxes & Basic Overhead (~10%): ${monthly_costs_details['Payroll Taxes (~10%)']*runway_months_slider:,.0f}")
    if selected_optionals.get("Health Benefits Stipend (5ppl @ $300/mo each)", False):
        health_cost = optional_add_back_costs["Health Benefits Stipend (5ppl @ $300/mo each)"]["cost_value"] * runway_months_slider
        st.write(f"- *Optional: Health Benefits Stipend:* ${health_cost:,.0f}")


with st.expander("Product Development & Technology Infrastructure", expanded=False):
    st.metric("Total Product Dev & Tech", f"${categorized_spend.get('Product Dev & Tech Infrastructure',0):,.0f}")
    st.write(f"- Cloud Hosting (Avg over {runway_months_slider}mo): ${monthly_costs_details['Cloud Hosting (Avg)']*runway_months_slider:,.0f}")
    st.write(f"- AI Inference (Avg over {runway_months_slider}mo for pilots): ${monthly_costs_details['AI Inference (Avg for Pilots)']*runway_months_slider:,.0f}")
    st.write(f"- SOC 2 Readiness Platform (Fixed): ${fixed_costs_details['SOC 2 Readiness Platform']:,.0f}")
    st.write(f"- Other Development Tools (Avg over {runway_months_slider}mo): ${monthly_costs_details['Other Dev Tech Tools (Avg)']*runway_months_slider:,.0f}")
    if selected_optionals.get("Full SOC 2 Type I Audit", False):
        audit_cost = optional_add_back_costs["Full SOC 2 Type I Audit"]["cost_value"]
        st.write(f"- *Optional: Full SOC 2 Type I Audit:* ${audit_cost:,.0f}")

with st.expander("Software, Tools & Equipment (OpEx + CapEx)", expanded=False):
    st.metric("Total Software, Tools & Equipment", f"${categorized_spend.get('Software, Tools & Equipment (OpEx + CapEx)',0):,.0f}")
    st.write(f"**Operational SaaS (Total for {runway_months_slider} months):**")
    current_saas_total = 0
    for item in software_op_ex_monthly: # Defined in categorize_costs context
        val = monthly_costs_details[item] * runway_months_slider
        st.write(f"  - {item}: ${val:,.0f}")
        current_saas_total += val
    st.write(f"  **Subtotal SaaS OpEx: ${current_saas_total:,.0f}**")
    st.write(f"**Capital Expenditure (Fixed):**")
    st.write(f"  - Hardware (5 Laptops): ${fixed_costs_details['Hardware (5 Laptops)']:,.0f}")


with st.expander("Go-to-Market (Sales & Marketing)", expanded=False):
    st.metric("Total Go-to-Market", f"${categorized_spend.get('Go-to-Market (Sales & Marketing)',0):,.0f}")
    st.write(f"- Conferences & Events (Fixed Base): ${fixed_costs_details['Conferences & Events (Initial Plan)']:,.0f}")
    st.write(f"- Branding & Digital Presence (Fixed Base): ${fixed_costs_details['Branding & Digital Presence (Initial Plan)']:,.0f}")
    if selected_optionals.get("Increased Conference Budget", False):
        conf_increase = optional_add_back_costs["Increased Conference Budget"]["cost_value"]
        st.write(f"- *Optional: Increased Conference Budget:* ${conf_increase:,.0f}")


with st.expander("Professional Services & Admin", expanded=False):
    st.metric("Total Professional Services & Admin", f"${categorized_spend.get('Professional Services & Admin',0):,.0f}")
    st.write(f"**Office & Operations (Total for {runway_months_slider} months):**")
    st.write(f"  - Coworking/Flex Office: ${monthly_costs_details['Coworking/Flex Office']*runway_months_slider:,.0f}")
    st.write(f"  - GL Insurance: ${monthly_costs_details['GL Insurance']*runway_months_slider:,.0f}")
    st.write(f"  - Office Supplies: ${monthly_costs_details['Office Supplies']*runway_months_slider:,.0f}")
    st.write(f"**External Services:**")
    st.write(f"  - Legal - Initial Setup (Fixed): ${fixed_costs_details['Legal - Initial Setup (MSA, Trademark)']:,.0f}")
    retainer_monthly = monthly_costs_details.get('Legal - Ad Hoc Retainer (Avg)', 0)
    if retainer_monthly > 0:
        st.write(f"  - Legal - Ad Hoc Retainer (Avg over {runway_months_slider}mo): ${(retainer_monthly*runway_months_slider):,.0f}")
    st.write(f"  - Accounting - Tax Prep (1x Fixed): ${fixed_costs_details['Accounting - Tax Prep (1x)']:,.0f}")
    st.write(f"  - Accounting - Frac CFO (Initial Consult Fixed): ${fixed_costs_details['Accounting - Frac CFO (Initial Consult)']:,.0f}")
    st.write(f"  - E&O Insurance (Avg over {runway_months_slider}mo): ${monthly_costs_details['E&O Insurance (Avg)']*runway_months_slider:,.0f}")
    st.write(f"  - Misc Admin (Avg over {runway_months_slider}mo): ${monthly_costs_details['Misc Admin (Avg)']*runway_months_slider:,.0f}")
    if selected_optionals.get("D&O Insurance (Annual)", False):
        d_o_cost = optional_add_back_costs["D&O Insurance (Annual)"]["cost_value"] * (runway_months_slider / 12)
        st.write(f"- *Optional: D&O Insurance:* ${d_o_cost:,.2f}")


st.markdown("---")

# --- Key Milestones & Assumptions ---
col_m, col_a = st.columns(2)
with col_m:
    st.subheader("Key Milestones (with this Funding)")
    st.markdown(f"""
    *   **Beachhead Product Launch ({runway_months_slider} mo target):** Core AI screening, contextual role definition, foundational analytics.
    *   **Enterprise Pilot Customers (1-2 Clients):** Onboard and validate with initial paying customers.
    *   **SOC 2 Readiness:** Essential policies, procedures, and controls implemented.
    *   **Iterated Product & GTM Strategy:** Refined based on pilot feedback.
    *   **Strong Foundation for Seed Round.**
    """)
with col_a:
    st.subheader("Core Assumptions")
    st.markdown(f"""
    *   **Team:** 3 founders & 2 early engineers (total 5 FTE), no additional hires in this phase (unless toggled in scenario settings).
    *   **Salaries:** $10k/month per founder • $9k/month per engineer (plus equity grants).
    *   **Location:** Seattle-based (lean office/remote focus).
    *   **Health Benefits:** Deferred (unless stipend toggled as optional).
    *   **Marketing:** Highly targeted, low-cost initiatives.
    *   **Contingency Goal:** Aim for >20% buffer within the raise.
    """)

st.markdown("---")
st.caption("This dashboard is for illustrative and discussion purposes. All figures are estimates based on the current Opereta pre-seed plan. Actual expenditures may vary.")

# --- How to Use ---
with st.sidebar.expander("ℹ️ How to Use This Dashboard", expanded=True):
    st.markdown("""
    *   **Target Raise Amount:** Adjust the total funding you are hypothetically raising.
    *   **Desired Runway:** Use the slider to see how changing the operational runway (in months) impacts your core spend and contingency, assuming the target raise remains fixed.
    *   **Toggle Optional Expenses:** Check boxes to include typically deferred pre-seed expenses (like D&O insurance or health benefits) and observe their impact on the total budget and remaining contingency.
    *   **Charts & Breakdowns:** The main panel will update to reflect your selections, showing the allocation of funds and detailed costs.
    """)