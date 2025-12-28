"""
图形用户界面
使用tkinter实现跨平台GUI界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from typing import Optional, Callable
import threading

from smtp_client import SMTPClient, get_smtp_config
from pop3_client import POP3Client, get_pop3_config
from config_manager import ConfigManager
from email_encoder import EmailEncoder, create_encoder


class EmailClientGUI:
    """邮件客户端GUI"""
    
    def __init__(self, root: tk.Tk):
        """
        初始化GUI
        
        Args:
            root: tkinter根窗口
        """
        self.root = root
        self.root.title("邮件用户代理 (Email User Agent)")
        self.root.geometry("900x700")
        
        # 配置管理器
        self.config_manager = ConfigManager()
        
        # 编码器（用于未来的安全通信）
        self.encoder = None
        
        # 创建主界面
        self._create_menu()
        self._create_main_interface()
        
        # 加载当前账号
        self._load_current_account()
    
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="设置", menu=settings_menu)
        settings_menu.add_command(label="账号管理", command=self._show_account_manager)
        settings_menu.add_command(label="高级设置", command=self._show_advanced_settings)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
    
    def _create_main_interface(self):
        """创建主界面"""
        # 创建选项卡
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 发送邮件选项卡
        self.send_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.send_frame, text="发送邮件")
        self._create_send_interface()
        
        # 接收邮件选项卡
        self.receive_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.receive_frame, text="接收邮件")
        self._create_receive_interface()
        
        # 状态栏
        self.status_bar = tk.Label(
            self.root,
            text="就绪",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_send_interface(self):
        """创建发送邮件界面"""
        # 收件人
        tk.Label(self.send_frame, text="收件人:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.to_entry = tk.Entry(self.send_frame, width=60)
        self.to_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Label(self.send_frame, text="(多个收件人用逗号分隔)", fg="gray").grid(
            row=0, column=2, sticky=tk.W
        )
        
        # 抄送
        tk.Label(self.send_frame, text="抄送:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.cc_entry = tk.Entry(self.send_frame, width=60)
        self.cc_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # 主题
        tk.Label(self.send_frame, text="主题:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )
        self.subject_entry = tk.Entry(self.send_frame, width=60)
        self.subject_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # 正文
        tk.Label(self.send_frame, text="正文:").grid(
            row=3, column=0, sticky=tk.NW, padx=5, pady=5
        )
        self.body_text = scrolledtext.ScrolledText(
            self.send_frame,
            width=70,
            height=20
        )
        self.body_text.grid(row=3, column=1, padx=5, pady=5)
        
        # 按钮框架
        button_frame = tk.Frame(self.send_frame)
        button_frame.grid(row=4, column=1, pady=10)
        
        # 发送按钮
        send_button = tk.Button(
            button_frame,
            text="发送",
            command=self._send_email,
            width=15,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        send_button.pack(side=tk.LEFT, padx=5)
        
        # 清空按钮
        clear_button = tk.Button(
            button_frame,
            text="清空",
            command=self._clear_send_form,
            width=15
        )
        clear_button.pack(side=tk.LEFT, padx=5)
    
    def _create_receive_interface(self):
        """创建接收邮件界面"""
        # 控制按钮框架
        control_frame = tk.Frame(self.receive_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 接收按钮
        receive_button = tk.Button(
            control_frame,
            text="接收邮件",
            command=self._receive_emails,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold")
        )
        receive_button.pack(side=tk.LEFT, padx=5)
        
        # 邮件数量标签
        self.email_count_label = tk.Label(
            control_frame,
            text="邮件数: 0"
        )
        self.email_count_label.pack(side=tk.LEFT, padx=20)
        
        # 邮件列表框架
        list_frame = tk.Frame(self.receive_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建邮件列表
        self.email_listbox = tk.Listbox(list_frame, height=10)
        self.email_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.email_listbox.bind('<<ListboxSelect>>', self._on_email_select)
        
        # 滚动条
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.email_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.email_listbox.yview)
        
        # 邮件详情框架
        detail_frame = tk.LabelFrame(
            self.receive_frame,
            text="邮件详情",
            padx=5,
            pady=5
        )
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 邮件详情文本
        self.email_detail_text = scrolledtext.ScrolledText(
            detail_frame,
            width=80,
            height=15,
            state=tk.DISABLED
        )
        self.email_detail_text.pack(fill=tk.BOTH, expand=True)
        
        # 存储邮件数据
        self.emails_data = []
    
    def _load_current_account(self):
        """加载当前账号"""
        account = self.config_manager.get_current_account()
        if account:
            self.status_bar.config(text=f"当前账号: {account['email']}")
        else:
            self.status_bar.config(text="未配置账号，请在设置中添加账号")
    
    def _send_email(self):
        """发送邮件"""
        # 获取当前账号
        account = self.config_manager.get_current_account()
        if not account:
            messagebox.showerror("错误", "请先在设置中配置邮件账号")
            return
        
        # 获取表单数据
        to_addrs = [addr.strip() for addr in self.to_entry.get().split(',') if addr.strip()]
        cc_addrs = [addr.strip() for addr in self.cc_entry.get().split(',') if addr.strip()]
        subject = self.subject_entry.get()
        body = self.body_text.get("1.0", tk.END).strip()
        
        # 验证输入
        if not to_addrs:
            messagebox.showerror("错误", "请输入收件人地址")
            return
        
        if not subject:
            messagebox.showerror("错误", "请输入邮件主题")
            return
        
        if not body:
            messagebox.showerror("错误", "请输入邮件正文")
            return
        
        # 在新线程中发送邮件，避免阻塞UI
        self.status_bar.config(text="正在发送邮件...")
        self.root.update()
        
        def send_task():
            try:
                # 创建SMTP客户端
                smtp_client = SMTPClient(
                    account['smtp_server'],
                    account['smtp_port'],
                    account['email'],
                    account['password'],
                    account.get('use_ssl', True)
                )
                
                # 准备编码函数（如果启用了自定义编码）
                encoder_func = None
                if self.encoder:
                    encoder_func = lambda text: self.encoder.encode(text)
                
                # 发送邮件
                with smtp_client:
                    smtp_client.send_email(
                        to_addrs,
                        subject,
                        body,
                        cc_addrs=cc_addrs if cc_addrs else None,
                        encoder_func=encoder_func
                    )
                
                # 更新UI
                self.root.after(0, lambda: self._on_send_success())
            except Exception as e:
                self.root.after(0, lambda: self._on_send_error(str(e)))
        
        thread = threading.Thread(target=send_task, daemon=True)
        thread.start()
    
    def _on_send_success(self):
        """发送成功回调"""
        self.status_bar.config(text="邮件发送成功")
        messagebox.showinfo("成功", "邮件发送成功")
        self._clear_send_form()
    
    def _on_send_error(self, error_msg: str):
        """发送失败回调"""
        self.status_bar.config(text="邮件发送失败")
        messagebox.showerror("错误", f"发送邮件失败:\n{error_msg}")
    
    def _clear_send_form(self):
        """清空发送表单"""
        self.to_entry.delete(0, tk.END)
        self.cc_entry.delete(0, tk.END)
        self.subject_entry.delete(0, tk.END)
        self.body_text.delete("1.0", tk.END)
    
    def _receive_emails(self):
        """接收邮件"""
        # 获取当前账号
        account = self.config_manager.get_current_account()
        if not account:
            messagebox.showerror("错误", "请先在设置中配置邮件账号")
            return
        
        # 在新线程中接收邮件
        self.status_bar.config(text="正在接收邮件...")
        self.root.update()
        
        def receive_task():
            try:
                # 创建POP3客户端
                pop3_client = POP3Client(
                    account['pop3_server'],
                    account['pop3_port'],
                    account['email'],
                    account['password'],
                    account.get('use_ssl', True)
                )
                
                # 准备解码函数（如果启用了自定义编码）
                decoder_func = None
                if self.encoder:
                    decoder_func = lambda text: self.encoder.decode(text)
                
                # 接收邮件
                max_emails = self.config_manager.get_setting('max_emails', 50)
                with pop3_client:
                    emails = pop3_client.list_emails(
                        count=max_emails,
                        decoder_func=decoder_func
                    )
                
                # 更新UI
                self.root.after(0, lambda: self._on_receive_success(emails))
            except Exception as e:
                self.root.after(0, lambda: self._on_receive_error(str(e)))
        
        thread = threading.Thread(target=receive_task, daemon=True)
        thread.start()
    
    def _on_receive_success(self, emails):
        """接收成功回调"""
        self.status_bar.config(text=f"成功接收 {len(emails)} 封邮件")
        self.emails_data = emails
        
        # 更新邮件列表
        self.email_listbox.delete(0, tk.END)
        for email in emails:
            subject = email.get('subject', '(无主题)')
            from_addr = email.get('from', '(未知发件人)')
            # 截断长标题
            if len(subject) > 40:
                subject = subject[:40] + "..."
            self.email_listbox.insert(tk.END, f"{subject} - {from_addr}")
        
        # 更新邮件数量
        self.email_count_label.config(text=f"邮件数: {len(emails)}")
    
    def _on_receive_error(self, error_msg: str):
        """接收失败回调"""
        self.status_bar.config(text="接收邮件失败")
        messagebox.showerror("错误", f"接收邮件失败:\n{error_msg}")
    
    def _on_email_select(self, event):
        """邮件选中事件"""
        selection = self.email_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.emails_data):
            email = self.emails_data[index]
            
            # 显示邮件详情
            self.email_detail_text.config(state=tk.NORMAL)
            self.email_detail_text.delete("1.0", tk.END)
            
            detail = f"发件人: {email.get('from', '(未知)')}\n"
            detail += f"收件人: {email.get('to', '(未知)')}\n"
            detail += f"主题: {email.get('subject', '(无主题)')}\n"
            detail += f"日期: {email.get('date', '(未知)')}\n"
            detail += "-" * 80 + "\n\n"
            detail += email.get('body', '(无内容)')
            
            self.email_detail_text.insert("1.0", detail)
            self.email_detail_text.config(state=tk.DISABLED)
    
    def _show_account_manager(self):
        """显示账号管理窗口"""
        AccountManagerWindow(self.root, self.config_manager, self._load_current_account)
    
    def _show_advanced_settings(self):
        """显示高级设置窗口"""
        AdvancedSettingsWindow(self.root, self.config_manager, self._update_encoder)
    
    def _update_encoder(self):
        """更新编码器"""
        use_custom = self.config_manager.get_setting('use_custom_encoder', False)
        shared_secret = self.config_manager.get_setting('shared_secret', '')
        
        if use_custom and shared_secret:
            self.encoder = create_encoder(True, shared_secret)
        else:
            self.encoder = None
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """邮件用户代理使用说明

