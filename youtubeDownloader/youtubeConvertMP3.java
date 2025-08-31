package youtubeDownloader;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.concurrent.Task;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.stage.DirectoryChooser;
import javafx.stage.Stage;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;

public class youtubeConvertMP3 extends Application {
    
    private TextField urlField;
    private TextField outputPathField;
    private Button downloadButton;
    private Button downloadOnlyButton;
    private Button browseButton;
    private ProgressBar progressBar;
    private TextArea logArea;
    private Label statusLabel;
    private ComboBox<String> formatComboBox;
    
    public static void main(String[] args) {
        launch(args);
    }
    
    @Override
    public void start(Stage primaryStage) {
        primaryStage.setTitle("YouTube to MP3 Converter");
        
        // Create UI components
        createUIComponents();
        
        // Create layout
        VBox root = createLayout();
        
        // Set up event handlers
        setupEventHandlers(primaryStage);
        
        // Create scene and show stage
        Scene scene = new Scene(root, 600, 500);
        primaryStage.setScene(scene);
        primaryStage.setResizable(true);
        primaryStage.show();
        
        // Check for required dependencies
        checkDependencies();
    }
    
    private void createUIComponents() {
        // URL input
        urlField = new TextField();
        urlField.setPromptText("Enter YouTube URL here...");
        
        // Output path
        outputPathField = new TextField();
        outputPathField.setPromptText("Select output folder...");
        outputPathField.setText(System.getProperty("user.home") + File.separator + "Downloads");
        
        // Buttons
        downloadButton = new Button("下载高质量音频 (M4A/WEBM)");
        downloadButton.setPrefWidth(200);
        
        downloadOnlyButton = new Button("下载原始音频格式");
        downloadOnlyButton.setPrefWidth(150);
        
        browseButton = new Button("浏览");
        browseButton.setPrefWidth(80);
        
        // Format selection
        formatComboBox = new ComboBox<>();
        formatComboBox.getItems().addAll(
            "M4A (高质量音频)",
            "WEBM (开源格式)",
            "OGG (开源格式)",
            "最佳音频 (自动选择)"
        );
        formatComboBox.setValue("M4A (高质量音频)");
        formatComboBox.setPrefWidth(200);
        
        // Progress bar
        progressBar = new ProgressBar(0);
        progressBar.setPrefWidth(400);
        progressBar.setVisible(false);
        
        // Status label
        statusLabel = new Label("Ready");
        
        // Log area
        logArea = new TextArea();
        logArea.setEditable(false);
        logArea.setPrefRowCount(10);
        logArea.setWrapText(true);
    }
    
    private VBox createLayout() {
        VBox root = new VBox(10);
        root.setPadding(new Insets(20));
        
        // Title
        Label titleLabel = new Label("YouTube to MP3 Converter");
        titleLabel.setStyle("-fx-font-size: 18px; -fx-font-weight: bold;");
        
        // URL section
        Label urlLabel = new Label("YouTube URL:");
        
        // Output path section
        Label pathLabel = new Label("Output Folder:");
        HBox pathBox = new HBox(5);
        pathBox.getChildren().addAll(outputPathField, browseButton);
        HBox.setHgrow(outputPathField, Priority.ALWAYS);
        
        // Format selection section
        Label formatLabel = new Label("音频格式 (无需 FFmpeg):");
        
        // Download section
        VBox downloadSection = new VBox(10);
        downloadSection.setAlignment(Pos.CENTER);
        
        HBox buttonBox = new HBox(10);
        buttonBox.setAlignment(Pos.CENTER);
        buttonBox.getChildren().addAll(downloadButton, downloadOnlyButton);
        
        downloadSection.getChildren().addAll(buttonBox, progressBar, statusLabel);
        
        // Log section
        Label logLabel = new Label("Log:");
        VBox logSection = new VBox(5);
        logSection.getChildren().addAll(logLabel, logArea);
        VBox.setVgrow(logArea, Priority.ALWAYS);
        
        root.getChildren().addAll(
            titleLabel,
            new Separator(),
            urlLabel,
            urlField,
            pathLabel,
            pathBox,
            formatLabel,
            formatComboBox,
            new Separator(),
            downloadSection,
            new Separator(),
            logSection
        );
        
        return root;
    }
    
