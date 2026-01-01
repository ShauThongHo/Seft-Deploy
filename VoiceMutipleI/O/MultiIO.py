import tkinter as tk
from tkinter import messagebox, ttk, Canvas, Scrollbar
import pyaudio
import numpy as np
import threading

class AudioRouterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 音频路由器 - Audio Router")
        self.root.geometry("900x600")
        self.root.configure(bg="#1e1e1e")

        self.p = pyaudio.PyAudio()
        self.input_streams = []
        self.output_streams = []
        self.running = False
        self.sample_rate = 44100
        self.channels = 2
        self.chunk = 1024
        self.route_thread = None
        self.device_check_interval = 500  # ms

        # Get devices (use set to track unique devices)
        self.input_devices = []
        self.output_devices = []
        seen_input = set()
        seen_output = set()
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0 and i not in seen_input:
                self.input_devices.append((i, dev['name'], dev))
                seen_input.add(i)
            if dev['maxOutputChannels'] > 0 and i not in seen_output:
                self.output_devices.append((i, dev['name'], dev))
                seen_output.add(i)

        # Create main container
        main_container = tk.Frame(root, bg="#1e1e1e")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title_label = tk.Label(main_container, text="🎵 音频路由器 Audio Router", 
                               font=("Arial", 20, "bold"), bg="#1e1e1e", fg="#ffffff")
        title_label.pack(pady=(0, 20))

        # Device selection frame
        devices_frame = tk.Frame(main_container, bg="#1e1e1e")
        devices_frame.pack(fill=tk.BOTH, expand=True)

        # Input devices section
        input_section = tk.Frame(devices_frame, bg="#2d2d2d", relief=tk.RAISED, bd=2)
        input_section.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        input_header = tk.Frame(input_section, bg="#0078d4", height=40)
        input_header.pack(fill=tk.X)
        tk.Label(input_header, text="🎤 输入设备 Input Devices", 
                font=("Arial", 12, "bold"), bg="#0078d4", fg="#ffffff").pack(pady=8)

        # Input canvas with scrollbar
        input_canvas_frame = tk.Frame(input_section, bg="#2d2d2d")
        input_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        input_canvas = Canvas(input_canvas_frame, bg="#2d2d2d", highlightthickness=0)
        input_scrollbar = Scrollbar(input_canvas_frame, orient="vertical", command=input_canvas.yview)
        self.input_scroll_frame = tk.Frame(input_canvas, bg="#2d2d2d")

        self.input_scroll_frame.bind(
            "<Configure>",
            lambda e: input_canvas.configure(scrollregion=input_canvas.bbox("all"))
        )

        input_canvas.create_window((0, 0), window=self.input_scroll_frame, anchor="nw")
        input_canvas.configure(yscrollcommand=input_scrollbar.set)

        input_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add input devices
        self.input_vars = []
        for idx, name, dev in self.input_devices:
            var = tk.BooleanVar()
            var.trace_add('write', lambda *args: self.on_device_change())
            self.input_vars.append((idx, var, dev))
            device_frame = tk.Frame(self.input_scroll_frame, bg="#3d3d3d", relief=tk.FLAT, bd=1)
            device_frame.pack(fill=tk.X, padx=5, pady=2)
            cb = tk.Checkbutton(device_frame, text=f"[{idx}] {name}", variable=var,
                               bg="#3d3d3d", fg="#ffffff", selectcolor="#0078d4",
                               font=("Arial", 9), anchor="w", relief=tk.FLAT)
            cb.pack(fill=tk.X, padx=5, pady=5)

        # Output devices section
        output_section = tk.Frame(devices_frame, bg="#2d2d2d", relief=tk.RAISED, bd=2)
        output_section.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        output_header = tk.Frame(output_section, bg="#107c10", height=40)
        output_header.pack(fill=tk.X)
        tk.Label(output_header, text="🔊 输出设备 Output Devices", 
                font=("Arial", 12, "bold"), bg="#107c10", fg="#ffffff").pack(pady=8)

        # Output canvas with scrollbar
        output_canvas_frame = tk.Frame(output_section, bg="#2d2d2d")
        output_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        output_canvas = Canvas(output_canvas_frame, bg="#2d2d2d", highlightthickness=0)
        output_scrollbar = Scrollbar(output_canvas_frame, orient="vertical", command=output_canvas.yview)
        self.output_scroll_frame = tk.Frame(output_canvas, bg="#2d2d2d")

        self.output_scroll_frame.bind(
            "<Configure>",
            lambda e: output_canvas.configure(scrollregion=output_canvas.bbox("all"))
        )

        output_canvas.create_window((0, 0), window=self.output_scroll_frame, anchor="nw")
        output_canvas.configure(yscrollcommand=output_scrollbar.set)

        output_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add output devices
        self.output_vars = []
        for idx, name, dev in self.output_devices:
            var = tk.BooleanVar()
            var.trace_add('write', lambda *args: self.on_device_change())
            self.output_vars.append((idx, var, dev))
            device_frame = tk.Frame(self.output_scroll_frame, bg="#3d3d3d", relief=tk.FLAT, bd=1)
            device_frame.pack(fill=tk.X, padx=5, pady=2)
            cb = tk.Checkbutton(device_frame, text=f"[{idx}] {name}", variable=var,
                               bg="#3d3d3d", fg="#ffffff", selectcolor="#107c10",
                               font=("Arial", 9), anchor="w", relief=tk.FLAT)
            cb.pack(fill=tk.X, padx=5, pady=5)

        # Control panel
        control_panel = tk.Frame(main_container, bg="#2d2d2d", relief=tk.RAISED, bd=2)
        control_panel.pack(fill=tk.X, pady=(20, 0))

        # Status
        status_frame = tk.Frame(control_panel, bg="#2d2d2d")
        status_frame.pack(pady=10)
        tk.Label(status_frame, text="状态 Status:", font=("Arial", 10), 
                bg="#2d2d2d", fg="#888888").pack(side=tk.LEFT, padx=5)
        self.status_label = tk.Label(status_frame, text="⏸ 停止 Stopped", 
                                     font=("Arial", 10, "bold"), bg="#2d2d2d", fg="#ff6b6b")
        self.status_label.pack(side=tk.LEFT)

        # Control buttons
        button_frame = tk.Frame(control_panel, bg="#2d2d2d")
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="▶ 开始路由 Start", 
                                      command=self.start_routing,
                                      bg="#107c10", fg="#ffffff", font=("Arial", 11, "bold"),
                                      relief=tk.FLAT, padx=20, pady=10, cursor="hand2")
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="⏹ 停止 Stop", 
                                     command=self.stop_routing, state=tk.DISABLED,
                                     bg="#666666", fg="#ffffff", font=("Arial", 11, "bold"),
                                     relief=tk.FLAT, padx=20, pady=10, cursor="hand2")
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Info label
        info_label = tk.Label(control_panel, 
                             text=f"📊 发现 {len(self.input_devices)} 个输入设备 | {len(self.output_devices)} 个输出设备",
                             font=("Arial", 9), bg="#2d2d2d", fg="#888888")
        info_label.pack(pady=(0, 10))

    def get_supported_rate(self, device_info, is_input=True):
        """获取设备支持的采样率"""
        rates = [44100, 48000, 32000, 22050, 16000, 8000]
        for rate in rates:
            try:
                if is_input:
                    if self.p.is_format_supported(rate,
                                                  input_device=device_info['index'],
                                                  input_channels=min(2, device_info['maxInputChannels']),
                                                  input_format=pyaudio.paInt16):
                        return rate, min(2, device_info['maxInputChannels'])
                else:
                    if self.p.is_format_supported(rate,
                                                  output_device=device_info['index'],
                                                  output_channels=min(2, device_info['maxOutputChannels']),
                                                  output_format=pyaudio.paInt16):
                        return rate, min(2, device_info['maxOutputChannels'])
            except:
                continue
        return int(device_info.get('defaultSampleRate', 44100)), 1

    def start_routing(self):
        input_selections = [(idx, dev) for idx, var, dev in self.input_vars if var.get()]
        output_selections = [(idx, dev) for idx, var, dev in self.output_vars if var.get()]

        if not input_selections or not output_selections:
            messagebox.showerror("❌ 错误", "请至少选择一个输入和一个输出设备\nPlease select at least one input and one output device")
            return

        selected_inputs = [(idx, name, dev) for idx, name, dev in self.input_devices if idx in [i[0] for i in input_selections]]
        selected_outputs = [(idx, name, dev) for idx, name, dev in self.output_devices if idx in [i[0] for i in output_selections]]

        try:
            # Create input streams
            self.input_streams = []
            for idx, name, dev in selected_inputs:
                try:
                    rate, channels = self.get_supported_rate(dev, is_input=True)
                    stream = self.p.open(format=pyaudio.paInt16,
                                       channels=channels,
                                       rate=rate,
                                       input=True,
                                       input_device_index=idx,
                                       frames_per_buffer=1024)
                    self.input_streams.append((stream, rate, channels, idx))
                except Exception as e:
                    messagebox.showerror("❌ 输入设备错误", f"无法打开输入设备 [{idx}] {name}\n{str(e)}")
                    self.cleanup_streams()
                    return

            # Create output streams
            self.output_streams = []
            for idx, name, dev in selected_outputs:
                try:
                    rate, channels = self.get_supported_rate(dev, is_input=False)
                    stream = self.p.open(format=pyaudio.paInt16,
                                       channels=channels,
                                       rate=rate,
                                       output=True,
                                       output_device_index=idx,
                                       frames_per_buffer=1024)
                    self.output_streams.append((stream, rate, channels, idx))
                except Exception as e:
                    messagebox.showerror("❌ 输出设备错误", f"无法打开输出设备 [{idx}] {name}\n{str(e)}")
                    self.cleanup_streams()
                    return

            self.running = True
            self.start_button.config(state=tk.DISABLED, bg="#666666")
            self.stop_button.config(state=tk.NORMAL, bg="#d32f2f")
            self.status_label.config(text="▶ 运行中 Running", fg="#4caf50")

            # Start routing thread
            self.route_thread = threading.Thread(target=self.route_audio, daemon=True)
            self.route_thread.start()
        
        except Exception as e:
            messagebox.showerror("❌ 错误", f"启动路由失败:\n{str(e)}")
            self.cleanup_streams()
    
    def cleanup_streams(self):
        """清理所有流"""
        for item in self.input_streams:
            try:
                stream = item[0] if isinstance(item, tuple) else item
                stream.stop_stream()
                stream.close()
            except:
                pass
        self.input_streams = []
        
        for item in self.output_streams:
            try:
                stream = item[0] if isinstance(item, tuple) else item
                stream.stop_stream()
                stream.close()
            except:
                pass
        self.output_streams = []

    def route_audio(self):
        """实时音频路由线程"""
        try:
            while self.running:
                # Read from all inputs
                inputs_data = []
                for item in self.input_streams:
                    stream, rate, channels = item[0], item[1], item[2]
                    try:
                        data = stream.read(1024, exception_on_overflow=False)
                        audio_array = np.frombuffer(data, dtype=np.int16)
                        # Convert to mono if stereo
                        if channels == 2 and len(audio_array) > 0:
                            audio_array = audio_array.reshape(-1, 2).mean(axis=1).astype(np.int16)
                        inputs_data.append(audio_array)
                    except Exception as e:
                        print(f"读取输入流错误: {e}")
                        continue

                # Mix (average)
                if inputs_data:
                    # Find minimum length
                    min_len = min(len(d) for d in inputs_data)
                    if min_len > 0:
                        # Truncate all to same length
                        inputs_data = [d[:min_len] for d in inputs_data]
                        mixed = np.mean(inputs_data, axis=0).astype(np.int16)
                        
                        # Write to all outputs
                        for item in self.output_streams:
                            stream, rate, channels = item[0], item[1], item[2]
                            try:
                                # Convert mono to stereo if needed
                                if channels == 2:
                                    stereo_data = np.column_stack((mixed, mixed)).flatten()
                                    stream.write(stereo_data.tobytes())
                                else:
                                    stream.write(mixed.tobytes())
                            except Exception as e:
                                print(f"写入输出流错误: {e}")
                                continue
        except Exception as e:
            print(f"路由线程错误: {e}")
            self.running = False
            self.root.after(0, self.stop_routing)

    def on_device_change(self):
        """设备选择变化时调用"""
        if self.running:
            # 在后台更新流，不中断音频
            threading.Thread(target=self.update_streams, daemon=True).start()
    
    def update_streams(self):
        """动态更新音频流"""
        try:
            input_selections = [(idx, dev) for idx, var, dev in self.input_vars if var.get()]
            output_selections = [(idx, dev) for idx, var, dev in self.output_vars if var.get()]
            
            if not input_selections or not output_selections:
                return
            
            selected_inputs = [(idx, name, dev) for idx, name, dev in self.input_devices if idx in [i[0] for i in input_selections]]
            selected_outputs = [(idx, name, dev) for idx, name, dev in self.output_devices if idx in [i[0] for i in output_selections]]
            
            # 获取当前流的设备ID
            current_input_ids = set()
            current_output_ids = set()
            
            # 关闭不需要的输入流
            new_input_streams = []
            for item in self.input_streams:
                stream, rate, channels, dev_idx = item if len(item) == 4 else (*item, None)
                if dev_idx in [idx for idx, _, _ in selected_inputs]:
                    new_input_streams.append((stream, rate, channels, dev_idx))
                    current_input_ids.add(dev_idx)
                else:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except:
                        pass
            self.input_streams = new_input_streams
            
            # 添加新的输入流
            for idx, name, dev in selected_inputs:
                if idx not in current_input_ids:
                    try:
                        rate, channels = self.get_supported_rate(dev, is_input=True)
                        stream = self.p.open(format=pyaudio.paInt16,
                                           channels=channels,
                                           rate=rate,
                                           input=True,
                                           input_device_index=idx,
                                           frames_per_buffer=1024)
                        self.input_streams.append((stream, rate, channels, idx))
                    except:
                        pass
            
            # 关闭不需要的输出流
            new_output_streams = []
            for item in self.output_streams:
                stream, rate, channels, dev_idx = item if len(item) == 4 else (*item, None)
                if dev_idx in [idx for idx, _, _ in selected_outputs]:
                    new_output_streams.append((stream, rate, channels, dev_idx))
                    current_output_ids.add(dev_idx)
                else:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except:
                        pass
            self.output_streams = new_output_streams
            
            # 添加新的输出流
            for idx, name, dev in selected_outputs:
                if idx not in current_output_ids:
                    try:
                        rate, channels = self.get_supported_rate(dev, is_input=False)
                        stream = self.p.open(format=pyaudio.paInt16,
                                           channels=channels,
                                           rate=rate,
                                           output=True,
                                           output_device_index=idx,
                                           frames_per_buffer=1024)
                        self.output_streams.append((stream, rate, channels, idx))
                    except:
                        pass
        except Exception as e:
            print(f"更新流错误: {e}")
    
    def stop_routing(self):
        """停止音频路由"""
        self.running = False
        if self.route_thread:
            self.route_thread.join(timeout=1)
        self.cleanup_streams()
        self.start_button.config(state=tk.NORMAL, bg="#107c10")
        self.stop_button.config(state=tk.DISABLED, bg="#666666")
        self.status_label.config(text="⏸ 停止 Stopped", fg="#ff6b6b")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRouterApp(root)
    root.mainloop()
