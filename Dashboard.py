# ---------- Imports ----------
import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile

# ---------- Page Config ----------
st.set_page_config(page_title="FraudShield Dashboard", layout="wide")

st.markdown(
    "<h1 style='text-align: center; color: #FF4B4B;'>🚨 FraudShield: Graph-Based Banking Fraud Detection</h1>",
    unsafe_allow_html=True
)
st.markdown("<hr>", unsafe_allow_html=True)


with st.sidebar:
    st.image("https://img.icons8.com/clouds/500/bank.png", width=150)
    st.title("📁 Upload Transaction Data")
    uploaded_file = st.file_uploader("Upload a CSV File", type="csv")
    


def load_data(file):
    df = pd.read_csv(file)
    df.columns = [col.lower() for col in df.columns]
    return df

def build_graph(df):
    G = nx.DiGraph()
    for _, row in df.iterrows():
        src = row['sender']
        dst = row['receiver']
        amt = row['amount']
        G.add_edge(src, dst, weight=amt)
    return G

def detect_fraud(G):
    fraud_nodes = []
    out_weight = {}

    for node in G.nodes():
        total_out = sum(G[u][v]['weight'] for u, v in G.out_edges(node))
        out_weight[node] = total_out

    threshold = pd.Series(out_weight).quantile(0.95)  
    fraud_nodes = [node for node, wt in out_weight.items() if wt >= threshold]

    return fraud_nodes, out_weight

def display_graph(G, fraud_nodes=None, title="Graph"):
    net = Network(height="800px", width="100%", bgcolor="#222222", font_color="white", directed=True)

    for node in G.nodes:
        color = "yellow" if fraud_nodes and node in fraud_nodes else "red"
        net.add_node(node, label=str(node), color=color)

    for source, target, data in G.edges(data=True):
        weight = data.get('weight', 1)
        net.add_edge(
            source,
            target,
            value=0.5,
            title=f"Amount: {weight}",
            color="white",
            width=0.5
        )

    net.force_atlas_2based(
        gravity=-50,
        central_gravity=0.01,
        spring_length=300,
        spring_strength=0.005,
        damping=0.6
    )

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp_file:
        net.save_graph(tmp_file.name)
        html_file = open(tmp_file.name, "r", encoding="utf-8").read()
        st.markdown(f"### {title}")
        components.html(html_file, height=800)


if uploaded_file:
    df = load_data(uploaded_file)
    G = build_graph(df)
    fraud_nodes, out_weights = detect_fraud(G)

    # Graphs
    with st.expander("📡 View Normal Transaction Graph", expanded=True):
        st.markdown("🔴 **Red nodes** = Accounts<br>➡️ **White edges** = Transactions", unsafe_allow_html=True)
        display_graph(G, title="Normal Transaction Graph")

    with st.expander("🚨 View Fraud Detection Graph", expanded=True):
        st.markdown("🟡 **Yellow nodes** = Suspicious accounts (Top 5% by amount sent)<br>🔴 **Red nodes** = Normal accounts", unsafe_allow_html=True)
        display_graph(G, fraud_nodes=fraud_nodes, title="Fraud Detection Graph")

    # Summary Stats
    st.markdown("## 📊 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔢 Total Transactions", len(df))
    col2.metric("💰 Total Amount", f"${df['amount'].sum():,.2f}")
    col3.metric("👤 Unique Senders", df['sender'].nunique())
    col4.metric("👥 Unique Receivers", df['receiver'].nunique())

    # Top Suspicious Accounts
    st.markdown("## 🚨 Top Suspicious Accounts (By Outgoing Amount)")
    fraud_data = [{"Account": node, "Total Outgoing": out_weights[node]} for node in fraud_nodes]
    fraud_df = pd.DataFrame(fraud_data).sort_values(by="Total Outgoing", ascending=False)
    st.dataframe(fraud_df.head(5), use_container_width=True)

else:
    st.info("👈 Upload a CSV file from the sidebar to begin your fraud analysis.")