    private void setupEventHandlers(Stage primaryStage) {
        // Browse button
        browseButton.setOnAction(event -> {
            DirectoryChooser directoryChooser = new DirectoryChooser();
            directoryChooser.setTitle("Select Output Folder");
            
            File currentDir = new File(outputPathField.getText());
            if (currentDir.exists()) {
                directoryChooser.setInitialDirectory(currentDir);
            }
            
            File selectedDirectory = directoryChooser.showDialog(primaryStage);
            if (selectedDirectory != null) {
                outputPathField.setText(selectedDirectory.getAbsolutePath());
            }
        });
        
        // Download button
        downloadButton.setOnAction(event -> startDownload(true));
        
        // Download only button  
        downloadOnlyButton.setOnAction(event -> startDownload(false));
        
        // Enter key in URL field
        urlField.setOnAction(event -> startDownload(true));
    }
    
    private void startDownload() {
        startDownload(true); // 默认转换为 MP3
    }
    
    private void startDownload(boolean convertToMp3) {
        String url = urlField.getText().trim();
        String outputPath = outputPathField.getText().trim();
        
        // Validate inputs
        if (url.isEmpty()) {
            showAlert("错误", "请输入 YouTube URL");
            return;
        }
        
        if (outputPath.isEmpty()) {
            showAlert("错误", "请选择输出文件夹");
            return;
        }
        
        if (!isValidYouTubeUrl(url)) {
            showAlert("错误", "请输入有效的 YouTube URL");
            return;
        }
        
        // Create output directory if it doesn't exist
        File outputDir = new File(outputPath);
        if (!outputDir.exists()) {
            outputDir.mkdirs();
        }
        
        // Start download task
        Task<Void> downloadTask = createDownloadTask(url, outputPath, convertToMp3);
        
        // Update UI
        downloadButton.setDisable(true);
        downloadOnlyButton.setDisable(true);
        progressBar.setVisible(true);
        progressBar.setProgress(ProgressIndicator.INDETERMINATE_PROGRESS);
        statusLabel.setText(convertToMp3 ? "下载并转换中..." : "下载中...");
        logArea.clear();
        
        // Run task in background thread
        Thread thread = new Thread(downloadTask);
        thread.setDaemon(true);
        thread.start();
    }
    
