import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from scipy.stats import chi2_contingency

st.set_page_config(
    page_title="GrowthPulse Dashboard",
    page_icon="📊",
    layout="wide"
)

DB_PATH = "data/growthpulse.db"


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)

    users = pd.read_sql_query("SELECT * FROM users", conn)
    events = pd.read_sql_query("SELECT * FROM events", conn)
    purchases = pd.read_sql_query("SELECT * FROM purchases", conn)

    conn.close()

    users["signup_date"] = pd.to_datetime(users["signup_date"])
    events["event_timestamp"] = pd.to_datetime(events["event_timestamp"])
    purchases["purchase_timestamp"] = pd.to_datetime(purchases["purchase_timestamp"])

    return users, events, purchases


users, events, purchases = load_data()

st.title("GrowthPulse: Product Funnel & Experimentation Dashboard")
st.caption("Senior leadership dashboard for funnel conversion, retention, revenue, and A/B test impact.")

with st.sidebar:
    st.header("Filters")

    selected_device = st.multiselect(
        "Device",
        sorted(users["device"].unique()),
        default=sorted(users["device"].unique())
    )

    selected_country = st.multiselect(
        "Country",
        sorted(users["country"].unique()),
        default=sorted(users["country"].unique())
    )

    selected_campaign = st.multiselect(
        "Campaign",
        sorted(users["campaign"].unique()),
        default=sorted(users["campaign"].unique())
    )

filtered_users = users[
    (users["device"].isin(selected_device)) &
    (users["country"].isin(selected_country)) &
    (users["campaign"].isin(selected_campaign))
]

filtered_events = events[events["user_id"].isin(filtered_users["user_id"])]
filtered_purchases = purchases[purchases["user_id"].isin(filtered_users["user_id"])]

total_users = filtered_users["user_id"].nunique()
total_purchases = filtered_purchases["user_id"].nunique()
revenue = filtered_purchases["purchase_amount"].sum()
conversion_rate = total_purchases / total_users if total_users > 0 else 0

d30_users = filtered_events[filtered_events["event_name"] == "Returned Day 30"]["user_id"].nunique()
d30_retention = d30_users / total_users if total_users > 0 else 0

avg_order_value = revenue / total_purchases if total_purchases > 0 else 0

tab1, tab2, tab3, tab4 = st.tabs([
    "Executive Summary",
    "Funnel Analysis",
    "Retention",
    "Experiment Impact"
])

# -----------------------------
# TAB 1: EXECUTIVE SUMMARY
# -----------------------------
with tab1:
    st.subheader("Executive Summary")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Users", f"{total_users:,}")
    col2.metric("Paid Conversion Rate", f"{conversion_rate:.1%}")
    col3.metric("Revenue", f"${revenue:,.0f}")
    col4.metric("D30 Retention", f"{d30_retention:.1%}")

    st.divider()

    target_conversion = 0.18
    revenue_opportunity = max((target_conversion - conversion_rate) * total_users * avg_order_value, 0)

    st.subheader("Leadership Readout")

    if conversion_rate < target_conversion:
        st.warning(
            f"Conversion is below the 18% target. Closing this gap could unlock an estimated "
            f"${revenue_opportunity:,.0f} in incremental revenue."
        )
    else:
        st.success(
            "Conversion is above target. Leadership should focus on retention and scaling the highest-performing segments."
        )

    if d30_retention < 0.15:
        st.warning(
            "D30 retention is below target, suggesting users may not be finding enough long-term value after onboarding."
        )
    else:
        st.success(
            "D30 retention is in a healthy range, indicating stronger post-purchase engagement."
        )

    st.info(
        "Recommended leadership focus: prioritize funnel friction, monitor retention by cohort, "
        "and use the experiment results to decide whether to scale the new onboarding experience."
    )

