import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from database import Database
from csv_manager import CSVManager
from config import Config
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime, timedelta
import os
import csv
import random
import json
from PIL import Image, ImageTk
import requests
import time

class ServerCommunicator:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        
    def get_sensor_data(self, node_id=None):
        """Get sensor data from server"""
        try:
            url = f"{self.base_url}/api/get_data"
            if node_id:
                url += f"?node_id={node_id}"
                
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            print(f"Error getting sensor data: {e}")
            return None
            
    def get_alerts(self):
        """Get alerts from server"""
        try:
            response = requests.get(f"{self.base_url}/api/get_alerts")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException as e:
            print(f"Error getting alerts: {e}")
            return None
            
    def send_test_data(self):
        """Send test data to server (for debugging)"""
        try:
            data = {
                "node_id": 1,
                "temperature": random.uniform(10, 40),
                "humidity": random.uniform(20, 95),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            response = requests.post(
                f"{self.base_url}/api/sensor_data",
                json=data
            )
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Error sending test data: {e}")
            return False

class ForestMonitoringApp:
    def __init__(self, root):
        self.root = root
        self.root.title(Config.APP_NAME)
        self.root.geometry("1400x900")
        self.root.configure(bg=Config.BG_COLOR)
        
        # Initialize components
        self.db = Database()
        self.csv_manager = CSVManager()
        self.server = ServerCommunicator()
        self.current_user = None
        self.animation_items = []
        self.data_refresh_interval = 5000  # 5 seconds
        self.current_view = None
        
        # Set style
        self.setup_styles()
        
        # Create navigation frame (hidden initially)
        self.nav_frame = ttk.Frame(self.root, style='Nav.TFrame')
        
        # Create content frame
        self.content_frame = ttk.Frame(self.root)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Show login screen
        self.show_login()
        
        # Initialize data refresh (will only activate after login)
        #self.schedule_data_refresh()
    def show_map(self):
        """Affiche une vue carte vide pour l’instant"""
        self.clear_content()
        label = tk.Label(self.content_frame, text="Map view (à venir)", font=("Arial", 16))
        label.pack(pady=20)

    def setup_styles(self):
        """Configure ttk styles for professional look"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors and fonts
        style.configure('.', 
                      background=Config.BG_COLOR,
                      foreground=Config.TEXT_COLOR,
                      font=('Segoe UI', 10))
        
        # Navigation frame
        style.configure('Nav.TFrame', 
                       background=Config.PRIMARY_COLOR)
        
        # Navigation buttons
        style.configure('Nav.TButton', 
                       font=('Segoe UI', 10, 'bold'),
                       foreground='white',
                       background=Config.PRIMARY_COLOR,
                       borderwidth=0,
                       padding=10)
        style.map('Nav.TButton',
                 background=[('active', Config.SECONDARY_COLOR)],
                 foreground=[('active', 'white')])
        
        # Regular buttons
        style.configure('TButton',
                       font=('Segoe UI', 10),
                       padding=8,
                       background=Config.SECONDARY_COLOR,
                       foreground='white')
        style.map('TButton',
                 background=[('active', Config.ACCENT_COLOR)],
                 foreground=[('active', 'white')])
        
        # Labels
        style.configure('TLabel',
                       background=Config.BG_COLOR,
                       foreground=Config.TEXT_COLOR,
                       font=('Segoe UI', 10))
        style.configure('Header.TLabel',
                      font=('Segoe UI', 12, 'bold'))
        style.configure('Title.TLabel',
                       font=('Segoe UI', 24, 'bold'),
                       foreground=Config.PRIMARY_COLOR)
        
        # Frames
        style.configure('Card.TFrame',
                      background='white',
                      relief=tk.RAISED,
                      borderwidth=1)
        
        # Treeview (tables)
        style.configure('Treeview',
                      font=('Segoe UI', 10),
                      rowheight=30,
                      background='white',
                      fieldbackground='white',
                      bordercolor='#e0e0e0')
        style.configure('Treeview.Heading',
                      font=('Segoe UI', 10, 'bold'),
                      background=Config.PRIMARY_COLOR,
                      foreground='white')
        style.map('Treeview',
                 background=[('selected', Config.SECONDARY_COLOR)])
    
    def setup_navigation(self):
        """Create persistent navigation bar"""
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        
        # App title/logo
        ttk.Label(
            self.nav_frame,
            text="🌲 FOREST GUARDIAN",
            style='Header.TLabel',
            foreground='white',
            background=Config.PRIMARY_COLOR,
            font=('Segoe UI', 14, 'bold')
        ).pack(side=tk.LEFT, padx=20)
        
        # Navigation buttons
        nav_buttons = [
            ("Dashboard", self.show_dashboard),
            ("Data Tables", self.show_data_table),
            ("Charts", self.show_data_charts),
            ("Alerts", self.show_inbox),
            ("Map", self.show_map),
            ("CSV Tools", self.show_csv_tools)
        ]
        
        for text, command in nav_buttons:
            ttk.Button(
                self.nav_frame,
                text=text,
                style='Nav.TButton',
                command=command
            ).pack(side=tk.LEFT, padx=5)
        
        # Logout button
        ttk.Button(
            self.nav_frame,
            text="Logout",
            style='Nav.TButton',
            command=self.logout
        ).pack(side=tk.RIGHT, padx=20)
    
    def clear_content(self):
        """Clear only the content area"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def create_animation(self):
        """Create falling characters animation for login screen"""
        self.clear_animation()
        
        # Create 50 random falling characters
        for _ in range(50):
            char = random.choice(['0','1','2','3','4','5','6','7','8','9','A','B','C'])
            x = random.randint(0, self.content_frame.winfo_width())
            y = random.randint(-100, 0)
            speed = random.uniform(0.5, 2.0)
            
            label = ttk.Label(
                self.content_frame,
                text=char,
                font=('Segoe UI', 8),
                foreground='#e0e0e0',
                background=Config.BG_COLOR
            )
            label.place(x=x, y=y)
            
            self.animation_items.append((label, speed))
        
        self.animate_characters()
    
    def animate_characters(self):
        """Animate the falling characters"""
        for item in self.animation_items:
            label, speed = item
            x, y = label.winfo_x(), label.winfo_y()
            
            # Move character down
            new_y = y + speed
            label.place(x=x, y=new_y)
            
            # Reset to top if fallen off bottom
            if new_y > self.content_frame.winfo_height():
                label.place(x=random.randint(0, self.content_frame.winfo_width()), 
                           y=random.randint(-100, 0))
        
        # Schedule next animation frame
        if hasattr(self, 'content_frame') and self.current_user is None:
            self.root.after(30, self.animate_characters)
    
    def clear_animation(self):
        """Clear all animation elements"""
        for item in self.animation_items:
            item[0].destroy()
        self.animation_items = []
    
    def show_login(self):
        """Display login window with animations"""
        self.clear_content()
        
        # Hide navigation when logged out
        self.nav_frame.pack_forget()
        
        # Create animation
        self.create_animation()
        
        # Main login container
        login_container = ttk.Frame(self.content_frame)
        login_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Card frame for login form
        card = ttk.Frame(login_container, style='Card.TFrame', padding=(40, 30))
        card.pack()
        
        # Title
        ttk.Label(
            card,
            text="FOREST MONITORING SYSTEM",
            style='Title.TLabel'
        ).grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Username field
        ttk.Label(card, 
                 text="Username:", 
                 style='Header.TLabel').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(card, width=25, font=('Segoe UI', 10))
        self.username_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Password field
        ttk.Label(card, 
                 text="Password:", 
                 style='Header.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(card, show="•", width=25, font=('Segoe UI', 10))
        self.password_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Error message label (initially empty)
        self.login_error_label = ttk.Label(
            card,
            text="",
            foreground="red",
            font=('Segoe UI', 9)
        )
        self.login_error_label.grid(row=3, column=0, columnspan=2, pady=(5, 0))
        
        # Login button
        login_btn = ttk.Button(
            card,
            text="LOGIN",
            style='TButton',
            command=self.handle_login
        )
        login_btn.grid(row=4, column=0, columnspan=2, pady=20, ipadx=20)
        
        # Focus username field
        self.username_entry.focus()
        
        # Bind Enter key to login
        self.root.bind('<Return>', lambda e: self.handle_login())
    
    def handle_login(self):
        print("Login attempt detected")
        """Handle login attempt with validation"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # Clear previous error messages
        self.login_error_label.config(text="")
        
        # Validate inputs
        if not username and not password:
            self.login_error_label.config(text="Please enter both username and password")
            return
        elif not username:
            self.login_error_label.config(text="Please enter your username")
            return
        elif not password:
            self.login_error_label.config(text="Please enter your password")
            return
        
        # Authenticate user
        user = self.db.authenticate_user(username, password)
        if user:
            self.current_user = user
            self.clear_animation()
            self.setup_navigation() 
            self.nav_frame.pack(fill=tk.X, before=self.content_frame)
            self.show_dashboard()
            self.schedule_data_refresh()  # Start periodic refresh

            # Check for alerts in existing data
            self.check_csv_for_alerts()
        else:
            self.login_error_label.config(text="Invalid username or password")
            self.password_entry.delete(0, tk.END)
            self.shake_login()
    
    def shake_login(self):
        """Add shake animation to login on failure"""
        x = self.root.winfo_x()
        for delta in [10, -10, 10, -10, 5, -5, 2, -2, 0]:
            self.root.geometry(f"+{x+delta}+{self.root.winfo_y()}")
            self.root.update()
            self.root.after(30)
    
    def check_csv_for_alerts(self):
        """Check all CSV files for threshold violations and create alerts"""
        try:
            for csv_file in self.csv_manager.get_csv_files():
                filepath = os.path.join('data', csv_file)
                
                with open(filepath, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            node_id = int(row.get('node_id', 0))
                            temp = float(row.get('temperature', 0))
                            humidity = float(row.get('humidity', 0))
                            timestamp = row.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                            
                            # Check temperature thresholds
                            if temp >= Config.TEMP_CRITICAL_THRESHOLD:
                                self.db.add_alert(
                                    node_id,
                                    f"Node {node_id}: Critical high temperature ({temp}°C)",
                                    "critical",
                                    timestamp
                                )
                            elif temp >= Config.TEMP_HIGH_THRESHOLD:
                                self.db.add_alert(
                                    node_id,
                                    f"Node {node_id}: High temperature ({temp}°C)",
                                    "high",
                                    timestamp
                                )
                            elif temp <= Config.TEMP_LOW_THRESHOLD:
                                self.db.add_alert(
                                    node_id,
                                    f"Node {node_id}: Low temperature ({temp}°C)",
                                    "high",
                                    timestamp
                                )
                            
                            # Check humidity thresholds
                            if humidity >= Config.HUMIDITY_CRITICAL_THRESHOLD:
                                self.db.add_alert(
                                    node_id,
                                    f"Node {node_id}: Critical high humidity ({humidity}%)",
                                    "critical",
                                    timestamp
                                )
                            elif humidity >= Config.HUMIDITY_HIGH_THRESHOLD:
                                self.db.add_alert(
                                    node_id,
                                    f"Node {node_id}: High humidity ({humidity}%)",
                                    "high",
                                    timestamp
                                )
                            elif humidity <= Config.HUMIDITY_LOW_THRESHOLD:
                                self.db.add_alert(
                                    node_id,
                                    f"Node {node_id}: Low humidity ({humidity}%)",
                                    "high",
                                    timestamp
                                )
                                
                        except (ValueError, KeyError) as e:
                            print(f"Error processing row: {e}")
                            continue
        except Exception as e:
            print(f"Error checking CSV for alerts: {e}")
    
    def logout(self):
        """Secure logout - hides all content and returns to login"""
        self.current_user = None
        self.nav_frame.pack_forget()
        self.show_login()
    
    def show_dashboard(self):
        """Clean dashboard with just the title"""
        self.clear_content()
        self.current_view = "dashboard"
        
        # Centered title only
        ttk.Label(
            self.content_frame,
            text="FOREST MONITORING DASHBOARD",
            style='Title.TLabel'
        ).place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    def show_csv_tools(self):
        """CSV management tools with improved layout"""
        self.clear_content()
        self.current_view = "csv_tools"
        
        # Header
        header_frame = ttk.Frame(self.content_frame)
        header_frame.pack(fill=tk.X, pady=(20, 10))
        
        ttk.Label(
            header_frame,
            text="CSV File Management",
            style='Title.TLabel'
        ).pack(side=tk.LEFT, padx=20)
        
        # Button frame
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame,
            text="Import CSV",
            style='TButton',
            command=self.show_add_csv
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            button_frame,
            text="Export Data",
            style='TButton',
            command=self.export_data
        ).pack(side=tk.LEFT, padx=10)
        
        # File list container
        list_container = ttk.Frame(self.content_frame)
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        files = self.csv_manager.get_csv_files()
        if not files:
            ttk.Label(list_container, text="No CSV files available").pack()
            return
        
        # Treeview for files with scrollbar
        tree_frame = ttk.Frame(list_container)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        tree = ttk.Treeview(
            tree_frame,
            columns=('filename', 'size', 'modified'),
            show='headings',
            selectmode='browse'
        )
        
        # Configure columns
        tree.heading('filename', text='Filename')
        tree.heading('size', text='Size (KB)')
        tree.heading('modified', text='Last Modified')
        
        tree.column('filename', width=300)
        tree.column('size', width=100, anchor=tk.CENTER)
        tree.column('modified', width=200, anchor=tk.CENTER)
        
        # Add files to treeview
        for file in files:
            filepath = os.path.join('data', file)
            size_kb = os.path.getsize(filepath) / 1024
            modified = datetime.fromtimestamp(os.path.getmtime(filepath))
            
            tree.insert('', tk.END, values=(
                file,
                f"{size_kb:.1f}",
                modified.strftime('%Y-%m-%d %H:%M')
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons
        action_frame = ttk.Frame(self.content_frame)
        action_frame.pack(pady=10)
        
        ttk.Button(
            action_frame,
            text="View Selected",
            style='TButton',
            command=lambda: self.view_csv_content(tree)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            action_frame,
            text="Delete Selected",
            style='TButton',
            command=lambda: self.confirm_delete_csv(tree)
        ).pack(side=tk.LEFT, padx=5)
    
    def show_add_csv(self):
        """Show CSV import dialog with file validation"""
        filepath = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if filepath:
            # Validate CSV structure before importing
            try:
                with open(filepath, 'r') as f:
                    reader = csv.DictReader(f)
                    if not all(field in reader.fieldnames for field in ['node_id', 'temperature', 'humidity']):
                        messagebox.showerror("Error", "CSV file must contain node_id, temperature, and humidity columns")
                        return
            except Exception as e:
                messagebox.showerror("Error", f"Invalid CSV file: {str(e)}")
                return
            
            success, message = self.csv_manager.import_csv(filepath)
            if success:
                messagebox.showinfo("Success", message)
                self.show_csv_tools()
                self.check_csv_for_alerts()  # Check for alerts in new data
            else:
                messagebox.showerror("Error", message)
    
    def view_csv_content(self, tree):
        """View content of selected CSV file in a new window"""
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        filename = tree.item(selected)['values'][0]
        filepath = os.path.join('data', filename)
        
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                rows = list(reader)
            
            # Create popup window
            popup = tk.Toplevel(self.root)
            popup.title(f"Viewing: {filename}")
            popup.geometry("1000x600")
            
            # Create frame for the table
            table_frame = ttk.Frame(popup)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Create treeview widget
            tree = ttk.Treeview(table_frame, columns=headers, show='headings')
            
            # Configure columns
            for header in headers:
                tree.heading(header, text=header)
                tree.column(header, width=150, anchor=tk.CENTER)
            
            # Add data
            for row in rows:
                tree.insert('', tk.END, values=[row.get(h, '') for h in headers])
            
            # Add scrollbars
            vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
            
            # Grid layout
            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')
            hsb.grid(row=1, column=0, sticky='ew')
            
            # Configure resizing
            table_frame.grid_rowconfigure(0, weight=1)
            table_frame.grid_columnconfigure(0, weight=1)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {str(e)}")
    
    def confirm_delete_csv(self, tree):
        """Confirm and delete selected CSV file"""
        selected = tree.focus()
        if not selected:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        filename = tree.item(selected)['values'][0]
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{filename}'?"
        )
        
        if confirm:
            success, message = self.csv_manager.delete_csv(filename)
            if success:
                messagebox.showinfo("Success", message)
                self.show_csv_tools()
            else:
                messagebox.showerror("Error", message)
    
    def export_data(self):
        """Export sensor data to CSV with confirmation"""
        confirm = messagebox.askyesno(
            "Confirm Export",
            "Export all sensor data to a new CSV file?"
        )
        
        if confirm:
            success, message = self.csv_manager.export_to_csv()
            if success:
                messagebox.showinfo("Success", message)
                self.show_csv_tools()
            else:
                messagebox.showerror("Error", message)
    
    def show_data_table(self):
        """Show sensor data in table view with threshold highlighting"""
        self.clear_content()
        self.current_view = "data_table"
        
        # Header
        header_frame = ttk.Frame(self.content_frame)
        header_frame.pack(fill=tk.X, pady=(20, 10))
        
        ttk.Label(
            header_frame,
            text="Sensor Data Table",
            style='Title.TLabel'
        ).pack(side=tk.LEFT, padx=20)
        
        # Try to get data from server first, fall back to CSV files
        data = []
        server_data = self.server.get_sensor_data()
        
        if server_data and server_data.get('status') == 'success':
            # Process server data
            nodes = server_data.get('data', {})
            for node_id, readings in nodes.items():
                for reading in readings:
                    try:
                        node_id = reading.get('node_id', 'N/A')
                        temp = float(reading.get('temperature', 0))
                        hum = float(reading.get('humidity', 0))
                        timestamp = reading.get('timestamp', 'N/A')
                        
                        # Determine status
                        status = []
                        if temp >= Config.TEMP_CRITICAL_THRESHOLD:
                            status.append("CRITICAL HIGH TEMP")
                        elif temp >= Config.TEMP_HIGH_THRESHOLD:
                            status.append("HIGH TEMP")
                        elif temp <= Config.TEMP_LOW_THRESHOLD:
                            status.append("LOW TEMP")
                            
                        if hum >= Config.HUMIDITY_CRITICAL_THRESHOLD:
                            status.append("CRITICAL HIGH HUMIDITY")
                        elif hum >= Config.HUMIDITY_HIGH_THRESHOLD:
                            status.append("HIGH HUMIDITY")
                        elif hum <= Config.HUMIDITY_LOW_THRESHOLD:
                            status.append("LOW HUMIDITY")
                            
                        status_text = ", ".join(status) if status else "Normal"
                        
                        data.append((node_id, temp, hum, timestamp, status_text))
                    except ValueError:
                        continue
        else:
            # Fall back to CSV data
            for csv_file in self.csv_manager.get_csv_files():
                with open(os.path.join('data', csv_file), 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            node_id = row.get('node_id', 'N/A')
                            temp = float(row.get('temperature', 0))
                            hum = float(row.get('humidity', 0))
                            timestamp = row.get('timestamp', 'N/A')
                            
                            # Determine status
                            status = []
                            if temp >= Config.TEMP_CRITICAL_THRESHOLD:
                                status.append("CRITICAL HIGH TEMP")
                            elif temp >= Config.TEMP_HIGH_THRESHOLD:
                                status.append("HIGH TEMP")
                            elif temp <= Config.TEMP_LOW_THRESHOLD:
                                status.append("LOW TEMP")
                                
                            if hum >= Config.HUMIDITY_CRITICAL_THRESHOLD:
                                status.append("CRITICAL HIGH HUMIDITY")
                            elif hum >= Config.HUMIDITY_HIGH_THRESHOLD:
                                status.append("HIGH HUMIDITY")
                            elif hum <= Config.HUMIDITY_LOW_THRESHOLD:
                                status.append("LOW HUMIDITY")
                                
                            status_text = ", ".join(status) if status else "Normal"
                            
                            data.append((node_id, temp, hum, timestamp, status_text))
                        except ValueError:
                            continue
        
        if not data:
            ttk.Label(self.content_frame, text="No sensor data available").pack()
            return
        
        # Create frame for table
        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview widget
        tree = ttk.Treeview(
            table_frame,
            columns=('node_id', 'temperature', 'humidity', 'timestamp', 'status'),
            show='headings',
            selectmode='extended'
        )
        
        # Define headings
        tree.heading('node_id', text='Node ID')
        tree.heading('temperature', text='Temperature (°C)')
        tree.heading('humidity', text='Humidity (%)')
        tree.heading('timestamp', text='Timestamp')
        tree.heading('status', text='Status')
        
        # Define column widths
        tree.column('node_id', width=100, anchor=tk.CENTER)
        tree.column('temperature', width=150, anchor=tk.CENTER)
        tree.column('humidity', width=150, anchor=tk.CENTER)
        tree.column('timestamp', width=200, anchor=tk.CENTER)
        tree.column('status', width=300)
        
        # Add data to treeview with color coding for thresholds
        for row in data:
            node_id, temp, hum, timestamp, status = row
            tags = ()
            
            if "CRITICAL" in status:
                tags = ('critical',)
            elif "HIGH" in status or "LOW" in status:
                tags = ('warning',)
            
            tree.insert('', tk.END, values=row, tags=tags)
        
        # Configure tag colors
        tree.tag_configure('warning', background='#fff3cd')  # Light yellow
        tree.tag_configure('critical', background='#ffcccc')  # Light red
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def show_data_charts(self):
        """Show beautiful data visualization charts per node"""
        self.clear_content()
        self.current_view = "data_charts"
        
        # Header
        header_frame = ttk.Frame(self.content_frame)
        header_frame.pack(fill=tk.X, pady=(20, 10))
        
        ttk.Label(
            header_frame,
            text="Sensor Data Visualization",
            style='Title.TLabel'
        ).pack(side=tk.LEFT, padx=20)
        
        # Get data from CSV files grouped by node
        node_data = {}
        
        for csv_file in self.csv_manager.get_csv_files():
            with open(os.path.join('data', csv_file), 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        node_id = int(row['node_id'])
                        if node_id not in node_data:
                            node_data[node_id] = []
                            
                        timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                        temp = float(row['temperature'])
                        hum = float(row['humidity'])
                            
                        node_data[node_id].append((timestamp, temp, hum))
                    except (KeyError, ValueError) as e:
                        print(f"Error processing row: {e}")
                        continue
        
        if not node_data:
            ttk.Label(self.content_frame, text="No sensor data available").pack()
            return
        
        # Create notebook for tabbed interface
        notebook = ttk.Notebook(self.content_frame)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a tab for each node
        for node_id, data in sorted(node_data.items()):
            if not data:
                continue
                
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=f"Node {node_id}")
            
            # Sort data by timestamp
            data.sort(key=lambda x: x[0])
            timestamps = [x[0] for x in data]
            temps = [x[1] for x in data]
            hums = [x[2] for x in data]
            
            # Create figure with custom style
            plt.style.use('seaborn-v0_8')
            fig = Figure(figsize=(12, 8), dpi=100, facecolor='#f5f5f5')
            fig.suptitle(f"Node {node_id} Sensor Data", fontsize=14, fontweight='bold')
            
            # Temperature plot
            ax1 = fig.add_subplot(211)
            ax1.plot(timestamps, temps, 'r-', linewidth=2, marker='o', markersize=4, 
                     markerfacecolor='white', markeredgecolor='red')
            ax1.set_title('Temperature', fontsize=12, pad=10)
            ax1.set_ylabel('Temperature (°C)', fontsize=10)
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.set_facecolor('#f9f9f9')
            
            # Add threshold lines and annotations
            ax1.axhline(y=Config.TEMP_HIGH_THRESHOLD, color='orange', linestyle='--', linewidth=1)
            ax1.axhline(y=Config.TEMP_CRITICAL_THRESHOLD, color='red', linestyle='--', linewidth=1)
            ax1.axhline(y=Config.TEMP_LOW_THRESHOLD, color='blue', linestyle='--', linewidth=1)
            
            ax1.annotate(f'High Threshold ({Config.TEMP_HIGH_THRESHOLD}°C)', 
                        xy=(timestamps[0], Config.TEMP_HIGH_THRESHOLD),
                        xytext=(10, 10), textcoords='offset points',
                        color='orange', fontsize=8)
            
            ax1.annotate(f'Critical Threshold ({Config.TEMP_CRITICAL_THRESHOLD}°C)', 
                        xy=(timestamps[0], Config.TEMP_CRITICAL_THRESHOLD),
                        xytext=(10, 10), textcoords='offset points',
                        color='red', fontsize=8)
            
            ax1.annotate(f'Low Threshold ({Config.TEMP_LOW_THRESHOLD}°C)', 
                        xy=(timestamps[0], Config.TEMP_LOW_THRESHOLD),
                        xytext=(10, -20), textcoords='offset points',
                        color='blue', fontsize=8)
            
            # Humidity plot
            ax2 = fig.add_subplot(212)
            ax2.plot(timestamps, hums, 'b-', linewidth=2, marker='o', markersize=4,
                    markerfacecolor='white', markeredgecolor='blue')
            ax2.set_title('Humidity', fontsize=12, pad=10)
            ax2.set_ylabel('Humidity (%)', fontsize=10)
            ax2.grid(True, linestyle='--', alpha=0.7)
            ax2.set_facecolor('#f9f9f9')
            
            # Add threshold lines and annotations
            ax2.axhline(y=Config.HUMIDITY_HIGH_THRESHOLD, color='orange', linestyle='--', linewidth=1)
            ax2.axhline(y=Config.HUMIDITY_CRITICAL_THRESHOLD, color='red', linestyle='--', linewidth=1)
            ax2.axhline(y=Config.HUMIDITY_LOW_THRESHOLD, color='blue', linestyle='--', linewidth=1)
            
            ax2.annotate(f'High Threshold ({Config.HUMIDITY_HIGH_THRESHOLD}%)', 
                        xy=(timestamps[0], Config.HUMIDITY_HIGH_THRESHOLD),
                        xytext=(10, 10), textcoords='offset points',
                        color='orange', fontsize=8)
            
            ax2.annotate(f'Critical Threshold ({Config.HUMIDITY_CRITICAL_THRESHOLD}%)', 
                        xy=(timestamps[0], Config.HUMIDITY_CRITICAL_THRESHOLD),
                        xytext=(10, 10), textcoords='offset points',
                        color='red', fontsize=8)
            
            ax2.annotate(f'Low Threshold ({Config.HUMIDITY_LOW_THRESHOLD}%)', 
                        xy=(timestamps[0], Config.HUMIDITY_LOW_THRESHOLD),
                        xytext=(10, -20), textcoords='offset points',
                        color='blue', fontsize=8)
            
            # Rotate x-axis labels
            for ax in fig.axes:
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                ax.tick_params(axis='both', which='major', labelsize=8)
            
            fig.tight_layout(rect=[0, 0, 1, 0.96])
            
            # Embed in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def show_inbox(self):
        """Show alert messages inbox with improved styling"""
        self.clear_content()
        self.current_view = "inbox"
        
        # Header with action buttons
        header_frame = ttk.Frame(self.content_frame)
        header_frame.pack(fill=tk.X, pady=(20, 10))
        
        ttk.Label(
            header_frame,
            text="Alert Inbox",
            style='Title.TLabel'
        ).pack(side=tk.LEFT, padx=20)
        
        # Try to get alerts from server first, fall back to database
        alerts = []
        server_alerts = self.server.get_alerts()
        
        if server_alerts and server_alerts.get('status') == 'success':
            alerts = server_alerts.get('alerts', [])
        else:
            # Fall back to database alerts
            alerts = self.db.get_alerts(unread_only=False)

        if not alerts:
            ttk.Label(self.content_frame, text="No alerts found").pack()
            return
        
        # Create frame for alerts table
        table_frame = ttk.Frame(self.content_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview widget
        tree = ttk.Treeview(
            table_frame,
            columns=('id', 'node_id', 'message', 'severity', 'timestamp'),
            show='headings',
            selectmode='extended'
        )
        
        # Define headings
        tree.heading('id', text='ID')
        tree.heading('node_id', text='Node')
        tree.heading('message', text='Message')
        tree.heading('severity', text='Severity')
        tree.heading('timestamp', text='Timestamp')
        
        # Define column widths
        tree.column('id', width=50, anchor=tk.CENTER)
        tree.column('node_id', width=80, anchor=tk.CENTER)
        tree.column('message', width=400)
        tree.column('severity', width=100, anchor=tk.CENTER)
        tree.column('timestamp', width=200, anchor=tk.CENTER)
        
        # Add data to treeview with color coding
        for alert in alerts:
            alert_id, node_id, message, severity, timestamp = alert
            tags = (severity,)
            
            tree.insert('', tk.END, values=alert, tags=tags)
        
        # Configure tag colors
        tree.tag_configure('critical', background='#ffcccc', font=('Segoe UI', 10, 'bold'))
        tree.tag_configure('high', background='#ffeb99', font=('Segoe UI', 10))
        tree.tag_configure('medium', background='#e6f3ff', font=('Segoe UI', 10))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Action buttons at bottom
        bottom_frame = ttk.Frame(self.content_frame)
        bottom_frame.pack(pady=10)
        
        ttk.Button(
            bottom_frame,
            text="Mark as Read",
            style='TButton',
            command=lambda: self.mark_alert_read(tree)
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            bottom_frame,
            text="Delete Selected",
            style='TButton',
            command=lambda: self.delete_alerts(tree)
        ).pack(side=tk.LEFT, padx=5)
    
    def mark_alert_read(self, tree):
        """Mark selected alerts as read"""
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Warning", "Please select at least one alert")
            return
        
        for item in selected_items:
            alert_id = tree.item(item)['values'][0]
            self.db.mark_alert_as_read(alert_id)
            tree.item(item, tags=('read',))  # Change tag to remove highlight
        
        messagebox.showinfo("Success", f"Marked {len(selected_items)} alerts as read")
    
def show_map(self):
    """Show map placeholder with improved styling"""
    self.clear_content()
    self.current_view = "map"
    
    # Header
    header_frame = ttk.Frame(self.content_frame)
    header_frame.pack(fill=tk.X, pady=(20, 10))
    
    ttk.Label(
        header_frame,
        text="Forest Map",
        style='Title.TLabel'
    ).pack(side=tk.LEFT, padx=20)
    
    # Map placeholder with card style
    map_card = ttk.Frame(
        self.content_frame,
        style='Card.TFrame',
        height=600
    )
    map_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    map_card.pack_propagate(False)
    
    # Placeholder content
    ttk.Label(
        map_card,
        text="🌍 Interactive Forest Map\n\n(Implementation coming soon)",
        style='Header.TLabel',
        justify=tk.CENTER
    ).pack(expand=True)

    def schedule_data_refresh(self):
        """Schedule periodic data refresh if logged in"""
        if hasattr(self, 'current_user') and self.current_user:
            self.refresh_data()
            self.root.after(self.data_refresh_interval, self.schedule_data_refresh)

    def refresh_data(self):
        """Refresh the current view's data"""
        if self.current_view == "dashboard":
            self.show_dashboard()
        elif self.current_view == "data_table":
            self.show_data_table()
        elif self.current_view == "data_charts":
            self.show_data_charts()
        elif self.current_view == "inbox":
            self.show_inbox()
        elif self.current_view == "map":
            self.show_map()
        elif self.current_view == "csv_tools":
            self.show_csv_tools()

if __name__ == "__main__":
    root = tk.Tk()
    
    # Set window icon if available
    try:
        root.iconbitmap('assets/forest_icon.ico')
    except:
        pass
    
    # Configure the main window
    root.geometry("1400x900")
    root.minsize(1200, 800)
    
    # Create and run app
    app = ForestMonitoringApp(root)
    root.mainloop()