1. 配置账号
   - 点击"设置" -> "账号管理"
   - 添加您的邮箱账号信息
   - 常见邮箱服务器配置：
     * QQ邮箱: smtp.qq.com:465, pop.qq.com:995
     * 163邮箱: smtp.163.com:465, pop.163.com:995
     * Sina邮箱: smtp.sina.com:465, pop.sina.com:995

2. 发送邮件
   - 切换到"发送邮件"标签
   - 填写收件人、主题和正文
   - 点击"发送"按钮

3. 接收邮件
   - 切换到"接收邮件"标签
   - 点击"接收邮件"按钮
   - 点击邮件列表查看详情

4. 高级功能
   - 自定义Base64编码（用于安全通信）
   - 点击"设置" -> "高级设置"配置

更多信息请参考README.md文件。"""
        
        messagebox.showinfo("使用说明", help_text)
    
    def _show_about(self):
        """显示关于信息"""
        about_text = """邮件用户代理 v1.0

一个支持SMTP和POP3协议的跨平台邮件客户端

作者: Sun-yh233
许可证: MIT License

技术实现:
- SMTP协议: Python标准库smtplib
- POP3协议: Python标准库poplib
- GUI界面: tkinter

GitHub: https://github.com/Sun-yh233/Email-User-Agent"""
        
        messagebox.showinfo("关于", about_text)


