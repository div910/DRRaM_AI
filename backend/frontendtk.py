import tkinter as tk
import requests
from tkinter import messagebox

class DestinationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("destination Management System")
        
        self.latitude_label = tk.Label(root, text="Latitude:")
        self.latitude_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.latitude_entry = tk.Entry(root)
        self.latitude_entry.grid(row=0, column=1, padx=10, pady=5)
        
        self.longitude_label = tk.Label(root, text="Longitude:")
        self.longitude_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.longitude_entry = tk.Entry(root)
        self.longitude_entry.grid(row=1, column=1, padx=10, pady=5)
        
        self.deadline_label = tk.Label(root, text="Deadline:")
        self.deadline_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.deadline_entry = tk.Entry(root)
        self.deadline_entry.grid(row=2, column=1, padx=10, pady=5)
        
        self.submit_button = tk.Button(root, text="Submit", command=self.submit_destination)
        self.submit_button.grid(row=3, columnspan=2, padx=10, pady=10)
    
    def submit_destination(self):
        latitude = self.latitude_entry.get()
        longitude = self.longitude_entry.get()
        deadline = self.deadline_entry.get()
        
        if not latitude or not longitude or not deadline:
            tk.messagebox.showerror("Error", "Please fill in all fields.")
            return
        
        data = {
            "latitude": latitude,
            "longitude": longitude,
            "deadline": deadline
        }
        
        try:
            response = requests.post("http://127.0.0.1:5000/create_destination", json=data)
            if response.status_code == 201:
                tk.messagebox.showinfo("Success", "Destination added successfully!")
                self.clear_fields()
            else:
                tk.messagebox.showerror("Error", "Failed to add destination.")
        except Exception as e:
            tk.messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def clear_fields(self):
        self.latitude_entry.delete(0, tk.END)
        self.longitude_entry.delete(0, tk.END)
        self.deadline_entry.delete(0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = DestinationApp(root)
    root.mainloop()
