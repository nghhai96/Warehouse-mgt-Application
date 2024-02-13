import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import ttk
import sqlite3
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        conn = self.connect('user_credentials.db')       
        self.df_usercred = pd.read_sql_query('SELECT * FROM user_credentials',conn)
        conn.close()
        
        self.title("Login")
        self.geometry("300x150")

        self.username_label = ttk.Label(self, text="Username:")
        self.username_entry = ttk.Entry(self)
        self.password_label = ttk.Label(self, text="Password:")
        self.password_entry = ttk.Entry(self, show="*")
        self.login_button = ttk.Button(self, text="Login", command=self.check_login)

        self.username_label.pack(pady=5)
        self.username_entry.pack(pady=5)
        self.password_label.pack(pady=5)
        self.password_entry.pack(pady=5)
        self.login_button.pack(pady=10)

    def check_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Check if the username and password are correct (replace with your logic)
        if username == "admin" and password == "password":
            self.destroy()  # Close the login window
            main_window = MainWindow()
        else:
            ttk.messagebox.showerror("Login Failed", "Incorrect username or password")

class MainWindow(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Warehouse Management")
        self.geometry("400x300")
        
        # Import Button
        self.import_btn = ttk.Button(self, text="Import", command=self.open_import_window)
        self.import_btn.pack(padx = 6, pady = 10, anchor='nw')
        
        # Export Button
        self.export_btn = ttk.Button(self, text="Export", command=self.open_export_window)
        self.export_btn.pack(padx = 6, pady = 10, anchor='nw')
        
        # Database Edit
        # Choose table from dropdown
        self.edit_tb_btn = ttk.Button(self, text="Edit Table ", command=self.open_database_window)
        self.edit_tb_btn.pack(padx = 6, pady = 10, anchor='nw')
        
        self.tb_list = ['product','stock','warehouse']
        self.tb_dropdown = ttk.Combobox(self,state='readonly',values=self.tb_list,width=20)
        self.tb_dropdown.pack(padx = 6, pady = 10, anchor='nw')
        
        # Show Report Button
        self.report_btn = ttk.Button(self, text='Summary Report', command = self.open_report_window)
        self.report_btn.pack(padx = 6, pady = 10, anchor='nw')
        
        # Reset Tables Button
        self.reset_btn = ttk.Button(self, text = 'Reset Tables', command = self.reset_tables)
        self.reset_btn.pack(side='bottom', anchor="e", padx=8, pady=8)

    def open_import_window(self):
        self.import_window = ImportWindow()
    
    def open_export_window(self):
        self.export_window = ExportWindow()
        
    def open_database_window(self):
        self.tb_choice = self.tb_dropdown.get()
        self.database_window = DatabaseWindow(self, self.tb_dropdown.get())
        
    def open_report_window(self):
        self.open_report_window = ReportWindow()
        
    
    def reset_tables(self):
        conn = sqlite3.connect("sqlite_warehouse_mgt.db")
        cursor = conn.cursor()

        sql_reset_tables = """ 
        DROP TABLE IF EXISTS product;
        DROP TABLE IF EXISTS warehouse;
        DROP TABLE IF EXISTS stock;
        CREATE TABLE IF NOT EXISTS product (
            product_id integer PRIMARY KEY CHECK (typeof(product_id)='integer'),
            name text NOT NULL); 
        CREATE TABLE IF NOT EXISTS warehouse (
            warehouse_id integer PRIMARY KEY CHECK (typeof(warehouse_id)='integer'),
            location text NOT NULL);
        CREATE TABLE IF NOT EXISTS stock (
            id integer PRIMARY KEY CHECK (typeof(id)='integer'),
            product_id integer NOT NULL CHECK (typeof(product_id)='integer'),
            inventory integer NOT NULL CHECK (typeof(inventory)='integer'),
            warehouse_id integer NOT NULL CHECK (typeof(warehouse_id)='integer'));
        INSERT INTO warehouse (warehouse_id, location) VALUES 
            (1, 'New Castle'),
            (2, 'Hamshire'),
            (3, 'Hogwarts');      
        """
        cursor.executescript(sql_reset_tables)
        conn.commit()
        conn.close()
        tk.messagebox.showinfo(title='Tables Reset', message='Table has been reset successfully')

class ImportWindow(tk.Toplevel):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Import")
        self.geometry("300x150")
        # Browse Dir
        self.file_path = tk.StringVar()
        self.dir_box = ttk.Entry(self, textvariable=self.file_path, width = 200)
        self.dir_box.pack(padx = 6, pady = 10)
        self.dir_btn = ttk.Button(self, text="Browse Folder", command=self.file_browse)
        self.dir_btn.pack(padx = 6, pady = 10)
        # Import into sqlite_stock.db
        self.import_btn = ttk.Button(self, text = "Import!", command = self.import_cmd)
        self.import_btn.pack(padx = 6, pady = 10)
        
        
                     
    def file_browse(self):
        self.dirname = askopenfilename(filetypes=[("Excel files", ".xlsx .xls")])
        if self.dirname:
            self.file_path.set(self.dirname)
    
    # Add items into inventory 
    def import_cmd(self):
        if not self.file_path: return
        try:
            df = pd.read_excel(self.file_path.get())
            conn = sqlite3.connect('sqlite_warehouse_mgt.db')
            cursor = conn.cursor()
            
            # Iterate through excel rows
            for index,row in df.iterrows():
                item_id = row['id']
                item_name = row['product']
                quantity = row['inventory']
                warehouse_id = row['warehouse_id']
                
                # Check if item exist in *stock* table, if so updates inventory, else adds new entries
                cursor.execute("SELECT * FROM stock WHERE id = ? AND warehouse_id = ?", (item_id, warehouse_id))
                ext_item = cursor.fetchone()
                if ext_item:
                    new_inv = ext_item[1] + quantity
                    cursor.execute('UPDATE stock SET inventory = ? WHERE product_id = ?', (new_inv, item_id))
                else:
                    cursor.execute('INSERT INTO stock (product_id, inventory, warehouse_id) values (?,?,?)', (item_id, quantity, warehouse_id))
                    
                # Check if item exist in *product* table, if so updates inventory, else adds new entries
                cursor.execute("SELECT * FROM product WHERE product_id = ?", (item_id,))
                ext_item = cursor.fetchone()
                if not ext_item:
                    cursor.execute('INSERT INTO product (product_id, name) values (?,?)', (item_id, item_name))
            tk.messagebox.showinfo(title='Import', message='File Imported')           
            conn.commit()
            conn.close()
        except Exception as e:
            tk.messagebox.showerror(title='Error', message=f'An error occurred: {e}')

class ExportWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Export")
        self.geometry("300x80")
        # Choose table from dropdown
        self.tb_list = ['product','stock','warehouse','combined']
        self.tb_dropdown = ttk.Combobox(self,state='readonly',values=self.tb_list,width=150)
        self.tb_dropdown.pack(padx = 6, pady = 10)
        # Export Button
        self.export_btn = ttk.Button(self,text='Export',command=self.export)
        self.export_btn.pack(padx = 6, pady = 10)
        
    def export(self):
        try:
            conn = sqlite3.connect('sqlite_warehouse_mgt.db')
            # Export each table separately or as a combined report
            if self.tb_dropdown.get() == 'combined':
                sql = '''
                SELECT product_id, name, inventory, location
                FROM stock
                LEFT OUTER JOIN product ON stock.product_id = product.product_id
                LEFT OUTER JOIN warehouse ON stock.warehouse_id = warehouse.warehouse_id 
                '''
                df = pd.read_sql_query(sql,conn)
                self.output_file = 'overview_report.xlsx'
                df.to_excel(self.output_file, index=False)
                conn.close()
            else:
                sql = f'''
                SELECT * FROM {self.tb_dropdown.get()}
                '''
                df = pd.read_sql_query(sql,conn)
                self.output_file = self.tb_dropdown.get() + '_report.xlsx'
                df.to_excel(self.output_file, index=False)
            conn.close()
            tk.messagebox.showinfo(title='Export', message='File Exported')
        except Exception as e:
            tk.messagebox.showerror(title='Error', message=f'An error occurred: {e}')
            
class DatabaseWindow(tk.Toplevel):
    def __init__(self, master, tb_choice, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title("Database Editor")
        self.tb_choice = tb_choice
        # Fetch Data
        self.conn = sqlite3.connect('sqlite_warehouse_mgt.db') 
        sql = f'SELECT * FROM {self.tb_choice}'
        self.df_current = pd.read_sql(sql, self.conn)
        self.conn.close()
        
        # Display Table
        self.table_frame = ttk.Frame(self)
        self.table_frame.pack()
        self.view(self, self.df_current)
        
        # Add Row Btn
        self.add_row_btn = ttk.Button(self, text = 'Add Row', command = self.add_row)
        self.add_row_btn.pack(pady=4)
        
        # Delete Row Btn
        self.dlt_btn = ttk.Button(self, text = 'Delete Row', command = self.delete_selected_row)
        self.dlt_btn.pack(pady=4)
        
        # Edit Row Btn
        self.edit_btn = ttk.Button(self, text= 'Edit Row', command = self.edit_selected_row)
        self.edit_btn.pack(pady=4)
        
        # Commit Changes Btn
        self.commit_btn = ttk.Button(self, text='Commit', command=self.commit_changes)
        self.commit_btn.pack(pady=4)
        
        # View Dependencies Btn
        self.dpd_btn = ttk.Button(self, text='View Dependents', command = self.view_dependencies)
        self.dpd_btn.pack(pady=4)
        
    
    def add_row(self):
        # Open a new window for adding a new row
        add_window = tk.Toplevel(self)
        add_window.geometry('300x300')
        # Create entries for each column
        entry_widgets = []
        for col in self.df_current.columns:
            label = tk.Label(add_window, text=f'{col}: ')
            label.pack(padx=5, pady=5)
            entry_var = tk.StringVar()
            entry = tk.Entry(add_window, textvariable=entry_var)
            entry.pack(padx=5, pady=5)
            entry_widgets.append(entry_var)

        def confirm_add_row():
            # Get the values from the entry widgets
            new_values = [entry_var.get() for entry_var in entry_widgets]

            # insert into treeview and df
            self.tree.insert('', 'end', text=str(len(self.df_current)), values=new_values)
            self.df_current.loc[len(self.df_current)] = new_values
            add_window.destroy()
            
        # Confirm Add row btn
        add_button = tk.Button(add_window, text="Add Row", command=confirm_add_row)
        add_button.pack(pady=10)
        
        
    def delete_selected_row(self):
        selected_item = self.tree.selection()
        if selected_item:
            index = int(selected_item[0][1:]) - 1 # Get idx for df from tree
            # Delete from df and tree
            self.df_current.drop(index, inplace=True) 
            self.tree.delete(selected_item)

    def edit_selected_row(self):
        selected_item = self.tree.selection()
        if selected_item:
            item_id = selected_item[0]
            current_values = self.tree.item(item_id, 'values')

            edit_window = tk.Toplevel(self)
            edit_window.geometry('300x300')
            entry_widgets = []
            for idx, value in enumerate(current_values):
                label = tk.Label(edit_window, text=f'{self.df_current.columns[idx]}: ')
                label.pack(padx=5, pady=5)
                entry_var = tk.StringVar(value=str(value))
                entry = tk.Entry(edit_window, textvariable=entry_var)
                entry.pack(padx=5, pady=5)
                entry_widgets.append(entry_var)
            
           
            def update_values():
                # Get the updated values from the entry widgets
                new_values = [entry_var.get() for entry_var in entry_widgets]

                # Update treeview and df
                self.tree.item(item_id, values=new_values)
                self.df_current.loc[item_id] = new_values
                edit_window.destroy()
            
            update_button = tk.Button(edit_window, text="Update", command=update_values)
            update_button.pack(pady=10)
            
    def commit_changes(self):
        result = tk.messagebox.askquestion(title='Commit Changes', type='yesno', message='Are you sure you want to apply changes to the Database?')
        if result =='yes':
            try:
                self.conn = sqlite3.connect('sqlite_warehouse_mgt.db')
                cursor = self.conn.cursor()
                cursor.execute(f'DELETE FROM {self.tb_choice}')               
                self.df_current.to_sql(self.tb_choice,self.conn,index=False,if_exists='append')
                self.conn.commit()
                self.conn.close()
            except Exception as e:
                tk.messagebox.showerror(title='Error', message=f'An error occurred: {e}')

    def view_dependencies(self):
        conn = sqlite3.connect('sqlite_warehouse_mgt.db')
        
        # Retrieve foriegn tables
        sql = f'''
                SELECT name FROM sqlite_schema
                WHERE type='table'
                ORDER BY name;
            '''
        df_tb_name = pd.read_sql_query(sql, conn)
        df_tb_name = df_tb_name[df_tb_name['name'] != self.tb_choice]
        df_tb_name.reset_index(drop=True, inplace=True)
        df_tb_list = []
        for tb_name in df_tb_name['name']:
            sql = f'''
            SELECT * FROM {tb_name}
            '''
            df_tb_list.append(pd.read_sql_query(sql, conn))
        
        # Display dependencies in a subwindow
        selected_item = self.tree.selection()
        if selected_item:
            item_id = selected_item[0]
            current_values = self.tree.item(item_id, 'values')
            
            # convert to df
            # current_values = [[values] for values in current_values]
            df_current_value = pd.DataFrame(data=[current_values], columns=self.df_current.columns.tolist())
            
            dpc_window = tk.Toplevel(self)
            
            for idx, df_table in enumerate(df_tb_list):
                # get common column
                jointer = [col for col in df_table.columns.to_list() if col in df_current_value.columns.to_list()]
                if jointer:
                    label = ttk.Label(dpc_window, text=f"{df_tb_name.at[idx,'name'].capitalize()} table", font=('Ariel',16))
                    label.pack(padx=5, pady=5)
                    jointer = jointer[0]
                    
                    df_dpd_tree = df_table[df_table[jointer] == int(df_current_value.at[0,jointer])]
                    self.tree_dpd = ttk.Treeview(dpc_window, columns = tuple(df_dpd_tree.columns), show='headings')

                    # Add columns to the Treeview
                    for col in df_dpd_tree.columns:
                        self.tree_dpd.column(col, anchor='center', width=150)
                        self.tree_dpd.heading(col, text=col, anchor='center')

                    # Insert data into the Treeview
                    for index, row in df_dpd_tree.iterrows():
                        self.tree_dpd.insert('',index, values=tuple(row))
                    self.tree_dpd.pack(padx=8, pady=8)

        
    def clear_table(self):
        for table in self.table_frame.winfo_children():
            table.destroy()
            
    def view(self,window,df):  #View Dataframe
        # Create Table tree view
        self.tree = ttk.Treeview(window, columns = tuple(df.columns), show='headings')

        # Add columns to the Treeview
        for col in df.columns:
            self.tree.column(col, anchor='center', width=150)
            self.tree.heading(col, text=col, anchor='center')

        # Insert data into the Treeview
        for index, row in df.iterrows():
            self.tree.insert('',index, values=tuple(row))
        self.tree.pack(padx=8, pady=8)
    
    
class ReportWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title('Report')
        conn = sqlite3.connect('sqlite_warehouse_mgt.db')
        
        fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(10, 8))
        
        # Items with most quantity Bar Chart
        sql = '''
        SELECT product.product_id AS Product, sum(stock.inventory) as Total_Inventory
        FROM stock JOIN product ON product.product_id = stock.product_id
        GROUP BY product.name
        ORDER BY sum(stock.inventory) DESC
        LIMIT 5;
        '''
        df_bar_chart = pd.read_sql_query(sql,conn)
        axes[0].bar(df_bar_chart['Product'].astype(str),df_bar_chart['Total_Inventory'])
        axes[0].set_title('Top 10 Items Count')
    
        
        # Warehouse capacity percentage
        sql = '''
        SELECT warehouse.location AS Location, sum(stock.inventory) as Inventory
        FROM warehouse JOIN stock ON warehouse.warehouse_id = stock.warehouse_id
        GROUP BY warehouse.location
        '''
        df_pie_chart = pd.read_sql_query(sql,conn)
        axes[1].pie(df_pie_chart['Inventory'], labels=df_pie_chart['Location'], autopct='%1.1f%%', startangle=90, colors=['lightcoral', 'lightskyblue', 'gold'])
        axes[1].axis('equal')
        axes[1].set_title('Warehouse Inventory Percentage')
        
        # Warehouse Product percentage
        sql = '''
        SELECT warehouse.location AS Location, count(stock.product_id) AS Count
        FROM warehouse JOIN stock ON warehouse.warehouse_id = stock.warehouse_id
        GROUP BY warehouse.location
        '''
        df_pie_chart = pd.read_sql_query(sql,conn)
        axes[2].pie(df_pie_chart['Count'], labels=df_pie_chart['Location'], autopct='%1.1f%%', startangle=90, colors=['darkorange', 'mediumseagreen', 'firebrick'])
        axes[2].axis('equal')
        axes[2].set_title('Warehouse Product Percentage')
        
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=5,side='top', fill='both', expand=1)
    
        
if __name__ == "__main__":
    main_window = MainWindow()
    main_window.mainloop()