class AccountManagerWindow:
    """账号管理窗口"""
    
    def __init__(self, parent, config_manager: ConfigManager, 
                 callback: Optional[Callable] = None):
        """
        初始化账号管理窗口
        
        Args:
            parent: 父窗口
            config_manager: 配置管理器
            callback: 账号更新后的回调函数
        """
        self.config_manager = config_manager
        self.callback = callback
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("账号管理")
        self.window.geometry("700x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_interface()
        self._load_accounts()
    
    def _create_interface(self):
        """创建界面"""
        # 账号列表框架
        list_frame = tk.Frame(self.window)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(list_frame, text="账号列表", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 账号列表
        self.account_listbox = tk.Listbox(list_frame)
        self.account_listbox.pack(fill=tk.BOTH, expand=True)
        self.account_listbox.bind('<<ListboxSelect>>', self._on_account_select)
        
        # 按钮
        button_frame = tk.Frame(list_frame)
        button_frame.pack(pady=5)
        
        tk.Button(
            button_frame,
            text="添加",
            command=self._add_account,
            width=10
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame,
            text="删除",
            command=self._remove_account,
            width=10
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            button_frame,
            text="设为当前",
            command=self._set_current,
            width=10
        ).pack(side=tk.LEFT, padx=2)
        
        # 账号详情框架
        detail_frame = tk.Frame(self.window)
        detail_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        tk.Label(detail_frame, text="账号详情", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 表单
        form_frame = tk.Frame(detail_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 账号名称
        tk.Label(form_frame, text="账号名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = tk.Entry(form_frame, width=30)
        self.name_entry.grid(row=0, column=1, pady=5)
        
        # 邮箱地址
        tk.Label(form_frame, text="邮箱地址:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_entry = tk.Entry(form_frame, width=30)
        self.email_entry.grid(row=1, column=1, pady=5)
        
        # SMTP服务器
        tk.Label(form_frame, text="SMTP服务器:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.smtp_server_entry = tk.Entry(form_frame, width=30)
        self.smtp_server_entry.grid(row=2, column=1, pady=5)
        
        # SMTP端口
        tk.Label(form_frame, text="SMTP端口:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.smtp_port_entry = tk.Entry(form_frame, width=30)
        self.smtp_port_entry.grid(row=3, column=1, pady=5)
        self.smtp_port_entry.insert(0, "465")
        
        # POP3服务器
        tk.Label(form_frame, text="POP3服务器:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.pop3_server_entry = tk.Entry(form_frame, width=30)
        self.pop3_server_entry.grid(row=4, column=1, pady=5)
        
        # POP3端口
        tk.Label(form_frame, text="POP3端口:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.pop3_port_entry = tk.Entry(form_frame, width=30)
        self.pop3_port_entry.grid(row=5, column=1, pady=5)
        self.pop3_port_entry.insert(0, "995")
        
        # 密码/授权码
        tk.Label(form_frame, text="密码/授权码:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.password_entry = tk.Entry(form_frame, width=30, show="*")
        self.password_entry.grid(row=6, column=1, pady=5)
        
        # SSL选项
        self.use_ssl_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            form_frame,
            text="使用SSL/TLS",
            variable=self.use_ssl_var
        ).grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # 按钮
        button_frame2 = tk.Frame(form_frame)
        button_frame2.grid(row=8, column=1, pady=10)
        
        tk.Button(
            button_frame2,
            text="保存",
            command=self._save_account,
            width=10,
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame2,
            text="清空",
            command=self._clear_form,
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        # 自动填充按钮
        tk.Button(
            form_frame,
            text="自动识别服务器",
            command=self._auto_detect_servers
        ).grid(row=1, column=2, padx=5)
    
    def _load_accounts(self):
        """加载账号列表"""
        self.account_listbox.delete(0, tk.END)
        accounts = self.config_manager.list_accounts()
        current = self.config_manager.config['current_account']
        
        for account_name in accounts:
            display_name = account_name
            if account_name == current:
                display_name += " (当前)"
            self.account_listbox.insert(tk.END, display_name)
    
    def _on_account_select(self, event):
        """账号选中事件"""
        selection = self.account_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        accounts = self.config_manager.list_accounts()
        if index < len(accounts):
            account = self.config_manager.get_account(accounts[index])
            if account:
                self._fill_form(account)
    
    def _fill_form(self, account):
        """填充表单"""
        self._clear_form()
        self.name_entry.insert(0, account['name'])
        self.email_entry.insert(0, account['email'])
        self.smtp_server_entry.insert(0, account['smtp_server'])
        self.smtp_port_entry.insert(0, str(account['smtp_port']))
        self.pop3_server_entry.insert(0, account['pop3_server'])
        self.pop3_port_entry.insert(0, str(account['pop3_port']))
        self.password_entry.insert(0, account['password'])
        self.use_ssl_var.set(account.get('use_ssl', True))
    
    def _clear_form(self):
        """清空表单"""
        self.name_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.smtp_server_entry.delete(0, tk.END)
        self.smtp_port_entry.delete(0, tk.END)
        self.smtp_port_entry.insert(0, "465")
        self.pop3_server_entry.delete(0, tk.END)
        self.pop3_port_entry.delete(0, tk.END)
        self.pop3_port_entry.insert(0, "995")
        self.password_entry.delete(0, tk.END)
        self.use_ssl_var.set(True)
    
    def _auto_detect_servers(self):
        """自动识别服务器配置"""
        email = self.email_entry.get().strip()
        if not email:
            messagebox.showwarning("警告", "请先输入邮箱地址")
            return
        
        provider = self.config_manager.get_provider_from_email(email)
        if provider == 'custom':
            messagebox.showinfo("提示", "无法自动识别该邮箱服务商，请手动输入服务器信息")
            return
        
        smtp_config = get_smtp_config(provider)
        pop3_config = get_pop3_config(provider)
        
        if smtp_config['server']:
            self.smtp_server_entry.delete(0, tk.END)
            self.smtp_server_entry.insert(0, smtp_config['server'])
            self.smtp_port_entry.delete(0, tk.END)
            self.smtp_port_entry.insert(0, str(smtp_config['port']))
        
        if pop3_config['server']:
            self.pop3_server_entry.delete(0, tk.END)
            self.pop3_server_entry.insert(0, pop3_config['server'])
            self.pop3_port_entry.delete(0, tk.END)
            self.pop3_port_entry.insert(0, str(pop3_config['port']))
        
        messagebox.showinfo("成功", f"已自动填充{provider.upper()}邮箱的服务器配置")
    
    def _add_account(self):
        """添加账号"""
        self._clear_form()
    
    def _save_account(self):
        """保存账号"""
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        smtp_server = self.smtp_server_entry.get().strip()
        smtp_port = self.smtp_port_entry.get().strip()
        pop3_server = self.pop3_server_entry.get().strip()
        pop3_port = self.pop3_port_entry.get().strip()
        password = self.password_entry.get().strip()
        
        # 验证输入
        if not all([name, email, smtp_server, smtp_port, pop3_server, pop3_port, password]):
            messagebox.showerror("错误", "请填写所有必填字段")
            return
        
        try:
            smtp_port = int(smtp_port)
            pop3_port = int(pop3_port)
        except ValueError:
            messagebox.showerror("错误", "端口必须是数字")
            return
        
        # 检查是否是更新现有账号
        existing_account = self.config_manager.get_account(name)
        
        account = {
            'name': name,
            'email': email,
            'smtp_server': smtp_server,
            'smtp_port': smtp_port,
            'pop3_server': pop3_server,
            'pop3_port': pop3_port,
            'password': password,
            'use_ssl': self.use_ssl_var.get()
        }
        
        if existing_account:
            # 更新账号
            self.config_manager.update_account(name, account)
            messagebox.showinfo("成功", "账号更新成功")
        else:
            # 添加新账号
            if self.config_manager.add_account(account):
                messagebox.showinfo("成功", "账号添加成功")
            else:
                messagebox.showerror("错误", "账号添加失败")
                return
        
        self._load_accounts()
        if self.callback:
            self.callback()
    
    def _remove_account(self):
        """删除账号"""
        selection = self.account_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的账号")
            return
        
        index = selection[0]
        accounts = self.config_manager.list_accounts()
        if index < len(accounts):
            account_name = accounts[index]
            
            if messagebox.askyesno("确认", f"确定要删除账号 '{account_name}' 吗？"):
                self.config_manager.remove_account(account_name)
                self._load_accounts()
                self._clear_form()
                if self.callback:
                    self.callback()
    
    def _set_current(self):
        """设为当前账号"""
        selection = self.account_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择账号")
            return
        
        index = selection[0]
        accounts = self.config_manager.list_accounts()
        if index < len(accounts):
            account_name = accounts[index]
            self.config_manager.set_current_account(account_name)
            self._load_accounts()
            if self.callback:
                self.callback()


class AdvancedSettingsWindow:
    """高级设置窗口"""
    
    def __init__(self, parent, config_manager: ConfigManager,
                 callback: Optional[Callable] = None):
        """
        初始化高级设置窗口
        
        Args:
            parent: 父窗口
            config_manager: 配置管理器
            callback: 设置更新后的回调函数
        """
        self.config_manager = config_manager
        self.callback = callback
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("高级设置")
        self.window.geometry("500x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        self._create_interface()
        self._load_settings()
    
    def _create_interface(self):
        """创建界面"""
        # 安全通信设置
        security_frame = tk.LabelFrame(
            self.window,
            text="安全通信设置（Base64编码定制）",
            padx=10,
            pady=10
        )
        security_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 启用自定义编码
        self.use_custom_var = tk.BooleanVar()
        tk.Checkbutton(
            security_frame,
            text="启用自定义Base64编码",
            variable=self.use_custom_var,
            command=self._toggle_custom_encoding
        ).pack(anchor=tk.W, pady=5)
        
        # 说明
        tk.Label(
            security_frame,
            text="启用后，邮件正文将使用自定义Base64编码表进行编码，\n"
                 "与您通信的对方也需要使用相同的共享密钥。",
            fg="gray",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=5)
        
        # 共享密钥
        tk.Label(security_frame, text="共享密钥:").pack(anchor=tk.W, pady=5)
        self.shared_secret_entry = tk.Entry(security_frame, width=40)
        self.shared_secret_entry.pack(anchor=tk.W, pady=5)
        
        tk.Label(
            security_frame,
            text="提示：共享密钥用于生成自定义编码表，\n"
                 "通信双方必须使用相同的共享密钥。",
            fg="gray",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=5)
        
        # 其他设置
        other_frame = tk.LabelFrame(
            self.window,
            text="其他设置",
            padx=10,
            pady=10
        )
        other_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 最大邮件数
        tk.Label(other_frame, text="每次接收最大邮件数:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.max_emails_entry = tk.Entry(other_frame, width=10)
        self.max_emails_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 按钮
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        tk.Button(
            button_frame,
            text="保存",
            command=self._save_settings,
            width=15,
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="取消",
            command=self.window.destroy,
            width=15
        ).pack(side=tk.LEFT, padx=5)
    
    def _load_settings(self):
        """加载设置"""
        use_custom = self.config_manager.get_setting('use_custom_encoder', False)
        self.use_custom_var.set(use_custom)
        
        shared_secret = self.config_manager.get_setting('shared_secret', '')
        self.shared_secret_entry.insert(0, shared_secret)
        
        max_emails = self.config_manager.get_setting('max_emails', 50)
        self.max_emails_entry.insert(0, str(max_emails))
        
        self._toggle_custom_encoding()
    
    def _toggle_custom_encoding(self):
        """切换自定义编码状态"""
        if self.use_custom_var.get():
            self.shared_secret_entry.config(state=tk.NORMAL)
        else:
            self.shared_secret_entry.config(state=tk.DISABLED)
    
    def _save_settings(self):
        """保存设置"""
        use_custom = self.use_custom_var.get()
        shared_secret = self.shared_secret_entry.get().strip()
        max_emails_str = self.max_emails_entry.get().strip()
        
        # 验证
        if use_custom and not shared_secret:
            messagebox.showerror("错误", "启用自定义编码时必须设置共享密钥")
            return
        
        try:
            max_emails = int(max_emails_str)
            if max_emails < 1 or max_emails > 1000:
                raise ValueError()
        except ValueError:
            messagebox.showerror("错误", "最大邮件数必须是1-1000之间的数字")
            return
        
        # 保存设置
        self.config_manager.set_setting('use_custom_encoder', use_custom)
        self.config_manager.set_setting('shared_secret', shared_secret)
        self.config_manager.set_setting('max_emails', max_emails)
        
        messagebox.showinfo("成功", "设置已保存")
        
        if self.callback:
            self.callback()
        
        self.window.destroy()


def run_gui():
    """运行GUI应用"""
    root = tk.Tk()
    app = EmailClientGUI(root)
    root.mainloop()


if __name__ == '__main__':
    run_gui()
