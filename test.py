import tkinter as tk
from tkinter import messagebox, font
from tkinter import ttk
from tkinter import filedialog
import json
import schedule
import time
import threading
from datetime import datetime

# wxauto库存在并且正确导入了WeChat类
from wxauto import WeChat

# 初始化微信自动化对象
wx = WeChat()

# 创建窗口
root = tk.Tk()
root.title("定时发送消息")
root.geometry("800x600")
root.configure(bg="#f0f0f0")

# 存储配置信息的数据结构
scheduled_times = []

# 显示当前时间的标签
current_time_label = ttk.Label(root, text="", font=("Arial", 12))
current_time_label.pack(pady=5)

# 进度指示器标签
progress_label = ttk.Label(root, text="", font=("Arial", 12))
progress_label.pack(pady=5)

# 显示当前时间
def display_current_time():
    current_time_label.config(text=f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 定期更新时间标签
def update_time_label():
    display_current_time()
    root.after(1000, update_time_label)  # 每秒更新一次

# 进度指示器函数
def progress_indicator():
    indicators = ['-', '\\', '|', '/']
    idx = 0
    while running.is_set():
        progress_label.config(text=f"正在运行... {indicators[idx % len(indicators)]}")
        idx += 1
        time.sleep(0.1)

# 添加定时任务的函数
def add_scheduled_time():
    time_str = entry_time.get()
    contact_name = entry_contact.get()
    message = entry_message.get()
    
    if not time_str or not contact_name or not message:
        messagebox.showerror("错误", "时间、联系人或消息不能为空")
        return
    
    # 将时间字符串转换为时间元组
    try:
        time.strptime(time_str, "%H:%M")
    except ValueError:
        messagebox.showerror("错误", "时间格式错误")
        return
    
    # 添加到列表
    scheduled_times.append({
        'time': time_str,
        'contact': contact_name,
        'message': message
    })
    
    # 更新表格
    update_treeview()
    
    # 清空输入框
    clear_entries()
    
    # 调度任务
    schedule.every().day.at(time_str).do(send_msg_to_contact, contact_name, message)
    
    messagebox.showinfo("成功", "定时任务已添加")

# 编辑定时任务
def edit_scheduled_time():
    selected_item = treeview.selection()
    if not selected_item:
        messagebox.showwarning("警告", "请选择要编辑的条目")
        return
    
    item = treeview.item(selected_item)
    values = item['values']
    index = int(values[0])
    
    time_str = entry_time.get()
    contact_name = entry_contact.get()
    message = entry_message.get()
    
    if not time_str or not contact_name or not message:
        messagebox.showerror("错误", "时间、联系人或消息不能为空")
        return
    
    try:
        time.strptime(time_str, "%H:%M")
    except ValueError:
        messagebox.showerror("错误", "时间格式错误")
        return
    
    scheduled_times[index] = {
        'time': time_str,
        'contact': contact_name,
        'message': message
    }
    
    # 更新表格
    update_treeview()
    
    # 清空输入框
    clear_entries()
    
    # 重新调度任务
    schedule.clear()  # 清除旧的任务
    for task in scheduled_times:
        schedule.every().day.at(task['time']).do(send_msg_to_contact, task['contact'], task['message'])
    
    messagebox.showinfo("成功", "定时任务已更新")

# 删除定时任务
def delete_scheduled_time():
    selected_item = treeview.selection()
    if not selected_item:
        messagebox.showwarning("警告", "请选择要删除的条目")
        return
    
    item = treeview.item(selected_item)
    values = item['values']
    index = int(values[0])
    
    del scheduled_times[index]
    
    # 更新表格
    update_treeview()
    
    # 重新调度任务
    schedule.clear()  # 清除旧的任务
    for task in scheduled_times:
        schedule.every().day.at(task['time']).do(send_msg_to_contact, task['contact'], task['message'])
    
    messagebox.showinfo("成功", "定时任务已删除")

# 显示当前选中的任务信息
def on_select(event):
    selected_item = treeview.selection()
    if selected_item:
        item = treeview.item(selected_item)
        values = item['values']
        index = int(values[0])
        current_task = scheduled_times[index]
        entry_time.delete(0, tk.END)
        entry_time.insert(tk.END, current_task['time'])
        entry_contact.delete(0, tk.END)
        entry_contact.insert(tk.END, current_task['contact'])
        entry_message.delete(0, tk.END)
        entry_message.insert(tk.END, current_task['message'])

# 更新 Treeview
def update_treeview():
    treeview.delete(*treeview.get_children())
    for i, task in enumerate(scheduled_times):
        treeview.insert('', 'end', values=(i, task['time'], task['contact'], task['message']))

# 清空输入框
def clear_entries():
    entry_time.delete(0, tk.END)
    entry_contact.delete(0, tk.END)
    entry_message.delete(0, tk.END)

# 导入任务
def import_tasks():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            global scheduled_times
            scheduled_times = data
            
            # 清除旧的任务
            schedule.clear()
            
            # 重新调度新导入的任务
            for task in scheduled_times:
                schedule.every().day.at(task['time']).do(send_msg_to_contact, task['contact'], task['message'])
            
            # 更新表格
            update_treeview()
            
            messagebox.showinfo("成功", "任务已导入")

# 导出任务
def export_tasks():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(scheduled_times, file, indent=4)
        messagebox.showinfo("成功", "任务已导出")

# 发送消息到指定联系人的函数
def send_msg_to_contact(contact_name, message):
    """发送消息到指定联系人"""
    wx.SendMsg(message, contact_name)

# 创建输入框和按钮
frame_input = ttk.Frame(root, padding="10")
frame_input.pack(pady=20)

# 样式设置
custom_font = font.Font(family='Arial', size=12)

label_time = ttk.Label(frame_input, text="发送时间 (HH:MM):", font=custom_font)
label_time.grid(row=0, column=0, padx=(20, 0), sticky=tk.W)

entry_time = ttk.Entry(frame_input, width=20, font=custom_font)
entry_time.grid(row=0, column=1, padx=(10, 0))

label_contact = ttk.Label(frame_input, text="联系人:", font=custom_font)
label_contact.grid(row=1, column=0, padx=(20, 0), sticky=tk.W)

entry_contact = ttk.Entry(frame_input, width=20, font=custom_font)
entry_contact.grid(row=1, column=1, padx=(10, 0))

label_message = ttk.Label(frame_input, text="消息内容:", font=custom_font)
label_message.grid(row=2, column=0, padx=(20, 0), sticky=tk.W)

entry_message = ttk.Entry(frame_input, width=20, font=custom_font)
entry_message.grid(row=2, column=1, padx=(10, 0))

# 按钮区域
button_frame = ttk.Frame(frame_input)
button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))