    private Task<Void> createDownloadTask(String url, String outputPath, boolean convertToMp3) {
        return new Task<Void>() {
            @Override
            protected Void call() throws Exception {
                try {
                    Platform.runLater(() -> {
                        logArea.appendText("开始下载...\n");
                        logArea.appendText("URL: " + url + "\n");
                        logArea.appendText("输出路径: " + outputPath + "\n");
                        logArea.appendText("转换模式: " + (convertToMp3 ? "转换为 MP3" : "仅下载音频") + "\n\n");
                    });
                    
                    // 找到 yt-dlp 命令
                    final String ytDlpCommand;
                    String foundCommand = findCommand("yt-dlp");
                    if (foundCommand == null) {
                        // 如果找不到，尝试直接使用 "yt-dlp"
                        ytDlpCommand = "yt-dlp";
                        Platform.runLater(() -> {
                            logArea.appendText("警告: 无法在常见位置找到 yt-dlp，尝试直接调用...\n");
                        });
                    } else {
                        ytDlpCommand = foundCommand;
                        Platform.runLater(() -> {
                            logArea.appendText("找到 yt-dlp: " + ytDlpCommand + "\n");
                        });
                    }
                    
                    ProcessBuilder pb;
                    
                    // 获取用户选择的格式
                    String selectedFormat = formatComboBox.getValue();
                    String formatFilter = getFormatFilter(selectedFormat);
                    
                    if (convertToMp3) {
                        // 方法A: 直接下载指定格式的音频流（无需 FFmpeg）
                        Platform.runLater(() -> {
                            logArea.appendText("使用无FFmpeg方法：直接下载音频流...\n");
                            logArea.appendText("选择格式：" + selectedFormat + "\n");
                            logArea.appendText("格式过滤器：" + formatFilter + "\n");
                            logArea.appendText("输出目录：" + outputPath + "\n");
                            logArea.appendText("完整输出路径模板：" + outputPath + File.separator + "%(title)s.%(ext)s\n");
                        });
                        pb = new ProcessBuilder(
                            ytDlpCommand,
                            "-f", formatFilter,
                            "--output", outputPath + File.separator + "%(title)s.%(ext)s",
                            "--no-post-overwrites",
                            "--verbose",  // 添加详细输出
                            url
                        );
                    } else {
                        // 仅下载模式 - 下载最佳质量的音频（保持原格式）
                        Platform.runLater(() -> {
                            logArea.appendText("仅下载模式：保持原始音频格式...\n");
                        });
                        pb = new ProcessBuilder(
                            ytDlpCommand,
                            "-f", "bestaudio",
                            "--output", outputPath + File.separator + "%(title)s.%(ext)s",
                            url
                        );
                        
                        Platform.runLater(() -> {
                            logArea.appendText("模式: 仅下载音频文件，不进行格式转换\n");
                        });
                    }
                    
                    Platform.runLater(() -> {
                        logArea.appendText("执行命令: " + String.join(" ", pb.command()) + "\n\n");
                    });
                    
                    pb.redirectErrorStream(true);
                    Process process = pb.start();
                    
                    // Read output
                    BufferedReader reader = new BufferedReader(
                        new InputStreamReader(process.getInputStream())
                    );
                    
                    String line;
                    while ((line = reader.readLine()) != null) {
                        final String logLine = line;
                        
                        // 过滤掉一些无关紧要的警告信息，只显示重要信息
                        if (!line.contains("WARNING: [youtube] pOc_jg3hjDk: Signature extraction failed") &&
                            !line.contains("Some formats may be missing") &&
                            !line.contains("player API JSON")) {
                            
                            Platform.runLater(() -> {
                                logArea.appendText(logLine + "\n");
                            });
                        }
                        
                        // 更新进度条（基于下载百分比）
                        if (line.contains("[download]") && line.contains("%")) {
                            try {
                                String[] parts = line.split("\\s+");
                                for (String part : parts) {
                                    if (part.contains("%")) {
                                        String percentStr = part.replace("%", "");
                                        double percent = Double.parseDouble(percentStr) / 100.0;
                                        Platform.runLater(() -> {
                                            progressBar.setProgress(percent);
                                            statusLabel.setText("下载中... " + percentStr + "%");
                                        });
                                        break;
                                    }
                                }
                            } catch (NumberFormatException ignored) {
                                // 忽略解析错误
                            }
                        }
                    }
                    
                    int exitCode = process.waitFor();
                    
                    Platform.runLater(() -> {
                        if (exitCode == 0) {
                            statusLabel.setText("下载完成！");
                            progressBar.setProgress(1.0);
                            
                            // 检查下载的文件
                            checkDownloadedFiles(outputPath);
                        } else {
                            statusLabel.setText("下载失败");
                            progressBar.setProgress(0);
                            showAlert("错误", "下载失败。请检查日志了解详细信息。\n\n可能的原因：\n- URL 无效\n- 网络连接问题\n- 视频不可用");
                        }
                    });
                    
                } catch (IOException | InterruptedException e) {
                    Platform.runLater(() -> {
                        statusLabel.setText("Error occurred");
                        progressBar.setProgress(0);
                        logArea.appendText("Error: " + e.getMessage() + "\n");
                        showAlert("Error", "An error occurred: " + e.getMessage());
                    });
                } finally {
                    Platform.runLater(() -> {
                        downloadButton.setDisable(false);
                        downloadOnlyButton.setDisable(false);
                        progressBar.setVisible(false);
                    });
                }
                
                return null;
            }
        };
    }
    
    private boolean isValidYouTubeUrl(String url) {
        return url.contains("youtube.com/watch") || 
               url.contains("youtu.be/") || 
               url.contains("youtube.com/playlist") ||
               url.contains("m.youtube.com");
    }
    