# -----------------------------
# TAB 2: FUNNEL ANALYSIS
# -----------------------------
with tab2:
    st.subheader("Funnel Analysis")

    funnel_steps = ["Visited Site", "Signed Up", "Activated", "Purchased"]
    funnel_data = []

    for step in funnel_steps:
        user_count = filtered_events[filtered_events["event_name"] == step]["user_id"].nunique()
        funnel_data.append([step, user_count])

    funnel_df = pd.DataFrame(funnel_data, columns=["Step", "Users"])
    funnel_df["Conversion From Start"] = funnel_df["Users"] / funnel_df["Users"].iloc[0]
    funnel_df["Step Drop-Off"] = funnel_df["Users"].pct_change().fillna(0)

    fig_funnel = px.funnel(
        funnel_df,
        x="Users",
        y="Step",
        title="User Funnel: Visit to Purchase"
    )

    st.plotly_chart(fig_funnel, use_container_width=True)
    st.dataframe(funnel_df, use_container_width=True)

    biggest_dropoff_idx = funnel_df["Step Drop-Off"].idxmin()
    biggest_dropoff_step = funnel_df.loc[biggest_dropoff_idx, "Step"]
    biggest_dropoff_rate = abs(funnel_df.loc[biggest_dropoff_idx, "Step Drop-Off"])

    st.warning(
        f"Biggest funnel drop-off occurs at **{biggest_dropoff_step}**, "
        f"with a step-level drop-off of **{biggest_dropoff_rate:.1%}**."
    )

    st.divider()

    st.subheader("Segment-Level Funnel Diagnosis")

    segment = st.selectbox("Select Segment", ["device", "country", "campaign"])

    segment_df = []

    for val in filtered_users[segment].unique():
        seg_users = filtered_users[filtered_users[segment] == val]
        purchased = filtered_purchases[
            filtered_purchases["user_id"].isin(seg_users["user_id"])
        ]

        total = seg_users["user_id"].nunique()
        converted = purchased["user_id"].nunique()
        conv_rate = converted / total if total > 0 else 0

        segment_df.append([val, total, converted, conv_rate])

    segment_df = pd.DataFrame(
        segment_df,
        columns=["Segment", "Users", "Purchases", "Conversion Rate"]
    )

    fig_segment = px.bar(
        segment_df,
        x="Segment",
        y="Conversion Rate",
        text="Conversion Rate",
        title="Conversion Rate by Segment"
    )

    fig_segment.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    fig_segment.update_layout(yaxis_tickformat=".0%")

    st.plotly_chart(fig_segment, use_container_width=True)
    st.dataframe(segment_df, use_container_width=True)

    worst_segment = segment_df.loc[segment_df["Conversion Rate"].idxmin()]

    st.warning(
        f"Lowest-performing segment is **{worst_segment['Segment']}**, "
        f"with conversion at **{worst_segment['Conversion Rate']:.1%}**. "
        f"This is a key opportunity for targeted optimization."
    )

    st.divider()

    st.subheader("Revenue Opportunity by Segment")

    target_conv = 0.18

    segment_df["Revenue Opportunity"] = (
        (target_conv - segment_df["Conversion Rate"])
        * segment_df["Users"]
        * avg_order_value
    ).clip(lower=0)

    fig_rev = px.bar(
        segment_df,
        x="Segment",
        y="Revenue Opportunity",
        text="Revenue Opportunity",
        title="Estimated Revenue Opportunity by Segment"
    )

    fig_rev.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")

    st.plotly_chart(fig_rev, use_container_width=True)