button_add = ttk.Button(button_frame, text="添加定时任务", command=add_scheduled_time)
button_add.pack(side=tk.LEFT, padx=10)

button_edit = ttk.Button(button_frame, text="编辑定时任务", command=edit_scheduled_time)
button_edit.pack(side=tk.LEFT, padx=10)

button_delete = ttk.Button(button_frame, text="删除定时任务", command=delete_scheduled_time)
button_delete.pack(side=tk.LEFT, padx=10)

button_import = ttk.Button(button_frame, text="导入任务", command=import_tasks)
button_import.pack(side=tk.LEFT, padx=10)

button_export = ttk.Button(button_frame, text="导出任务", command=export_tasks)
button_export.pack(side=tk.LEFT, padx=10)

# 创建表格显示已添加的定时任务
frame_treeview = ttk.Frame(root, padding="10")
frame_treeview.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

treeview = ttk.Treeview(frame_treeview, columns=("Index", "Time", "Contact", "Message"), show="headings")
treeview.heading("Index", text="序号")
treeview.heading("Time", text="时间")
treeview.heading("Contact", text="联系人")
treeview.heading("Message", text="消息内容")

# 设置列宽和文本居中
treeview.column("Index", width=50, anchor=tk.CENTER)
treeview.column("Time", width=100, anchor=tk.CENTER)
treeview.column("Contact", width=150, anchor=tk.CENTER)
treeview.column("Message", width=300, anchor=tk.CENTER)

treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 绑定事件
treeview.bind('<<TreeviewSelect>>', on_select)

running = threading.Event()

# 主循环检查是否有待执行的任务
def run_scheduled_tasks():
    schedule.run_pending()
    root.after(1000, run_scheduled_tasks)  # 每秒检查一次

# 启动任务检查
root.after(1000, run_scheduled_tasks)

# 启动时间标签更新
root.after(1000, update_time_label)

# 启动进度指示器线程
def start_progress_indicator_thread():
    progress_thread = threading.Thread(target=progress_indicator, daemon=True)
    progress_thread.start()

# 在需要的时候启动进度指示器线程
# root.after_idle(start_progress_indicator_thread)

root.mainloop()