    private void checkDependencies() {
        // 简化依赖检查，只检查 yt-dlp
        Platform.runLater(() -> {
            StringBuilder message = new StringBuilder();
            message.append("依赖检查结果：\n\n");
            
            // 检查 yt-dlp（这是唯一需要的）
            boolean ytDlpExists = checkCommand("yt-dlp");
            if (ytDlpExists) {
                message.append("✅ yt-dlp: 已找到 - 程序已准备就绪\n");
                message.append("ℹ️ 说明：使用 yt-dlp 内置音频处理功能，无需 FFmpeg\n");
                message.append("✅ 程序已准备就绪！可以开始下载 YouTube 音频文件。");
            } else {
                message.append("❌ yt-dlp: 未找到在 PATH 中，但程序会尝试查找\n");
                message.append("⚠️ 警告：yt-dlp 是必需的。如果下载失败，请安装：pip install yt-dlp\n");
                
                Alert alert = new Alert(Alert.AlertType.WARNING);
                alert.setTitle("依赖检查");
                alert.setHeaderText("缺少必要的依赖项");
                alert.setContentText("未找到 yt-dlp。这是下载 YouTube 视频的必需工具。\n\n请安装：pip install yt-dlp");
                alert.showAndWait();
            }
            
            logArea.appendText(message.toString() + "\n");
        });
    }
    
    private boolean checkCommand(String command) {
        // 首先尝试标准方式
        try {
            ProcessBuilder pb = new ProcessBuilder(command, "--version");
            Process process = pb.start();
            int exitCode = process.waitFor();
            if (exitCode == 0) {
                return true;
            }
        } catch (IOException | InterruptedException e) {
            // 继续尝试其他方法
        }
        
        // 如果标准方式失败，尝试在常见位置查找 yt-dlp
        if (command.equals("yt-dlp")) {
            String[] possiblePaths = {
                "C:\\Python\\Scripts\\yt-dlp.exe",
                System.getProperty("user.home") + "\\AppData\\Local\\Programs\\Python\\Python39\\Scripts\\yt-dlp.exe",
                System.getProperty("user.home") + "\\AppData\\Local\\Programs\\Python\\Python310\\Scripts\\yt-dlp.exe",
                System.getProperty("user.home") + "\\AppData\\Local\\Programs\\Python\\Python311\\Scripts\\yt-dlp.exe",
                System.getProperty("user.home") + "\\AppData\\Local\\Microsoft\\WindowsApps\\yt-dlp.exe"
            };
            
            for (String path : possiblePaths) {
                try {
                    ProcessBuilder pb = new ProcessBuilder(path, "--version");
                    Process process = pb.start();
                    int exitCode = process.waitFor();
                    if (exitCode == 0) {
                        return true;
                    }
                } catch (IOException | InterruptedException e) {
                    // 继续检查其他路径
                }
            }
        }
        
        return false;
    }
    
    private String findCommand(String command) {
        // 首先尝试直接使用命令
        try {
            ProcessBuilder pb = new ProcessBuilder(command, "--version");
            Process process = pb.start();
            int exitCode = process.waitFor();
            if (exitCode == 0) {
                return command;
            }
        } catch (IOException | InterruptedException e) {
            // 继续尝试其他方法
        }
        
        // 在常见位置查找 yt-dlp
        if (command.equals("yt-dlp")) {
            String[] possiblePaths = {
                "C:\\Python\\Scripts\\yt-dlp.exe",
                System.getProperty("user.home") + "\\AppData\\Local\\Programs\\Python\\Python39\\Scripts\\yt-dlp.exe",
                System.getProperty("user.home") + "\\AppData\\Local\\Programs\\Python\\Python310\\Scripts\\yt-dlp.exe",
                System.getProperty("user.home") + "\\AppData\\Local\\Programs\\Python\\Python311\\Scripts\\yt-dlp.exe",
                System.getProperty("user.home") + "\\AppData\\Local\\Microsoft\\WindowsApps\\yt-dlp.exe"
            };
            
            for (String path : possiblePaths) {
                try {
                    ProcessBuilder pb = new ProcessBuilder(path, "--version");
                    Process process = pb.start();
                    int exitCode = process.waitFor();
                    if (exitCode == 0) {
                        return path;
                    }
                } catch (IOException | InterruptedException e) {
                    // 继续检查其他路径
                }
            }
        }
        
        return null;
    }
    
