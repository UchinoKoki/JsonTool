import customtkinter
from tkinter import ttk, filedialog
import json
import copy

class JsonEditorApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("JSON Editor")
        self.geometry("1000x700")
        
        self.current_file_path = None
        self.json_data = None
        self.node_map = {}
        self.current_edit_path = None
        self.editor_widget = None
        self.is_locked = False

        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.top_frame = customtkinter.CTkFrame(self, height=50, corner_radius=0)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.btn_load = customtkinter.CTkButton(self.top_frame, text="Load File", command=self.load_file)
        self.btn_load.pack(side="left", padx=5, pady=5)
        self.btn_new = customtkinter.CTkButton(self.top_frame, text="New File", command=self.new_file)
        self.btn_new.pack(side="left", padx=5, pady=5)
        self.btn_save = customtkinter.CTkButton(self.top_frame, text="Save", command=self.save_file)
        self.btn_save.pack(side="left", padx=5, pady=5)
        
        self.btn_lock = customtkinter.CTkButton(self.top_frame, text="Lock Structure", command=self.toggle_lock)
        self.btn_lock.pack(side="right", padx=5, pady=5)

        self.tree_frame = customtkinter.CTkFrame(self)
        self.tree_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        self.update_treeview_style()

        self.tree = ttk.Treeview(self.tree_frame, style="Treeview", columns=("Value"), show="tree headings")
        self.tree.heading("#0", text="Key / Index")
        self.tree.heading("Value", text="Value")
        self.tree.column("Value", width=150)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.editor_frame = customtkinter.CTkFrame(self)
        self.editor_frame.grid(row=1, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.editor_frame.grid_columnconfigure(0, weight=1)

        self.editor_label = customtkinter.CTkLabel(self.editor_frame, text="Select an item from the tree to edit.", font=("", 16))
        self.editor_label.pack(padx=20, pady=20, anchor="center")

        self.status_bar = customtkinter.CTkLabel(self, text="No file loaded.", anchor="w")
        self.status_bar.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")

        self.bind("<Configure>", self.on_theme_change)

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.btn_lock.configure(text="Unlock Structure", fg_color="red")
            self.status_bar.configure(text="Structure is LOCKED. Editing is restricted to values only.")
        else:
            self.btn_lock.configure(text="Lock Structure", fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
            self.status_bar.configure(text="Structure is UNLOCKED. Full editing enabled.")
        # Refresh editor view to show/hide buttons
        self.on_tree_select(None)

    def update_treeview_style(self, event=None):
        bg_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self._apply_appearance_mode(customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
        style = ttk.Style()
        style.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, rowheight=25)
        style.configure("Treeview.Heading", background=bg_color, foreground=text_color, font=('Arial', 10, 'bold'))
        style.map('Treeview', background=[('selected', selected_color)])
        style.map('Treeview.Heading', background=[('active', bg_color)])

    def on_theme_change(self, event=None):
        self.after(100, self.update_treeview_style)

    def load_file(self):
        file_path = filedialog.askopenfilename(title="Open JSON File", filetypes=(("JSON files", "*.json"), ("All files", "*.*")))
        if not file_path: return
        self.current_file_path = file_path
        try:
            with open(file_path, 'r', encoding='utf-8') as f: self.json_data = json.load(f)
            self.status_bar.configure(text=f"Loaded: {self.current_file_path}")
            self.populate_treeview()
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self.status_bar.configure(text=f"Error: Failed to read or parse file. {e}")
            self.json_data = None
            for i in self.tree.get_children(): self.tree.delete(i)

    def new_file(self):
        self.current_file_path = None
        self.json_data = {"new_key": "new_value", "is_active": True, "items": [{"id": 1, "name": "First"}, {"id": 2, "name": "Second"}]}
        self.status_bar.configure(text="New file created. Edit and save.")
        self.populate_treeview()
        for widget in self.editor_frame.winfo_children(): widget.destroy()

    def save_file(self):
        if self.json_data is None:
            self.status_bar.configure(text="No data to save.")
            return
        
        save_path = self.current_file_path
        if not save_path:
            save_path = filedialog.asksaveasfilename(title="Save JSON File", defaultextension=".json", filetypes=(("JSON files", "*.json"), ("All files", "*.*")))
        
        if not save_path:
            self.status_bar.configure(text="Save cancelled.")
            return

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.json_data, f, indent=4, ensure_ascii=False)
            self.current_file_path = save_path
            self.status_bar.configure(text=f"File saved successfully to {save_path}")
        except Exception as e:
            self.status_bar.configure(text=f"Error saving file: {e}")

    def populate_treeview(self):
        focused_id = self.tree.focus()
        for i in self.tree.get_children(): self.tree.delete(i)
        self.node_map.clear()
        if self.json_data is not None:
            self._populate_node("", self.json_data, [])
        
        # Try to re-select the previously focused item
        if focused_id and focused_id in self.tree.get_children(self.tree.parent(focused_id)):
             self.tree.focus(focused_id)
             self.tree.selection_set(focused_id)

    def _populate_node(self, parent_id, data, path):
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = path + [key]
                if isinstance(value, (dict, list)):
                    node_id = self.tree.insert(parent_id, "end", text=key, open=True)
                    self.node_map[node_id] = new_path
                    self._populate_node(node_id, value, new_path)
                else:
                    node_id = self.tree.insert(parent_id, "end", text=key, values=(self.format_value(value),), open=False)
                    self.node_map[node_id] = new_path
        elif isinstance(data, list):
            for index, item in enumerate(data):
                new_path = path + [index]
                text = f"[{index}]"
                if isinstance(item, (dict, list)):
                    node_id = self.tree.insert(parent_id, "end", text=text, open=True)
                    self.node_map[node_id] = new_path
                    self._populate_node(node_id, item, new_path)
                else:
                    node_id = self.tree.insert(parent_id, "end", text=text, values=(self.format_value(item),), open=False)
                    self.node_map[node_id] = new_path

    def format_value(self, value):
        if value is None: return "null"
        if isinstance(value, bool): return str(value).lower()
        return str(value)

    def on_tree_select(self, event):
        selected_id = self.tree.focus()
        if not selected_id:
            for widget in self.editor_frame.winfo_children(): widget.destroy()
            self.editor_label = customtkinter.CTkLabel(self.editor_frame, text="Select an item from the tree to edit.", font=("", 16))
            self.editor_label.pack(padx=20, pady=20, anchor="center")
            return

        self.current_edit_path = self.node_map.get(selected_id)
        if self.current_edit_path is None: return
        value = self.get_value_from_path(self.current_edit_path)
        self.build_editor(value)

    def get_value_from_path(self, path):
        value = self.json_data
        for key in path: value = value[key]
        return value

    def build_editor(self, value):
        for widget in self.editor_frame.winfo_children(): widget.destroy()
        self.editor_widget = None

        editor_container = customtkinter.CTkFrame(self.editor_frame)
        editor_container.pack(padx=20, pady=20, fill="x")

        lbl_type = customtkinter.CTkLabel(editor_container, text=f"Type: {type(value).__name__}", font=("", 12))
        lbl_type.pack(pady=(0, 10), anchor="w")

        if isinstance(value, bool):
            self.editor_widget = customtkinter.CTkCheckBox(editor_container, text="", onvalue=True, offvalue=False)
            self.editor_widget.select() if value else self.editor_widget.deselect()
            self.editor_widget.pack(anchor="w")
        elif isinstance(value, (int, float, str)):
            self.editor_widget = customtkinter.CTkEntry(editor_container, font=("", 14))
            self.editor_widget.insert(0, str(value))
            self.editor_widget.pack(fill="x")
        elif value is None:
            self.editor_widget = customtkinter.CTkLabel(editor_container, text="null (read-only)")
            self.editor_widget.pack(anchor="w")
        elif isinstance(value, (dict, list)):
            self.build_container_editor(editor_container, value)
        
        if self.editor_widget and not isinstance(value, (dict, list, type(None))):
             update_btn = customtkinter.CTkButton(editor_container, text="Update Value", command=self.update_value)
             update_btn.pack(pady=10, side="left")

    def build_container_editor(self, parent, value):
        action_frame = customtkinter.CTkFrame(parent)
        action_frame.pack(fill="x", pady=5)
        
        btn_state = "disabled" if self.is_locked else "normal"

        if isinstance(value, list):
            btn_add = customtkinter.CTkButton(action_frame, text="Add Element", command=self.add_element, state=btn_state)
            btn_add.pack(side="left", padx=5)
        elif isinstance(value, dict):
            btn_add = customtkinter.CTkButton(action_frame, text="Add Key-Value", command=self.add_key_value, state=btn_state)
            btn_add.pack(side="left", padx=5)
        
        btn_del = customtkinter.CTkButton(action_frame, text="Delete Selected Node", command=self.delete_node, fg_color="red", state=btn_state)
        btn_del.pack(side="left", padx=5)

    def add_element(self):
        if self.is_locked: self.status_bar.configure(text="Structure is locked."); return
        if not self.current_edit_path: return
        container = self.get_value_from_path(self.current_edit_path)
        if isinstance(container, list):
            if container and isinstance(container[-1], dict):
                new_element = copy.deepcopy(container[-1])
            else:
                new_element = "new_value"
            container.append(new_element)
            self.status_bar.configure(text="Element added.")
            self.populate_treeview()

    def add_key_value(self):
        if self.is_locked: self.status_bar.configure(text="Structure is locked."); return
        if not self.current_edit_path: return
        dialog = customtkinter.CTkInputDialog(text="Enter new key:", title="Add Key-Value")
        new_key = dialog.get_input()
        if new_key:
            container = self.get_value_from_path(self.current_edit_path)
            if isinstance(container, dict):
                if new_key in container:
                    self.status_bar.configure(text=f"Error: Key '{new_key}' already exists.")
                else:
                    container[new_key] = "new_value"
                    self.status_bar.configure(text="Key-value pair added.")
                    self.populate_treeview()

    def delete_node(self):
        if self.is_locked: self.status_bar.configure(text="Structure is locked."); return
        if not self.current_edit_path or len(self.current_edit_path) == 0:
            self.status_bar.configure(text="Cannot delete the root element.")
            return
        
        parent_path = self.current_edit_path[:-1]
        node_to_delete_key = self.current_edit_path[-1]
        parent_container = self.get_value_from_path(parent_path)

        del parent_container[node_to_delete_key]
        
        self.status_bar.configure(text=f"Deleted: {node_to_delete_key}")
        self.current_edit_path = None
        for widget in self.editor_frame.winfo_children(): widget.destroy()
        self.populate_treeview()

    def update_value(self):
        if not self.current_edit_path or self.editor_widget is None: return
        
        original_value = self.get_value_from_path(self.current_edit_path)
        raw_new_value = self.get_widget_value()

        try:
            new_value = raw_new_value
            if self.is_locked and not isinstance(original_value, bool):
                # Enforce type strictly if locked
                if isinstance(original_value, (int, float, str)):
                    new_value = type(original_value)(raw_new_value)

            # Update data in memory
            data_ptr = self.json_data
            for key in self.current_edit_path[:-1]: data_ptr = data_ptr[key]
            data_ptr[self.current_edit_path[-1]] = new_value
            
            # Update tree view
            selected_id = self.tree.focus()
            if selected_id: self.tree.item(selected_id, values=(self.format_value(new_value),))
            
            self.status_bar.configure(text="Value updated successfully.")
        except (ValueError, TypeError):
            self.status_bar.configure(text=f"Error: Value must be of type '{type(original_value).__name__}'.")

    def get_widget_value(self):
        original_value = self.get_value_from_path(self.current_edit_path)
        if isinstance(original_value, bool):
            return self.editor_widget.get() == 1
        return self.editor_widget.get()

if __name__ == "__main__":
    app = JsonEditorApp()
    app.mainloop()
