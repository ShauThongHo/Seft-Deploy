# 发票生成器 JavaFX 版 - 快速启动指南

## � 前提条件

在使用本应用之前，请确保你的电脑已安装以下软件：

### ✅ 必需软件
1. **Java Development Kit (JDK) 17 或更高版本**
   - 下载地址: https://www.oracle.com/java/technologies/downloads/
   - 或使用 OpenJDK: https://adoptium.net/
   
2. **Apache Maven 3.6 或更高版本**
   - 下载地址: https://maven.apache.org/download.cgi
   - 确保 Maven 已添加到系统 PATH 环境变量

### 🔍 检查安装

打开命令行（CMD 或 PowerShell），运行以下命令验证安装：

```bash
# 检查 Java 版本（应显示 17 或更高）
java -version

# 检查 Maven 版本（应显示 3.6 或更高）
mvn -version
```

**如果命令无法识别，请先安装相应软件并配置环境变量。**

---

## 🚀 快速开始（3步启动）

### 方法一：一键启动（推荐）⭐

**Windows 用户：**
1. 找到项目文件夹中的 `run-app.bat`
2. 双击运行
3. 等待编译和启动（首次运行需要下载依赖，可能需要1-2分钟）
4. 应用窗口将自动弹出

### 方法二：命令行启动

```bash
# 1. 进入项目目录
cd InvoiceGeneratorJavaFX

# 2. 清理并运行
mvn clean javafx:run
```

### 方法三：开发模式（持续开发）

```bash
# 使用 Maven 编译并运行
mvn compile javafx:run
```

---

## 📱 应用界面说明

### 左侧导航栏
- **🧾 Generate** - 生成发票（单个/批量）
- **🏢 Seller Info** - 卖方信息设置
- **📦 Sales Items** - 商品库存管理

### Generate 页面 - 发票生成

#### 模式切换
- **Single** - 单个发票生成
  - 适合为一个客户生成一张发票
  - 可以添加多个商品项目
  
- **Bulk** - 批量发票生成
  - 适合为多个客户生成相同商品的发票
  - 一次性生成多张PDF

---

## 🎯 使用流程

### 第一次使用

#### 1️⃣ 设置卖方信息（你的公司信息）
1. 点击左侧 **Seller Info**
2. 填写：
   - Organization Name（公司名称）*必填
   - Address（地址）
   - Phone（电话）
   - Email（邮箱）
3. **Upload Logo** - 上传公司Logo（可选）
4. 点击 **Save** 保存（信息会自动记住）

#### 2️⃣ 添加常用商品（可选）
1. 点击左侧 **Sales Items**
2. 填写商品信息：
   - Item Name（商品名称）
   - Price（单价）
   - Tax Rate（税率，默认0%）
3. 点击 **Save Item** 保存到库存
4. 可以添加多个常用商品

#### 3️⃣ 生成单张发票
1. 点击左侧 **Generate**
2. 确保在 **Single** 模式
3. 填写客户信息：
   - Customer Name（客户姓名）*必填
   - ID Number（身份证号/学号）
   - Email（邮箱，如果为空会自动生成）
4. 添加商品：
   - 点击 **Add Item** 按钮
   - 从已保存的商品列表中选择
   - 或输入新商品信息
   - 点击 **Add**
5. 检查 Invoice Items 表格
6. 点击 **Generate Receipt** 生成PDF
7. 选择保存位置

#### 4️⃣ 批量生成发票
1. 点击 **Bulk** 模式
2. 添加多个客户：
   - Name（姓名）
   - ID（身份证号/学号）
   - Email（可选，为空自动生成 ID@sc.edu.my）
   - 点击 **Add to List**
3. 添加商品（同单个模式）
4. 点击 **Generate All Receipts**
5. 选择输出文件夹
6. 等待批量生成完成

---

## 💡 使用技巧

### 📝 自动功能
- ✅ **Email自动生成**: 如果Email为空，系统会自动使用 `ID@sc.edu.my` 格式
- ✅ **信息记忆**: 卖方信息保存后会自动记住
- ✅ **商品库存**: 保存的商品可以重复使用
- ✅ **PDF预览**: Seller Info页面实时预览PDF效果

### 🎨 界面技巧
- **编辑客户**: 在Bulk模式下，点击表格中的"Edit"按钮修改客户信息
- **删除操作**: 
  - 客户列表: 点击"Delete"按钮
  - 商品项目: 选中后点击"Delete Selected"按钮
  - 已保存商品: 在Sales Items页面删除
- **批量清空**: Bulk模式下点击"Clear All"清空所有客户

### 📊 数据管理
- 卖方信息保存在: `~/.invoice_generator_defaults.properties`
- 商品库存保存在: `~/.invoice_generator_items.json`
- Logo图片保存在: `src/main/resources/img/logo.png`

---

## � 常见问题

### Q: 首次运行很慢？
A: 首次运行需要下载依赖库，请耐心等待。有网络连接即可自动完成。

### Q: 应用无法启动？
A: 检查：
1. Java和Maven是否正确安装
2. 运行 `java -version` 和 `mvn -version` 确认
3. 确保Java版本 ≥ 17

### Q: PDF生成失败？
A: 确保：
1. 卖方信息已填写并保存
2. 客户信息至少有姓名
3. 至少添加了一个商品
4. 有文件写入权限

### Q: 如何分发给其他人？
A: 
1. 压缩整个项目文件夹为 `.zip`
2. 发送给用户
3. 用户需要安装 Java 17+ 和 Maven
4. 解压后双击 `run-app.bat` 运行

---

## 📦 分发说明

### 给最终用户的说明

**系统要求：**
- Windows 10/11 或更高版本
- Java 17 或更高版本
- Maven 3.6 或更高版本

**安装步骤：**
1. 安装 Java JDK 17+（如果未安装）
2. 安装 Apache Maven（如果未安装）
3. 解压收到的应用文件夹
4. 双击 `run-app.bat` 启动应用

**首次启动：**
- 首次运行会自动下载所需库（需要网络）
- 下载完成后应用会自动启动
- 后续启动将更快

---

**版本**: 1.0.0  
**最后更新**: 2025年11月  
**支持平台**: Windows 10/11, macOS, Linux

---

**祝你使用愉快！** 🎊