# -----------------------------
# TAB 3: RETENTION
# -----------------------------
with tab3:
    st.subheader("Retention Snapshot")

    retention_data = []

    for day in [1, 7, 30]:
        retained_users = filtered_events[
            filtered_events["event_name"] == f"Returned Day {day}"
        ]["user_id"].nunique()

        retention_rate = retained_users / total_users if total_users > 0 else 0
        retention_data.append([f"Day {day}", retained_users, retention_rate])

    retention_df = pd.DataFrame(
        retention_data,
        columns=["Retention Window", "Users Retained", "Retention Rate"]
    )

    fig_retention = px.bar(
        retention_df,
        x="Retention Window",
        y="Retention Rate",
        text="Retention Rate",
        title="Retention Performance"
    )

    fig_retention.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    fig_retention.update_layout(yaxis_tickformat=".0%")

    st.plotly_chart(fig_retention, use_container_width=True)
    st.dataframe(retention_df, use_container_width=True)

    st.info(
        "Retention naturally declines over time. The key leadership question is whether "
        "D7 and D30 retention are strong enough to support sustainable growth."
    )

    st.divider()

    st.subheader("Cohort Retention Heatmap")

    cohort_users = filtered_users.copy()
    cohort_users["signup_date"] = pd.to_datetime(cohort_users["signup_date"])
    cohort_users["signup_month"] = cohort_users["signup_date"].dt.to_period("M").astype(str)

    cohort_events = filtered_events.merge(
        cohort_users[["user_id", "signup_date", "signup_month"]],
        on="user_id",
        how="inner"
    )

    cohort_events["event_timestamp"] = pd.to_datetime(cohort_events["event_timestamp"])
    cohort_events["signup_date"] = pd.to_datetime(cohort_events["signup_date"])

    cohort_events["days_since_signup"] = (
        cohort_events["event_timestamp"].dt.normalize()
        - cohort_events["signup_date"].dt.normalize()
    ).dt.days

    cohort_events = cohort_events[
        cohort_events["days_since_signup"].isin([1, 7, 30])
    ]

    cohort_summary = cohort_events.groupby(
        ["signup_month", "days_since_signup"]
    )["user_id"].nunique().reset_index()

    cohort_sizes = cohort_users.groupby("signup_month")["user_id"].nunique().reset_index()
    cohort_sizes.columns = ["signup_month", "cohort_size"]

    cohort_summary = cohort_summary.merge(cohort_sizes, on="signup_month", how="left")
    cohort_summary["retention_rate"] = cohort_summary["user_id"] / cohort_summary["cohort_size"]

    cohort_pivot = cohort_summary.pivot(
        index="signup_month",
        columns="days_since_signup",
        values="retention_rate"
    ).fillna(0)

    cohort_pivot.columns = [f"Day {int(col)}" for col in cohort_pivot.columns]

    fig_cohort = px.imshow(
        cohort_pivot,
        text_auto=".1%",
        aspect="auto",
        title="Monthly Cohort Retention: D1 / D7 / D30",
        labels=dict(
            x="Retention Window",
            y="Signup Month",
            color="Retention Rate"
        )
    )

    st.plotly_chart(fig_cohort, use_container_width=True)
    st.dataframe(cohort_pivot.style.format("{:.1%}"), use_container_width=True)

    latest_month = cohort_pivot.index[-1]
    latest_d30 = cohort_pivot.loc[latest_month].get("Day 30", 0)

    if latest_d30 < 0.12:
        st.warning(
            f"Latest cohort D30 retention is **{latest_d30:.1%}**, which suggests weaker long-term engagement. "
            "Leadership should review onboarding quality, product value moments, and lifecycle communication."
        )
    else:
        st.success(
            f"Latest cohort D30 retention is **{latest_d30:.1%}**, showing healthier long-term engagement for recent users."
        )

# -----------------------------
# TAB 4: EXPERIMENT IMPACT
# -----------------------------
with tab4:
    st.subheader("A/B Test Impact")

    ab = filtered_users.merge(
        filtered_purchases[["user_id"]].drop_duplicates().assign(purchased=1),
        on="user_id",
        how="left"
    )

    ab["purchased"] = ab["purchased"].fillna(0)

    ab_summary = ab.groupby("experiment_group").agg(
        users=("user_id", "nunique"),
        purchases=("purchased", "sum")
    ).reset_index()

    ab_summary["conversion_rate"] = ab_summary["purchases"] / ab_summary["users"]

    control_rate = ab_summary.loc[
        ab_summary["experiment_group"] == "Control",
        "conversion_rate"
    ].values[0]

    variant_rate = ab_summary.loc[
        ab_summary["experiment_group"] == "Variant",
        "conversion_rate"
    ].values[0]

    lift = (variant_rate - control_rate) / control_rate

    contingency_table = pd.crosstab(ab["experiment_group"], ab["purchased"])
    chi2, p_value, dof, expected = chi2_contingency(contingency_table)

    col1, col2, col3 = st.columns(3)

    col1.metric("Control Conversion", f"{control_rate:.1%}")
    col2.metric("Variant Conversion", f"{variant_rate:.1%}")
    col3.metric("Lift", f"{lift:.1%}")

    st.write(f"**P-value:** {p_value:.4f}")

    if p_value < 0.05 and lift > 0:
        st.success(
            "Recommendation: Roll out the Variant. The experiment shows a statistically significant conversion lift."
        )
    elif p_value < 0.05 and lift < 0:
        st.error(
            "Recommendation: Do not roll out the Variant. The test shows statistically significant underperformance."
        )
    else:
        st.info(
            "Recommendation: Continue testing. The result is not statistically significant yet."
        )

    fig_ab = px.bar(
        ab_summary,
        x="experiment_group",
        y="conversion_rate",
        text="conversion_rate",
        title="A/B Test Conversion Rate"
    )

    fig_ab.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    fig_ab.update_layout(yaxis_tickformat=".0%")

    st.plotly_chart(fig_ab, use_container_width=True)
    st.dataframe(ab_summary, use_container_width=True)