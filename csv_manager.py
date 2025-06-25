import csv
import os
import sqlite3
from datetime import datetime
from database import Database

class CSVManager:
    def __init__(self):
        self.data_dir = "data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_csv_files(self):
        """Get list of CSV files in data directory"""
        return [f for f in os.listdir(self.data_dir) if f.endswith('.csv')]
    
    def import_csv(self, filepath):
        """Import CSV data to database"""
        try:
            db = Database()
            imported_rows = 0
            
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        db.add_sensor_data(
                            node_id=int(row.get('node_id', 1)),
                            temperature=float(row['temperature']),
                            humidity=float(row['humidity'])
                        )
                        imported_rows += 1
                    except (ValueError, KeyError) as e:
                        print(f"Skipping row due to error: {e}")
                        continue
            
            # Move imported file to data directory
            filename = os.path.basename(filepath)
            new_path = os.path.join(self.data_dir, filename)
            if not os.path.exists(new_path):
                os.rename(filepath, new_path)
            
            return True, f"Successfully imported {imported_rows} rows from {filename}"
        
        except Exception as e:
            return False, f"Error importing CSV: {str(e)}"
    
    def export_to_csv(self):
        """Export sensor data to CSV"""
        try:
            db = Database()
            data = db.get_sensor_data(limit=None)  # Get all data
            
            if not data:
                return False, "No data available to export"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sensor_data_export_{timestamp}.csv"
            filepath = os.path.join(self.data_dir, filename)
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['node_id', 'temperature', 'humidity', 'timestamp'])
                writer.writerows(data)
            
            return True, f"Successfully exported data to {filename}"
        
        except Exception as e:
            return False, f"Error exporting to CSV: {str(e)}"
    
    def delete_csv(self, filename):
        """Delete a CSV file"""
        try:
            filepath = os.path.join(self.data_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, f"Deleted {filename}"
            return False, f"File not found: {filename}"
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"