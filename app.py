"""
Telemetry Monitoring System with Streamlit Dashboard
Real-time system monitoring with interactive web interface
"""

import streamlit as st
import psutil
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import platform
import time
import socket

# Page configuration
st.set_page_config(
    page_title="System Telemetry Monitor",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    .alert-box {
        background-color: #ff4b4b;
        padding: 15px;
        border-radius: 5px;
        color: white;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = {
        'timestamp': [],
        'cpu': [],
        'memory': [],
        'disk': [],
        'network_sent': [],
        'network_recv': []
    }
if 'monitoring' not in st.session_state:
    st.session_state.monitoring = False

def format_bytes(bytes_value):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def get_system_info():
    """Get general system information"""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'boot_time': boot_time.strftime("%Y-%m-%d %H:%M:%S"),
        'uptime': str(uptime).split('.')[0],
        'cpu_count': psutil.cpu_count()
    }

def get_cpu_metrics():
    """Get CPU usage metrics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_freq = psutil.cpu_freq()
    per_cpu = psutil.cpu_percent(interval=1, percpu=True)
    
    return {
        'percent': cpu_percent,
        'frequency': cpu_freq.current if cpu_freq else 0,
        'per_cpu': per_cpu
    }

def get_memory_metrics():
    """Get memory usage metrics"""
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    
    return {
        'total': mem.total,
        'available': mem.available,
        'used': mem.used,
        'percent': mem.percent,
        'swap_total': swap.total,
        'swap_used': swap.used,
        'swap_percent': swap.percent
    }

def get_disk_metrics():
    """Get disk usage metrics"""
    disk = psutil.disk_usage('/')
    io = psutil.disk_io_counters()
    
    return {
        'total': disk.total,
        'used': disk.used,
        'free': disk.free,
        'percent': disk.percent,
        'read_bytes': io.read_bytes if io else 0,
        'write_bytes': io.write_bytes if io else 0
    }

def get_network_metrics():
    """Get network usage metrics"""
    net = psutil.net_io_counters()
    
    return {
        'bytes_sent': net.bytes_sent,
        'bytes_recv': net.bytes_recv,
        'packets_sent': net.packets_sent,
        'packets_recv': net.packets_recv
    }

def check_alerts(cpu_percent, mem_percent, disk_percent):
    """Check for alert conditions"""
    alerts = []
    
    if cpu_percent > 80:
        alerts.append(f"⚠️ HIGH CPU USAGE: {cpu_percent:.1f}%")
    
    if mem_percent > 80:
        alerts.append(f"⚠️ HIGH MEMORY USAGE: {mem_percent:.1f}%")
    
    if disk_percent > 90:
        alerts.append(f"⚠️ HIGH DISK USAGE: {disk_percent:.1f}%")
    
    return alerts

def create_gauge_chart(value, title, color):
    """Create a gauge chart for metrics"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 24}},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#e8f5e9'},
                {'range': [50, 80], 'color': '#fff9c4'},
                {'range': [80, 100], 'color': '#ffcdd2'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def create_line_chart(history_data):
    """Create line chart for historical data"""
    if not history_data['timestamp']:
        return None
    
    df = pd.DataFrame(history_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['cpu'],
        mode='lines+markers',
        name='CPU %',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['memory'],
        mode='lines+markers',
        name='Memory %',
        line=dict(color='#ff7f0e', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['disk'],
        mode='lines+markers',
        name='Disk %',
        line=dict(color='#2ca02c', width=2)
    ))
    
    fig.update_layout(
        title='Resource Usage Over Time',
        xaxis_title='Time',
        yaxis_title='Usage (%)',
        height=400,
        hovermode='x unified',
        yaxis=dict(range=[0, 100])
    )
    
    return fig

# Main Dashboard
def main():
    # Header
    st.title("🖥️ System Telemetry Monitor")
    st.markdown("### Real-time System Performance Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        refresh_rate = st.slider("Refresh Rate (seconds)", 1, 10, 2)
        max_history = st.slider("Max History Points", 10, 100, 50)
        
        st.markdown("---")
        st.header("📊 System Info")
        sys_info = get_system_info()
        st.info(f"**Hostname:** {sys_info['hostname']}")
        st.info(f"**Platform:** {sys_info['platform']}")
        st.info(f"**CPU Cores:** {sys_info['cpu_count']}")
        st.info(f"**Uptime:** {sys_info['uptime']}")
        st.info(f"**Boot Time:** {sys_info['boot_time']}")
    
    # Get current metrics
    cpu = get_cpu_metrics()
    memory = get_memory_metrics()
    disk = get_disk_metrics()
    network = get_network_metrics()
    
    # Check for alerts
    alerts = check_alerts(cpu['percent'], memory['percent'], disk['percent'])
    
    # Display alerts
    if alerts:
        st.markdown("### 🚨 Active Alerts")
        for alert in alerts:
            st.error(alert)
        st.markdown("---")
    
    # Metric Cards Row 1
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🔵 CPU Usage",
            value=f"{cpu['percent']:.1f}%",
            delta=f"{cpu['frequency']:.0f} MHz" if cpu['frequency'] else None
        )
    
    with col2:
        st.metric(
            label="🟣 Memory Usage",
            value=f"{memory['percent']:.1f}%",
            delta=f"{format_bytes(memory['available'])} free"
        )
    
    with col3:
        st.metric(
            label="🟢 Disk Usage",
            value=f"{disk['percent']:.1f}%",
            delta=f"{format_bytes(disk['free'])} free"
        )
    
    with col4:
        st.metric(
            label="🟠 Network Recv",
            value=format_bytes(network['bytes_recv']),
            delta=f"↑ {format_bytes(network['bytes_sent'])}"
        )
    
    st.markdown("---")
    
    # Gauge Charts
    st.markdown("### 📊 Real-time Gauges")
    gauge_col1, gauge_col2, gauge_col3 = st.columns(3)
    
    with gauge_col1:
        st.plotly_chart(
            create_gauge_chart(cpu['percent'], "CPU", "#1f77b4"),
            use_container_width=True
        )
    
    with gauge_col2:
        st.plotly_chart(
            create_gauge_chart(memory['percent'], "Memory", "#ff7f0e"),
            use_container_width=True
        )
    
    with gauge_col3:
        st.plotly_chart(
            create_gauge_chart(disk['percent'], "Disk", "#2ca02c"),
            use_container_width=True
        )
    
    # Update history
    current_time = datetime.now().strftime("%H:%M:%S")
    st.session_state.history['timestamp'].append(current_time)
    st.session_state.history['cpu'].append(cpu['percent'])
    st.session_state.history['memory'].append(memory['percent'])
    st.session_state.history['disk'].append(disk['percent'])
    st.session_state.history['network_sent'].append(network['bytes_sent'])
    st.session_state.history['network_recv'].append(network['bytes_recv'])
    
    # Keep only recent history
    for key in st.session_state.history:
        if len(st.session_state.history[key]) > max_history:
            st.session_state.history[key] = st.session_state.history[key][-max_history:]
    
    # Historical Chart
    st.markdown("---")
    st.markdown("### 📈 Historical Performance")
    
    if st.session_state.history['timestamp']:
        line_chart = create_line_chart(st.session_state.history)
        if line_chart:
            st.plotly_chart(line_chart, use_container_width=True)
    else:
        st.info("Collecting data... Chart will appear after first refresh.")
    
    # Detailed Statistics
    st.markdown("---")
    st.markdown("### 📋 Detailed Statistics")
    
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.markdown("#### 💾 Memory Details")
        mem_df = pd.DataFrame({
            'Metric': ['Total', 'Used', 'Available', 'Swap Total', 'Swap Used'],
            'Value': [
                format_bytes(memory['total']),
                format_bytes(memory['used']),
                format_bytes(memory['available']),
                format_bytes(memory['swap_total']),
                format_bytes(memory['swap_used'])
            ]
        })
        st.dataframe(mem_df, use_container_width=True, hide_index=True)
    
    with detail_col2:
        st.markdown("#### 💿 Disk Details")
        disk_df = pd.DataFrame({
            'Metric': ['Total', 'Used', 'Free', 'Read', 'Write'],
            'Value': [
                format_bytes(disk['total']),
                format_bytes(disk['used']),
                format_bytes(disk['free']),
                format_bytes(disk['read_bytes']),
                format_bytes(disk['write_bytes'])
            ]
        })
        st.dataframe(disk_df, use_container_width=True, hide_index=True)
    
    # Per-CPU Usage
    if cpu['per_cpu']:
        st.markdown("---")
        st.markdown("### 🔧 Per-Core CPU Usage")
        
        cpu_df = pd.DataFrame({
            'Core': [f"Core {i}" for i in range(len(cpu['per_cpu']))],
            'Usage (%)': cpu['per_cpu']
        })
        
        fig = px.bar(
            cpu_df,
            x='Core',
            y='Usage (%)',
            color='Usage (%)',
            color_continuous_scale='Viridis',
            title='CPU Usage by Core'
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    # Network Statistics
    st.markdown("---")
    st.markdown("### 🌐 Network Statistics")
    
    net_col1, net_col2 = st.columns(2)
    
    with net_col1:
        st.metric("📤 Packets Sent", f"{network['packets_sent']:,}")
    
    with net_col2:
        st.metric("📥 Packets Received", f"{network['packets_recv']:,}")
    
    # Auto-refresh
    st.markdown("---")
    st.info(f"🔄 Auto-refreshing every {refresh_rate} seconds...")
    time.sleep(refresh_rate)
    st.rerun()

if __name__ == "__main__":
    main()