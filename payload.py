import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
import json
import os

DATA_FILE = "payload_data.json"

class PayloadManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("by Ting")

        self.tree = ttk.Treeview(root)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_node_select)
        self.tree.bind("<Double-1>", self.copy_to_clipboard)

        # 右侧区域
        right_frame = tk.Frame(root, bg="white")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 顶部按钮区域
        btn_frame = tk.Frame(right_frame, bg="white")
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        copy_btn = tk.Button(btn_frame, text="复制", command=self.copy_from_textarea)
        copy_btn.pack(side=tk.LEFT, padx=5)

        paste_btn = tk.Button(btn_frame, text="粘贴", command=self.paste_to_textarea)
        paste_btn.pack(side=tk.LEFT, padx=5)

        add_btn = tk.Button(btn_frame, text="添加", command=self.toggle_input_area)
        add_btn.pack(side=tk.LEFT, padx=5)

        remove_btn = tk.Button(btn_frame, text="删除输入内容", command=self.remove_payloads)
        remove_btn.pack(side=tk.LEFT, padx=5)

        delete_file_btn = tk.Button(btn_frame, text="删除当前文件", command=self.delete_file)
        delete_file_btn.pack(side=tk.LEFT, padx=5)

        # 文件内容展示框
        self.text_area = tk.Text(right_frame, wrap=tk.WORD, bg="white", fg="black", insertbackground="black", height=15)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 5))

        # 输入内容输入框（默认隐藏）
        self.input_area = tk.Text(right_frame, wrap=tk.WORD, bg="white", fg="blue", insertbackground="blue", height=6)
        self.input_area.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))
        self.input_area.pack_forget()

        # 菜单
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)
        file_menu = tk.Menu(self.menu, tearoff=False)
        file_menu.add_command(label="添加目录", command=self.add_folder)
        file_menu.add_command(label="添加文件", command=self.add_file)
        file_menu.add_command(label="批量导入 Payload", command=self.import_payloads)
        self.menu.add_cascade(label="操作", menu=file_menu)

        self.tree_data = {}
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.tree_data = json.load(f)
        self.populate_tree()

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tree_data, f, indent=4, ensure_ascii=False)

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())

        def add_items(parent, dictionary):
            for key, value in dictionary.items():
                oid = self.tree.insert(parent, "end", text=key)
                if isinstance(value, dict):
                    add_items(oid, value)

        add_items("", self.tree_data)

    def get_node_path(self, item):
        path = []
        while item:
            path.insert(0, self.tree.item(item)["text"])
            item = self.tree.parent(item)
        return path

    def get_node_data(self, path):
        data = self.tree_data
        for p in path:
            data = data[p]
        return data

    def on_node_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        path = self.get_node_path(selected[0])
        try:
            data = self.get_node_data(path)
            if isinstance(data, str):
                self.text_area.delete(1.0, tk.END)
                self.text_area.insert(tk.END, data)
        except Exception:
            pass

    def copy_to_clipboard(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        path = self.get_node_path(selected[0])
        try:
            data = self.get_node_data(path)
            if isinstance(data, str):
                self.root.clipboard_clear()
                self.root.clipboard_append(data)
                self.root.update()
                messagebox.showinfo("提示", "Payload 已复制到剪贴板！")
        except Exception:
            pass

    def copy_from_textarea(self):
        content = self.text_area.get(1.0, tk.END).strip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.root.update()
            messagebox.showinfo("提示", "内容已复制到剪贴板！")

    def paste_to_textarea(self):
        try:
            pasted = self.root.clipboard_get()
            self.text_area.insert(tk.INSERT, pasted)
        except Exception:
            pass

    def toggle_input_area(self):
        if self.input_area.winfo_ismapped():
            self.add_payload_from_input()
            self.input_area.delete(1.0, tk.END)
            self.input_area.pack_forget()
        else:
            self.input_area.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

    def add_payload_from_input(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个文件节点")
            return
        path = self.get_node_path(selected[0])
        data = self.tree_data
        for p in path[:-1]:
            data = data[p]
        key = path[-1]
        if not isinstance(data.get(key), str):
            messagebox.showerror("错误", "目标不是文件")
            return

        original_lines = data[key].splitlines()
        new_lines = self.input_area.get(1.0, tk.END).splitlines()

        for line in new_lines:
            line = line.strip()
            if line and line not in original_lines:
                original_lines.append(line)

        data[key] = "\n".join(original_lines)
        self.save_data()
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, data[key])
        messagebox.showinfo("提示", "Payload 已添加！")

    def remove_payloads(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个文件节点")
            return

        # 显示输入框（修复点）
        if not self.input_area.winfo_ismapped():
            self.input_area.pack(fill=tk.BOTH, expand=False, padx=10, pady=(0, 10))

        path = self.get_node_path(selected[0])
        data = self.tree_data
        for p in path[:-1]:
            data = data[p]
        key = path[-1]

        if not isinstance(data.get(key), str):
            messagebox.showerror("错误", "目标不是文件")
            return

        current_lines = data[key].splitlines()
        lines_to_delete = self.input_area.get(1.0, tk.END).splitlines()

        new_lines = [line for line in current_lines if line not in lines_to_delete]

        if len(new_lines) == len(current_lines):
            messagebox.showinfo("提示", "未找到任何可删除的内容")
            return

        data[key] = "\n".join(new_lines)
        self.save_data()

        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(tk.END, data[key])
        self.input_area.delete(1.0, tk.END)

        messagebox.showinfo("提示", "指定内容已删除")

    def delete_file(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的文件")
            return
        path = self.get_node_path(selected[0])
        if not path:
            return
        data = self.tree_data
        for p in path[:-1]:
            data = data.get(p, {})
        key = path[-1]
        if key in data:
            confirm = messagebox.askyesno("确认删除", f"确定要删除文件 '{key}' 吗？")
            if confirm:
                del data[key]
                self.save_data()
                self.populate_tree()
                self.text_area.delete(1.0, tk.END)
                self.input_area.delete(1.0, tk.END)

    def add_folder(self):
        selected = self.tree.selection()
        folder_name = simpledialog.askstring("添加目录", "请输入目录名称：")
        if not folder_name:
            return
        if selected:
            path = self.get_node_path(selected[0])
        else:
            path = []
        data = self.tree_data
        for p in path:
            data = data.setdefault(p, {})
        data[folder_name] = {}
        self.save_data()
        self.populate_tree()

    def add_file(self):
        selected = self.tree.selection()
        file_name = simpledialog.askstring("添加文件", "请输入文件名称：")
        if not file_name:
            return
        if selected:
            path = self.get_node_path(selected[0])
        else:
            path = []
        data = self.tree_data
        for p in path:
            data = data.setdefault(p, {})
        data[file_name] = ""
        self.save_data()
        self.populate_tree()

    def import_payloads(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择一个文件节点")
            return
        file_path = filedialog.askopenfilename(title="选择文本文件", filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return
        with open(file_path, "r", encoding="utf-8") as f:
            payloads = f.read().splitlines()
        path = self.get_node_path(selected[0])
        data = self.tree_data
        for p in path[:-1]:
            data = data[p]
        key = path[-1]
        if not isinstance(data.get(key), str):
            messagebox.showerror("错误", "目标不是文件")
            return

        current_lines = data[key].splitlines()
        for line in payloads:
            line = line.strip()
            if line and line not in current_lines:
                current_lines.append(line)

        data[key] = "\n".join(current_lines)
        self.save_data()
        self.text_area.insert(tk.END, "\n".join(payloads) + "\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = PayloadManagerApp(root)
    root.geometry("1000x600")
    root.mainloop()
