"""
Telemetry Monitoring System
A comprehensive system monitoring tool that tracks CPU, Memory, Disk, and Network metrics
"""

import psutil
import time
import json
from datetime import datetime
from collections import deque
import threading
import socket
import platform

class TelemetryMonitor:
    def __init__(self, history_size=100):
        """Initialize the telemetry monitor with configurable history size"""
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        self.timestamps = deque(maxlen=history_size)
        self.monitoring = False
        self.monitor_thread = None
        
    def get_cpu_metrics(self):
        """Get CPU usage metrics"""
        return {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'per_cpu': psutil.cpu_percent(interval=1, percpu=True),
            'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    
    def get_memory_metrics(self):
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
    
    def get_disk_metrics(self):
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
    
    def get_network_metrics(self):
        """Get network usage metrics"""
        net = psutil.net_io_counters()
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv,
            'errors_in': net.errin,
            'errors_out': net.errout
        }
    
    def get_system_info(self):
        """Get general system information"""
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        return {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'boot_time': boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            'uptime': str(datetime.now() - boot_time).split('.')[0]
        }
    
    def collect_metrics(self):
        """Collect all metrics at once"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cpu = self.get_cpu_metrics()
        memory = self.get_memory_metrics()
        disk = self.get_disk_metrics()
        network = self.get_network_metrics()
        
        self.timestamps.append(timestamp)
        self.cpu_history.append(cpu['percent'])
        self.memory_history.append(memory['percent'])
        self.disk_history.append(disk['percent'])
        self.network_history.append({
            'sent': network['bytes_sent'],
            'recv': network['bytes_recv']
        })
        
        return {
            'timestamp': timestamp,
            'cpu': cpu,
            'memory': memory,
            'disk': disk,
            'network': network
        }
    
    def format_bytes(self, bytes_value):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} PB"
    
    def display_metrics(self, metrics):
        """Display metrics in a formatted way"""
        print("\n" + "="*60)
        print(f"System Telemetry - {metrics['timestamp']}")
        print("="*60)
        
        # CPU Information
        print(f"\n📊 CPU Usage:")
        print(f"  Overall: {metrics['cpu']['percent']:.1f}%")
        print(f"  Cores: {metrics['cpu']['count']}")
        if metrics['cpu']['freq']:
            print(f"  Frequency: {metrics['cpu']['freq']['current']:.0f} MHz")
        
        # Memory Information
        print(f"\n💾 Memory Usage:")
        print(f"  Used: {self.format_bytes(metrics['memory']['used'])} / {self.format_bytes(metrics['memory']['total'])}")
        print(f"  Percentage: {metrics['memory']['percent']:.1f}%")
        print(f"  Available: {self.format_bytes(metrics['memory']['available'])}")
        print(f"  Swap: {metrics['memory']['swap_percent']:.1f}%")
        
        # Disk Information
        print(f"\n💿 Disk Usage:")
        print(f"  Used: {self.format_bytes(metrics['disk']['used'])} / {self.format_bytes(metrics['disk']['total'])}")
        print(f"  Percentage: {metrics['disk']['percent']:.1f}%")
        print(f"  Free: {self.format_bytes(metrics['disk']['free'])}")
        
        # Network Information
        print(f"\n🌐 Network:")
        print(f"  Sent: {self.format_bytes(metrics['network']['bytes_sent'])}")
        print(f"  Received: {self.format_bytes(metrics['network']['bytes_recv'])}")
        print(f"  Packets Sent: {metrics['network']['packets_sent']:,}")
        print(f"  Packets Received: {metrics['network']['packets_recv']:,}")
    
    def check_alerts(self, metrics):
        """Check for alert conditions"""
        alerts = []
        
        if metrics['cpu']['percent'] > 80:
            alerts.append(f"⚠️  HIGH CPU USAGE: {metrics['cpu']['percent']:.1f}%")
        
        if metrics['memory']['percent'] > 80:
            alerts.append(f"⚠️  HIGH MEMORY USAGE: {metrics['memory']['percent']:.1f}%")
        
        if metrics['disk']['percent'] > 90:
            alerts.append(f"⚠️  HIGH DISK USAGE: {metrics['disk']['percent']:.1f}%")
        
        if alerts:
            print("\n" + "="*60)
            print("🚨 ALERTS:")
            for alert in alerts:
                print(f"  {alert}")
            print("="*60)
    
    def save_to_json(self, metrics, filename='telemetry_log.json'):
        """Save metrics to JSON file"""
        try:
            with open(filename, 'a') as f:
                json.dump(metrics, f)
                f.write('\n')
        except Exception as e:
            print(f"Error saving to file: {e}")
    
    def monitor_loop(self, interval=5, display=True, save=False):
        """Continuous monitoring loop"""
        print(f"\n🔍 Starting telemetry monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.monitoring:
                metrics = self.collect_metrics()
                
                if display:
                    self.display_metrics(metrics)
                    self.check_alerts(metrics)
                
                if save:
                    self.save_to_json(metrics)
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n✋ Monitoring stopped by user")
            self.monitoring = False
    
    def start_monitoring(self, interval=5, display=True, save=False):
        """Start monitoring in a separate thread"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self.monitor_loop,
                args=(interval, display, save),
                daemon=True
            )
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def get_summary(self):
        """Get summary statistics of collected data"""
        if len(self.cpu_history) == 0:
            return "No data collected yet"
        
        summary = {
            'cpu': {
                'avg': sum(self.cpu_history) / len(self.cpu_history),
                'max': max(self.cpu_history),
                'min': min(self.cpu_history)
            },
            'memory': {
                'avg': sum(self.memory_history) / len(self.memory_history),
                'max': max(self.memory_history),
                'min': min(self.memory_history)
            },
            'disk': {
                'avg': sum(self.disk_history) / len(self.disk_history),
                'max': max(self.disk_history),
                'min': min(self.disk_history)
            },
            'samples': len(self.cpu_history)
        }
        return summary


def main():
    """Main function to run the telemetry monitor"""
    monitor = TelemetryMonitor(history_size=100)
    
    # Display system info
    print("\n" + "="*60)
    print("🖥️  SYSTEM INFORMATION")
    print("="*60)
    sys_info = monitor.get_system_info()
    for key, value in sys_info.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Start continuous monitoring
    # Change parameters as needed:
    # - interval: seconds between readings
    # - display: show output in console
    # - save: save to JSON file
    monitor.monitor_loop(interval=5, display=True, save=False)


if __name__ == "__main__":
    main()