    private String getFormatFilter(String selectedFormat) {
        switch (selectedFormat) {
            case "M4A (高质量音频)":
                return "bestaudio[ext=m4a]/bestaudio";
            case "WEBM (开源格式)":
                return "bestaudio[ext=webm]/bestaudio";
            case "OGG (开源格式)":
                return "bestaudio[ext=ogg]/bestaudio";
            case "最佳音频 (自动选择)":
                return "bestaudio";
            default:
                return "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio";
        }
    }
    
    private void checkDownloadedFiles(String outputPath) {
        try {
            File directory = new File(outputPath);
            if (!directory.exists()) {
                showAlert("警告", "输出目录不存在: " + outputPath);
                return;
            }
            
            // 查找音频文件（包括 MP4 格式）
            File[] audioFiles = directory.listFiles((dir, name) -> {
                String lowerName = name.toLowerCase();
                return lowerName.endsWith(".mp3") || lowerName.endsWith(".m4a") || 
                       lowerName.endsWith(".webm") || lowerName.endsWith(".ogg") ||
                       lowerName.endsWith(".mp4") || lowerName.endsWith(".wav") ||
                       lowerName.endsWith(".aac") || lowerName.endsWith(".flac");
            });
            
            if (audioFiles != null && audioFiles.length > 0) {
                StringBuilder message = new StringBuilder("下载成功！找到 " + audioFiles.length + " 个音频文件：\n\n");
                for (File file : audioFiles) {
                    long fileSize = file.length();
                    String sizeStr = formatFileSize(fileSize);
                    message.append("📁 ").append(file.getName()).append(" (").append(sizeStr).append(")\n");
                }
                message.append("\n文件位置: ").append(outputPath);
                
                logArea.appendText("文件检查完成：\n");
                logArea.appendText("- 目录: " + outputPath + "\n");
                logArea.appendText("- 找到 " + audioFiles.length + " 个音频文件\n");
                
                showAlert("成功", message.toString());
            } else {
                // 没有找到音频文件，列出所有文件
                File[] allFiles = directory.listFiles();
                StringBuilder message = new StringBuilder("下载可能未完成或文件保存在其他位置。\n\n");
                message.append("在目录 ").append(outputPath).append(" 中找到的文件：\n\n");
                
                if (allFiles != null && allFiles.length > 0) {
                    for (File file : allFiles) {
                        if (file.isFile()) {
                            long fileSize = file.length();
                            String sizeStr = formatFileSize(fileSize);
                            message.append("📄 ").append(file.getName()).append(" (").append(sizeStr).append(")\n");
                        }
                    }
                } else {
                    message.append("目录为空。\n");
                }
                
                message.append("\n请检查：\n");
                message.append("1. yt-dlp 日志中的实际保存路径\n");
                message.append("2. 是否有权限访问该目录\n");
                message.append("3. 文件是否被保存到其他位置");
                
                logArea.appendText("警告：在输出目录中未找到音频文件\n");
                logArea.appendText("目录: " + outputPath + "\n");
                if (allFiles != null) {
                    logArea.appendText("目录中共有 " + allFiles.length + " 个文件\n");
                }
                
                showAlert("注意", message.toString());
            }
            
        } catch (Exception e) {
            logArea.appendText("文件检查出错: " + e.getMessage() + "\n");
            showAlert("错误", "检查下载文件时出错: " + e.getMessage());
        }
    }
    
    private String formatFileSize(long bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return String.format("%.1f KB", bytes / 1024.0);
        if (bytes < 1024 * 1024 * 1024) return String.format("%.1f MB", bytes / (1024.0 * 1024));
        return String.format("%.1f GB", bytes / (1024.0 * 1024 * 1024));
    }
    
    private void showAlert(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle(title);
        alert.setHeaderText(null);
        alert.setContentText(message);
        alert.showAndWait();
    }
}
